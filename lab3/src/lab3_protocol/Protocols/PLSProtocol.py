from playground.network.common import StackingProtocol, StackingTransport
from ..Transports.PLSTransport import PLSTransport
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import HMAC, SHA256, SHA
from Crypto.Util import Counter
from Crypto import Random
from ..Packets.PLSPackets import PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose, PlsBasicType
import os
import os.path

class PLSProtocol(StackingProtocol):

    DEBUG_MODE = True
    # State Definitions
    STATE_DEFAULT = 0

    STATE_SERVER_HELLO = 100
    STATE_SERVER_KEY_EXCHANGE = 101
    STATE_SERVER_PLS_HANDSHAKE_DONE = 102
    STATE_SERVER_TRANSFER = 103
    STATE_SERVER_CLOSED = 104

    STATE_CLIENT_HELLO = 200
    STATE_CLIENT_KEY_EXCHANGE = 201
    STATE_CLIENT_PLS_HANDSHAKE_DONE = 202
    STATE_CLIENT_TRANSFER = 203
    STATE_CLIENT_CLOSED = 204

    STATE_DESC = {
        0: "STATE_DEFAULT",
        100: "STATE_SERVER_HELLO",
        101: "STATE_SERVER_KEY_EXCHANGE",
        102: "STATE_SERVER_PLS_HANDSHAKE_DONE",
        103: "STATE_SERVER_TRANSFER",
        104: "STATE_SERVER_CLOSED",
        200: "STATE_CLIENT_HELLO",
        201: "STATE_CLIENT_KEY_EXCHANGE",
        202: "STATE_CLIENT_PLS_HANDSHAKE_DONE",
        203: "STATE_CLIENT_TRANSFER",
        204: "STATE_CLIENT_CLOSED"
    }

    

    def __init__(self, higherProtocol=None):
        if higherProtocol:
            print("Initializing PLS layer on " + type(higherProtocol).__name__)
        super().__init__(higherProtocol)
        random_generator = Random.new().read
        self.preKey = Random.get_random_bytes(48)
        self.nonce = int.from_bytes(os.urandom(8), byteorder='big')
        self.peerNonce = None
        self.deserializer = PlsBasicType.Deserializer()
        self.sessionKey = b"Hello PLS! JHU17"
        self.cipher = AES.new(self.sessionKey, AES.MODE_CTR, counter=Counter.new(128))

    def connection_made(self, transport):
        print("Connection made at PLS layer on " + type(self.higherProtocol()).__name__)
        self.transport = transport
        # higherTransport = PLSTransport(self.transport, self)
        # self.higherProtocol().connection_made(higherTransport)

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
    
    def createKey(self, name):
        my_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(my_path, ("./keys/" + name + ".key"))
        # import local private/public key pair
        with open(path) as f:
            rawKey = f.read() 
        private_key = RSA.importKey(rawKey)
        public_key = private_key.publickey()
        # import third party key
        third_path = os.path.join(my_path, ("./keys/thirdparty.key"))
        with open(third_path) as f:
            rawKey = f.read()
        third_private_key = RSA.importKey(rawKey)
        third_public_key = third_private_key.publickey()
        rsaSigner = PKCS1_v1_5.new(third_private_key)
        rsaVerifier = PKCS1_v1_5.new(third_public_key)

        return private_key, public_key, rsaSigner, rsaVerifier

    def verify(self, verifier, data, signature):
        hasher = SHA256.new()
        hasher.update(data)
        return verifier.verify(hasher, signature)

    def generateCerts(self, public_key, signer):
        hasher = SHA256.new()
        hasher.update(public_key)
        signature = signer.sign(hasher)
        return [public_key, signature]

    def verifyValidationHash(self, validationHash, M1, M2, M3, M4):
        hasher = SHA.new()
        hasher.update((str(M1) + str(M2) + str(M3) + str(M4)).encode())
        return validationHash == hasher.digest()

    def dbgPrint(self, msg):
        if (self.DEBUG_MODE):
            print(msg)

