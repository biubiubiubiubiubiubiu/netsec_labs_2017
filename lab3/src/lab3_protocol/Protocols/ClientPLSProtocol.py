from ..Packets.PLSPackets import PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose
from ..Transports.PLSTransport import PLSTransport
from .PLSProtocol import PLSProtocol
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import HMAC, SHA256, SHA
class ClientPLSProtocol(PLSProtocol):

    def __init__(self, higherProtocol=None):
        super().__init__(higherProtocol)
        '''
        TODO:
            1) set state as STATE_CLIENT_HELLO 
            2) input key from keys/...
            3) Generate private_key, public_key, signer
        ''' 
        self.private_key, self.public_key, self.rsaSigner, self.rsaVerifier = self.createKey("client")
        self.peerKey = None 

    def connection_made(self, transport):
        super().connection_made(transport)
        self.state = self.STATE_CLIENT_HELLO
        self.dbgPrint("Client: Sending Hello message, current state: {!r}, nonce number: {!r}".format(self.STATE_DESC[self.state], self.nonce))
        # TODO: get more certificates in the list
        # print(self.public_key.exportKey())
        helloPkt = PlsHello.makeHelloPacket(self.nonce, self.generateCerts(self.public_key.exportKey(), self.rsaSigner))
        self.transport.write(helloPkt.__serialize__())
        

    def data_received(self, data):
        if self.state != self.STATE_CLIENT_TRANSFER:
            self.deserializer.update(data)
            for pkt in self.deserializer.nextPackets():
                if isinstance(pkt, PlsHello) and self.state == self.STATE_CLIENT_HELLO:
                    if self.verify(self.rsaVerifier, pkt.Certs[0], pkt.Certs[1]):
                        self.dbgPrint("Client: received PlsHello packet from server, current state: {!r}".format(self.STATE_DESC[self.state]))
                        '''
                        TODO: 
                            1) Save public_key and Nonce in pkt
                            2) generate the PlsKeyExchange packet
                            3) switch state to "STATE_CLIENT_KEY_EXCHANGE"
                        '''  
                        self.peerNonce = pkt.Nonce
                        self.dbgPrint("Client: received pbkey: " + str(pkt.Certs[0]))
                        self.peerKey = RSA.importKey(pkt.Certs[0])
                        self.state = self.STATE_CLIENT_KEY_EXCHANGE
                        self.dbgPrint("Client: sending plsKeyExchage Packet. current state: {!r}, prekey: {!r}".format(self.STATE_DESC[self.state], str(self.preKey)))
                        plsKeyExchangePkt = PlsKeyExchange.makePlsKeyExchange(self.peerKey.encrypt(self.preKey, 32)[0], self.peerNonce + 1)
                        self.transport.write(plsKeyExchangePkt.__serialize__())
                    else:
                        # TODO: add pls.close()
                        raise NotImplementedError
                elif isinstance(pkt, PlsKeyExchange) and self.state == self.STATE_CLIENT_KEY_EXCHANGE:
                    if self.nonce + 1 == pkt.NoncePlusOne: 
                        self.dbgPrint("Client: received PlsKeyExchange packet from server")
                        self.peerPreKey = self.private_key.decrypt(pkt.PreKey)
                        self.dbgPrint("Client: server prekey received: " + str(self.peerPreKey))
                        # change the state
                        self.state = self.STATE_CLIENT_PLS_HANDSHAKE_DONE
                        # Send back handshakeDone packet
                        hasher = SHA.new()
                        hasher.update((str(self.nonce) + str(self.peerNonce) + str(self.preKey) + str(self.peerPreKey)).encode())
                        hashText = hasher.digest()
                        self.dbgPrint("Client: sending plsHandShakeDone packet, validationcode: {!r}".format(hashText))
                        handshakeDonePkt = PlsHandshakeDone.makePlsHandshakeDone(hashText)
                        self.transport.write(handshakeDonePkt.__serialize__())
                    else:
                        # TODO: add pls.close()
                        raise NotImplementedError
                elif isinstance(pkt, PlsHandshakeDone) and self.state == self.STATE_CLIENT_PLS_HANDSHAKE_DONE:
                    if self.verifyValidationHash(pkt.ValidationHash, self.nonce, self.peerNonce, self.preKey, self.peerPreKey):
                        self.dbgPrint("Client: received PlsHandShakeDone packet from server, notifying upperlayer connection_made...")
                        higherTransport = PLSTransport(self.transport, self)
                        self.higherProtocol().connection_made(higherTransport)
                        self.state = self.STATE_CLIENT_TRANSFER
                    else:
                        # TODO: add pls.close()
                        raise NotImplementedError
                else:
                    # TODO add pls.close()
                    raise NotImplementedError
        else:
            self.dbgPrint("Client: received application data from server")
            self.higherProtocol().data_received(self.decrypt(data))

                    

    def connection_lost(self, exc):
        super().connection_lost(exc)


