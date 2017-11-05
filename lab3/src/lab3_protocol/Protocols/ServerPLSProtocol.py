from ..Packets.PLSPackets import PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose
from ..Transports.PLSTransport import PLSTransport
from .PLSProtocol import PLSProtocol
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import HMAC, SHA256, SHA
from Crypto.Cipher import AES
from Crypto.Util import Counter
import struct

class ServerPLSProtocol(PLSProtocol):

    def __init__(self, higherProtocol=None):
        super().__init__(higherProtocol)
        self.state = self.STATE_SERVER_HELLO
        self.privateKey, self.publicKey, self.rsaSigner, self.rsaVerifier = self.createKey("server")

    def connection_made(self, transport):
        super().connection_made(transport)

    def data_received(self, data):
        # if self.state != self.STATE_SERVER_TRANSFER:
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PlsHello) and self.state == self.STATE_SERVER_HELLO:
                if self.verify(self.rsaVerifier, pkt.Certs[0], pkt.Certs[1]):
                    self.dbgPrint("Server: PlsHello received!")
                    self.peerKey = RSA.importKey(pkt.Certs[0])
                    self.clientNonce = pkt.Nonce
                    self.dbgPrint("Server: sending PlsHello back to client... Current state: {!r}, nonce Number: {!r}"
                                  .format(self.STATE_DESC[self.state], self.serverNonce))
                    # Make hellopacket and send back
                    self.dbgPrint("server public key: " + str(self.publicKey.exportKey()))
                    self.serverNonce = self.generateNonce()
                    helloPkt = PlsHello.makeHelloPacket(self.serverNonce, self.generateCerts(self.publicKey.exportKey(), self.rsaSigner))
                    self.transport.write(helloPkt.__serialize__())
                    self.state = self.STATE_SERVER_KEY_EXCHANGE
                else:
                    self.handleError("Error: cert verification failure.")
            elif isinstance(pkt, PlsKeyExchange) and self.state == self.STATE_SERVER_KEY_EXCHANGE:
                if self.serverNonce + 1 == pkt.NoncePlusOne:
                    self.dbgPrint("Server: received PlsKeyExchange packet from client")
                    '''
                    TODO:
                        1) get prekey from client side
                        2) set state as STATE_SERVER_PLS_HANDSHAKE_DONE
                    '''
                    self.clientPreKey = self.privateKey.decrypt(pkt.PreKey)
                    self.dbgPrint("Server: client prekey received: " + str(self.clientPreKey))
                    self.serverPreKey = self.generatePreKey()
                    self.dbgPrint("Server: sending plsKeyExchange packet, prekey: {!r}".format(str(self.serverPreKey)))
                    plsKeyExchangePkt = PlsKeyExchange.makePlsKeyExchange(self.peerKey.encrypt(self.serverPreKey, 32)[0], self.clientNonce + 1)
                    self.transport.write(plsKeyExchangePkt.__serialize__())
                    self.state = self.STATE_SERVER_PLS_HANDSHAKE_DONE
                else:
                    self.handleError("Error: bad nonce in key exchange.")
            elif isinstance(pkt, PlsHandshakeDone) and self.state == self.STATE_SERVER_PLS_HANDSHAKE_DONE:
                if self.verifyDerivationHash(pkt.ValidationHash, self.clientNonce, self.serverNonce, self.clientPreKey, self.serverPreKey):
                    self.dbgPrint("Server: plsHandshakeDone packet received from client, validation hash: {!r}".format(pkt.ValidationHash))
                    self.dbgPrint("Server: sending plsHandshakeDone to client and notifying upper layer connection_made")
                    hashText = self.generateDerivationHash()
                    handshakeDonePkt = PlsHandshakeDone.makePlsHandshakeDone(hashText)
                    self.transport.write(handshakeDonePkt.__serialize__())
                    self.setKeys(hashText)
                    self.setEngines()
                    self.state = self.STATE_SERVER_TRANSFER
                    higherTransport = PLSTransport(self.transport, self)
                    self.higherProtocol().connection_made(higherTransport)
                else:
                    self.handleError("Error: validation hash verification failure.")
            elif isinstance(pkt, PlsData) and self.state == self.STATE_SERVER_TRANSFER:
                self.dbgPrint("Server: received application data from client, decrypt and notify upper layer")
                # TODO: verify MAC
                self.higherProtocol().data_received(self.decrypt(pkt.Ciphertext))
            elif isinstance(pkt, PlsClose):
                self.dbgPrint("PlsClose received, closing...")
                self.transport.close()
            else:
                self.handleError("Error: wrong packet type " + pkt.DEFINITION_IDENTIFIER + ", current state "
                              + self.STATE_DESC[self.state])
        # else:
        #     self.dbgPrint("Server: received application data from client, decrypt and notify upper layer")
        #     self.higherProtocol().data_received(self.decrypt(data))

    def setEngines(self):
        # TODO: fix counter initial value
        self.encEngine = AES.new(self.EKs, AES.MODE_CTR, counter=Counter.new(128, initial_value=struct.unpack('>Q', self.IVs[:8])[0]))
        self.decEngine = AES.new(self.EKc, AES.MODE_CTR, counter=Counter.new(128, initial_value=struct.unpack('>Q', self.IVc[:8])[0]))
        self.macEngine = HMAC.new(self.MKc)
        self.verificationEngine = HMAC.new(self.MKs)
