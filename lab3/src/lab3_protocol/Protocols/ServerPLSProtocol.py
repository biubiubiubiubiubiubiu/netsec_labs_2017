from ..Packets.PLSPackets import PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose
from ..Transports.PLSTransport import PLSTransport
from .PLSProtocol import PLSProtocol
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import HMAC, SHA256, SHA
class ServerPLSProtocol(PLSProtocol):

    def __init__(self, higherProtocol=None):
        super().__init__(higherProtocol)
        self.state = self.STATE_SERVER_HELLO
        self.private_key, self.public_key, self.rsaSigner, self.rsaVerifier = self.createKey("server")
        self.peerKey = None 

    def connection_made(self, transport):
        super().connection_made(transport)

    def data_received(self, data):
        if self.state != self.STATE_SERVER_TRANSFER:
            self.deserializer.update(data)
            for pkt in self.deserializer.nextPackets():
                if isinstance(pkt, PlsHello) and self.state == self.STATE_SERVER_HELLO:
                    if self.verify(self.rsaVerifier, pkt.Certs[0], pkt.Certs[1]):
                        self.dbgPrint("Server: PlsHello received!")
                        self.peerKey = RSA.importKey(pkt.Certs[0])
                        self.peerNonce = pkt.Nonce
                        self.dbgPrint("Server: sending PlsHello back to client... Current state: {!r}, nonce Number: {!r}".format(self.STATE_DESC[self.state],\
                                                                                                                                            self.nonce))
                        # Make hellopacket and send back
                        self.dbgPrint("server pbkey: " + str(self.public_key.exportKey()))
                        helloPkt = PlsHello.makeHelloPacket(self.nonce, self.generateCerts(self.public_key.exportKey(), self.rsaSigner))
                        self.transport.write(helloPkt.__serialize__())
                        self.state = self.STATE_SERVER_KEY_EXCHANGE
                    else:
                        # TODO: add pls.close()
                        raise NotImplementedError
                elif isinstance(pkt, PlsKeyExchange) and self.state == self.STATE_SERVER_KEY_EXCHANGE:
                    if self.nonce + 1 == pkt.NoncePlusOne:
                        self.dbgPrint("Server: received PlsKeyExchange packet from client")
                        '''
                        TODO:
                            1) get prekey from client side
                            2) set state as STATE_CLIENT_PLS_HANDSHAKE_DONE
                        '''
                        self.peerPreKey = self.private_key.decrypt(pkt.PreKey)
                        self.dbgPrint("Server: client prekey received: " + str(self.peerPreKey))
                        self.dbgPrint("Server: sending plsKeyExchange packet, prekey: {!r}".format(str(self.preKey)))
                        plsKeyExchangePkt = PlsKeyExchange.makePlsKeyExchange(self.peerKey.encrypt(self.preKey, 32)[0], self.peerNonce + 1)
                        self.transport.write(plsKeyExchangePkt.__serialize__())
                        self.state = self.STATE_CLIENT_PLS_HANDSHAKE_DONE
                    else:
                        # TODO: add pls.close()
                        raise NotImplementedError
                elif isinstance(pkt, PlsHandshakeDone) and self.state == self.STATE_CLIENT_PLS_HANDSHAKE_DONE:
                    if self.verifyValidationHash(pkt.ValidationHash, self.peerNonce, self.nonce, self.peerPreKey, self.preKey):
                        self.dbgPrint("Server: plsHandshakeDone packet received from client, validation hash: {!r}".format(pkt.ValidationHash))
                        self.dbgPrint("Server: sending plsHandshakeDone to server... notifying upper layer connection_made")
                        hasher = SHA.new()
                        hasher.update((str(self.peerNonce) + str(self.nonce) + str(self.peerPreKey) + str(self.preKey)).encode())
                        hashText = hasher.digest()
                        handshakeDonePkt = PlsHandshakeDone.makePlsHandshakeDone(hashText)
                        self.transport.write(handshakeDonePkt.__serialize__())
                        higherTransport = PLSTransport(self.transport, self)
                        self.higherProtocol().connection_made(higherTransport)
                        self.state = self.STATE_SERVER_TRANSFER
                    else:
                        # TODO: add pls.close()
                        raise NotImplementedError
        else:
            self.dbgPrint("Server: received application data from client, decrypt and notify upper layer")
            self.higherProtocol().data_received(self.decrypt(data))





    def connection_lost(self, exc):
        super().connection_lost(exc)

