from playground.network.common import StackingProtocol, StackingTransport
from ..Transports.PLSTransport import PLSTransport
from Crypto.Cipher import AES
from Crypto.Util import Counter

class PLSProtocol(StackingProtocol):
    def __init__(self, higherProtocol=None):
        if higherProtocol:
            print("Initializing PLS layer on " + type(higherProtocol).__name__)
        super().__init__(higherProtocol)
        self.sessionKey = b"Hello PLS! JHU17"
        self.cipher = AES.new(self.sessionKey, AES.MODE_CTR, counter=Counter.new(128))

    def connection_made(self, transport):
        print("Connection made at PLS layer on " + type(self.higherProtocol()).__name__)
        self.transport = transport
        higherTransport = PLSTransport(self.transport, self)
        self.higherProtocol().connection_made(higherTransport)

    def data_received(self, data):
        print("Data received at PLS layer on " + type(self.higherProtocol()).__name__)
        self.higherProtocol().data_received(self.decrypt(data))

    def connection_lost(self, exc):
        print("Connection lost at PLS layer on " + type(self.higherProtocol()).__name__)
        self.higherProtocol().connection_lost(exc)
        self.transport = None

    def decrypt(self, data):
        print("Decrypting data at PLS layer on " + type(self.higherProtocol()).__name__)
        return self.cipher.decrypt(data)

    def encrypt(self, data):
        print("Encrypting data at PLS layer on " + type(self.higherProtocol()).__name__)
        return self.cipher.encrypt(data)
