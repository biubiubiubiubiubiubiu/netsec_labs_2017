from ..Packets.PLSPackets import PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose
from ..Transports.PLSTransport import PLSTransport
from .PLSProtocol import PLSProtocol
from playground.common import CipherUtil
from Crypto.PublicKey import RSA
from Crypto.Hash import HMAC
from Crypto.Cipher import AES
from Crypto.Util import Counter
import codecs


class ServerPLSProtocol(PLSProtocol):
    def __init__(self, higherProtocol=None):
        super().__init__(higherProtocol)
        self.state = self.STATE_SERVER_HELLO

    def connection_made(self, transport):
        super().connection_made(transport)
        self.importKeys("keys", "server")

    def data_received(self, data):
        # if self.state != self.STATE_SERVER_TRANSFER:
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PlsHello) and self.state == self.STATE_SERVER_HELLO:
                # Deserialize certs in packet, attach root cert
                peerCerts = [CipherUtil.getCertFromBytes(c) for c in pkt.Certs]
                if self.verifyCerts(peerCerts + [self.rootCert]):
                    self.dbgPrint("Server: PlsHello received!")
                    self.messages["M1"] = pkt.__serialize__()
                    self.peerKey = RSA.importKey(self.serializePublicKeyFromCert(peerCerts[0]))
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
                    self.clientPreKey = self.privateKey.decrypt(pkt.PreKey)
                    self.dbgPrint("Server: client prekey received: " + str(self.clientPreKey))

                    # Make PlsKeyExchange and send back
                    self.serverPreKey = self.generatePreKey()
                    self.dbgPrint("Server: sending plsKeyExchange packet, prekey: {!r}".format(str(self.serverPreKey)))
                    plsKeyExchangePkt = PlsKeyExchange.makePlsKeyExchange(
                        self.peerKey.encrypt(self.serverPreKey, 32)[0], self.clientNonce + 1)
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
                    self.dbgPrint("Server: plsHandshakeDone packet received from client, validation hash: {!r}".format(
                        pkt.ValidationHash))
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
                    self.handleError("Error: data verification failure.")
            elif isinstance(pkt, PlsClose):
                self.dbgPrint("PlsClose received, closing...")
                self.transport.close()
            else:
                self.handleError("Error: wrong packet type " + pkt.DEFINITION_IDENTIFIER + ", current state "
                                 + self.STATE_DESC[self.state])

    def setEngines(self):
        # TODO: fix counter initial value
        self.encEngine = AES.new(self.EKs, AES.MODE_CTR,
                                 counter=Counter.new(128, initial_value=int(codecs.encode(self.IVs, 'hex'),16)))
        self.decEngine = AES.new(self.EKc, AES.MODE_CTR,
                                 counter=Counter.new(128, initial_value=int(codecs.encode(self.IVc, 'hex'),16)))
        self.macEngine = HMAC.new(self.MKs)
        self.verificationEngine = HMAC.new(self.MKc)
