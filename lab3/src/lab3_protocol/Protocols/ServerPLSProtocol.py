from ..Packets.PLSPackets import PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose
from ..Transports.PLSTransport import PLSTransport
from .PLSProtocol import PLSProtocol
from playground.common import CipherUtil
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import padding


class ServerPLSProtocol(PLSProtocol):
    def __init__(self, higherProtocol=None):
        super().__init__(higherProtocol)
        self.state = self.STATE_SERVER_HELLO

    def connection_made(self, transport):
        super().connection_made(transport)
        self.importKeys()

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PlsHello) and self.state == self.STATE_SERVER_HELLO:
                # Deserialize certs in packet, attach root cert
                peerCerts = [CipherUtil.getCertFromBytes(c) for c in pkt.Certs]
                if self.verifyCerts(peerCerts):
                    self.dbgPrint("Server: PlsHello received!")
                    self.messages["M1"] = pkt.__serialize__()
                    self.peerPublicKey = peerCerts[0].public_key()
                    self.clientNonce = pkt.Nonce

                    # Make PlsHello and send back
                    self.serverNonce = self.generateNonce()
                    # Serialize certs to pack into PlsHello
                    certBytes = [CipherUtil.serializeCert(c) for c in self.certs]
                    self.dbgPrint("Server: sending PlsHello back to client... Current state: {!r}, nonce Number: {!r}"
                                  .format(self.STATE_DESC[self.state], self.serverNonce))
                    helloPkt = PlsHello.makeHelloPacket(self.serverNonce, certBytes)
                    self.messages["M2"] = helloPkt.__serialize__()
                    self.transport.write(helloPkt.__serialize__())
                    self.state = self.STATE_SERVER_KEY_EXCHANGE
                else:
                    self.handleError("Error: certificate verification failure.")
            elif isinstance(pkt, PlsKeyExchange) and self.state == self.STATE_SERVER_KEY_EXCHANGE:
                if self.serverNonce + 1 == pkt.NoncePlusOne:
                    self.dbgPrint("Server: received PlsKeyExchange packet from client")
                    self.messages["M3"] = pkt.__serialize__()
                    self.clientPreKey = self.privateKey.decrypt(
                        pkt.PreKey,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA1()),
                            algorithm=hashes.SHA1(),
                            label=None
                        )
                    )
                    if len(self.clientPreKey) != self.PRE_KEY_LENGTH_BYTES:
                        self.handleError("Error: Bad client pre-key with length = " + str(len(self.clientPreKey) * 8)
                                         + " bits, wrong RSA decryption?")
                    else:
                        self.dbgPrint("Server: client prekey received: " + self.clientPreKey.hex())

                        # Make PlsKeyExchange and send back
                        self.serverPreKey = self.generatePreKey()
                        self.dbgPrint(
                            "Server: sending plsKeyExchange packet, prekey: {!r}".format(self.serverPreKey.hex()))
                        encryptedPreKey = self.peerPublicKey.encrypt(
                            self.serverPreKey,
                            padding.OAEP(
                                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                                algorithm=hashes.SHA1(),
                                label=None
                            )
                        )
                        plsKeyExchangePkt = PlsKeyExchange.makePlsKeyExchange(encryptedPreKey, self.clientNonce + 1)
                        self.messages["M4"] = plsKeyExchangePkt.__serialize__()
                        self.transport.write(plsKeyExchangePkt.__serialize__())
                        self.state = self.STATE_SERVER_PLS_HANDSHAKE_DONE

                        # Enough info to generate keys and initialize ciphers
                        self.setKeys(self.generateDerivationHash())
                        self.setEngines()
                else:
                    self.handleError("Error: bad nonce in key exchange.")
            elif isinstance(pkt, PlsHandshakeDone) and self.state == self.STATE_SERVER_PLS_HANDSHAKE_DONE:
                if self.verifyValidationHash(pkt.ValidationHash):
                    self.dbgPrint("Server: plsHandshakeDone packet received from client.")
                    self.dbgPrint(
                        "Server: sending plsHandshakeDone to client and notifying upper layer connection_made")
                    hashText = self.generateValidationHash()
                    handshakeDonePkt = PlsHandshakeDone.makePlsHandshakeDone(hashText)
                    self.transport.write(handshakeDonePkt.__serialize__())

                    # Enter transmission
                    self.state = self.STATE_SERVER_TRANSFER
                    higherTransport = PLSTransport(self.transport, self)
                    self.higherProtocol().connection_made(higherTransport)
                else:
                    self.handleError("Error: validation hash verification failure.")
            elif isinstance(pkt, PlsData) and self.state == self.STATE_SERVER_TRANSFER:
                self.dbgPrint("Server: received application data from client, decrypt and notify upper layer")
                if self.verifyPlsData(pkt.Ciphertext, pkt.Mac):
                    self.dbgPrint("Verification succeeded, sending data to upper layer...")
                    self.higherProtocol().data_received(self.decrypt(pkt.Ciphertext))
                else:
                    # self.handleError("Error: data verification failure.")
                    self.dbgPrint("Data MAC verification error, discarded.")
            elif isinstance(pkt, PlsClose):
                self.dbgPrint("PlsClose received, closing...")
                self.transport.close()
            else:
                self.handleError("Error: wrong packet type " + pkt.DEFINITION_IDENTIFIER + ", current state "
                                 + self.STATE_DESC[self.state])

    def setEngines(self):
        self.encEngine = Cipher(algorithms.AES(self.EKs), modes.CTR(self.IVs), backend=default_backend()).encryptor()
        self.decEngine = Cipher(algorithms.AES(self.EKc), modes.CTR(self.IVc), backend=default_backend()).decryptor()
        self.macEngine = hmac.HMAC(self.MKs, hashes.SHA1(), backend=default_backend())
        self.verificationEngine = hmac.HMAC(self.MKc, hashes.SHA1(), backend=default_backend())
