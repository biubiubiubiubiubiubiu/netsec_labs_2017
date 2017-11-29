from ..Packets.PLSPackets import PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose
from ..Transports.PLSTransport import PLSTransport
from .PLSProtocol import PLSProtocol
from playground.common import CipherUtil
from Crypto.PublicKey import RSA
from Crypto.Hash import HMAC, SHA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util import Counter
import codecs


class ClientPLSProtocol(PLSProtocol):
    def __init__(self, higherProtocol=None):
        super().__init__(higherProtocol)

    def connection_made(self, transport):
        super().connection_made(transport)
        self.importKeys("keys", "client")
        self.state = self.STATE_CLIENT_HELLO
        self.dbgPrint(
            "Client: Sending Hello message, current state: {!r}, nonce number: {!r}".format(self.STATE_DESC[self.state],
                                                                                            self.clientNonce))
        self.clientNonce = self.generateNonce()
        # Serialize certs to pack into PlsHello
        certBytes = [CipherUtil.serializeCert(c) for c in self.certs]
        helloPkt = PlsHello.makeHelloPacket(self.clientNonce, certBytes)
        self.messages["M1"] = helloPkt.__serialize__()
        self.transport.write(helloPkt.__serialize__())

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PlsHello) and self.state == self.STATE_CLIENT_HELLO:
                # Deserialize certs in packet, attach root cert
                peerCerts = [CipherUtil.getCertFromBytes(c) for c in pkt.Certs]
                if self.verifyCerts(peerCerts):
                    self.dbgPrint("Client: received PlsHello packet from server, current state: {!r}".format(
                        self.STATE_DESC[self.state]))
                    self.messages["M2"] = pkt.__serialize__()
                    self.state = self.STATE_CLIENT_KEY_EXCHANGE

                    # Make PlsKeyExchange
                    self.serverNonce = pkt.Nonce
                    # Get public key from cert, as a PyCrypto object
                    self.peerPublicKey = RSA.importKey(self.serializePublicKeyFromCert(peerCerts[0]))
                    self.peerPublicCipher = PKCS1_OAEP.new(self.peerPublicKey)
                    self.clientPreKey = self.generatePreKey()
                    self.dbgPrint("Client: sending plsKeyExchage Packet. current state: {!r}, prekey: {!r}".format(
                        self.STATE_DESC[self.state], self.clientPreKey.hex()))
                    plsKeyExchangePkt = PlsKeyExchange.makePlsKeyExchange(
                        self.peerPublicCipher.encrypt(self.clientPreKey), self.serverNonce + 1)
                    self.messages["M3"] = plsKeyExchangePkt.__serialize__()
                    self.transport.write(plsKeyExchangePkt.__serialize__())
                else:
                    self.handleError("Error: certificate verification failure.")
            elif isinstance(pkt, PlsKeyExchange) and self.state == self.STATE_CLIENT_KEY_EXCHANGE:
                if self.clientNonce + 1 == pkt.NoncePlusOne:
                    self.dbgPrint("Client: received PlsKeyExchange packet from server")
                    self.messages["M4"] = pkt.__serialize__()
                    self.serverPreKey = self.privateCipher.decrypt(pkt.PreKey)
                    if len(self.serverPreKey) != self.PRE_KEY_LENGTH_BYTES:
                        self.handleError("Error: Bad server pre-key with length = " + str(len(self.serverPreKey) * 8)
                                         + " bits, wrong RSA decryption?")
                    else:
                        self.dbgPrint("Client: server prekey received: " + self.serverPreKey.hex())
                        # change the state
                        self.state = self.STATE_CLIENT_PLS_HANDSHAKE_DONE
                        # Create hash from M1 - M4, send back handshakeDone packet
                        hashText = self.generateValidationHash()
                        self.dbgPrint("Client: sending plsHandShakeDone packet...")
                        handshakeDonePkt = PlsHandshakeDone.makePlsHandshakeDone(hashText)
                        self.transport.write(handshakeDonePkt.__serialize__())

                        # Enough info to generate keys and initialize ciphers
                        self.setKeys(self.generateDerivationHash())
                        self.setEngines()
                else:
                    self.handleError("Error: bad nonce in key exchange.")
            elif isinstance(pkt, PlsHandshakeDone) and self.state == self.STATE_CLIENT_PLS_HANDSHAKE_DONE:
                if self.verifyValidationHash(pkt.ValidationHash):
                    self.dbgPrint(
                        "Client: received PlsHandShakeDone packet from server, notifying upperlayer connection_made...")
                    # Enter transmission
                    self.state = self.STATE_CLIENT_TRANSFER
                    higherTransport = PLSTransport(self.transport, self)
                    self.higherProtocol().connection_made(higherTransport)
                else:
                    self.handleError("Error: validation hash verification failure.")
            elif isinstance(pkt, PlsData) and self.state == self.STATE_CLIENT_TRANSFER:
                self.dbgPrint("Client: received application data from server")
                if self.verifyPlsData(pkt.Ciphertext, pkt.Mac):
                    self.dbgPrint("Verification succeeded, sending data to upper layer...")
                    self.higherProtocol().data_received(self.decrypt(pkt.Ciphertext))
                else:
                    self.handleError("Error: data verification failure.")
            elif isinstance(pkt, PlsClose):
                self.dbgPrint("PlsClose received, closing...")
                self.stop(pkt.Error)
            else:
                self.handleError("Error: wrong packet type " + pkt.DEFINITION_IDENTIFIER + ", current state "
                                 + self.STATE_DESC[self.state])

    def setEngines(self):
        # TODO: fix counter initial value
        self.encEngine = AES.new(self.EKc, AES.MODE_CTR,
                                 counter=Counter.new(128, initial_value=int(codecs.encode(self.IVc, 'hex'), 16)))
        self.decEngine = AES.new(self.EKs, AES.MODE_CTR,
                                 counter=Counter.new(128, initial_value=int(codecs.encode(self.IVs, 'hex'), 16)))
        self.macEngine = HMAC.new(self.MKc, digestmod=SHA)
        self.verificationEngine = HMAC.new(self.MKs, digestmod=SHA)
