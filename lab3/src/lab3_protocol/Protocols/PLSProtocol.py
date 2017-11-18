from playground.network.common import StackingProtocol
from playground.common import CipherUtil
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
from ..Packets.PLSPackets import PlsData, PlsClose, PlsBasicType
from ..CertFactory import *


class PLSProtocol(StackingProtocol):
    NONCE_LENGTH_BYTES = 8
    PRE_KEY_LENGTH_BYTES = 16

    DEBUG_MODE = False
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
        self.clientPreKey = None
        self.serverPreKey = None
        self.clientNonce = None
        self.serverNonce = None
        self.deserializer = PlsBasicType.Deserializer()

        self.messages = {}

        self.privateKey = None
        self.privateCipher = None
        self.rootCert = None
        self.certs = []
        self.publicKey = None
        self.peerPublicKey = None
        self.peerPublicCipher = None
        self.peerAddress = None

        self.EKc = None
        self.EKs = None
        self.IVc = None
        self.IVs = None
        self.MKc = None
        self.MKs = None

        self.encEngine = None
        self.decEngine = None
        self.macEngine = None
        self.verificationEngine = None

    def connection_made(self, transport):
        self.dbgPrint("Connection made at PLS layer on " + type(self.higherProtocol()).__name__)
        self.transport = transport
        self.peerAddress = transport.get_extra_info('peername')

    def data_received(self, data):
        self.dbgPrint("Data received at PLS layer on " + type(self.higherProtocol()).__name__)
        self.higherProtocol().data_received(self.decrypt(data))

    def connection_lost(self, exc):
        self.dbgPrint("Connection lost at PLS layer on " + type(self.higherProtocol()).__name__)
        self.higherProtocol().connection_lost(exc)
        self.transport = None

    def decrypt(self, data):
        self.dbgPrint("Decrypting data at PLS layer on " + type(self.higherProtocol()).__name__)
        return self.decEngine.decrypt(data)

    def encrypt(self, data):
        self.dbgPrint("Encrypting data at PLS layer on " + type(self.higherProtocol()).__name__)
        return self.encEngine.encrypt(data)

    def generateNonce(self):
        return int.from_bytes(Random.get_random_bytes(self.NONCE_LENGTH_BYTES), byteorder='big')

    def generatePreKey(self):
        return Random.get_random_bytes(self.PRE_KEY_LENGTH_BYTES)

    def serializePublicKeyFromCert(self, cert):
        from cryptography.hazmat.primitives import serialization
        return cert.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def importKeys(self, path, privateName):
        addr = self.transport.get_extra_info('sockname')[0]
        rawKey = getPrivateKeyForAddr(addr)
        self.privateKey = RSA.importKey(rawKey.encode("utf-8"))
        self.privateCipher = PKCS1_OAEP.new(self.privateKey)

        rawCerts = getCertsForAddr(addr)
        self.certs = [CipherUtil.getCertFromBytes(c.encode("utf-8")) for c in rawCerts]
        self.publicKey = RSA.importKey(self.serializePublicKeyFromCert(self.certs[0]))


        self.rootCert = CipherUtil.getCertFromBytes(getRootCert().encode("utf-8"))

    def verifyCerts(self, certs):
        certs.append(self.rootCert)

        commonName = CipherUtil.getCertSubject(certs[0])["commonName"]
        groupCommonName = CipherUtil.getCertSubject(certs[1])["commonName"]
        peerAddressList = [str(i) for i in self.peerAddress[0].split(".")]
        peerAddress = ".".join(peerAddressList)
        peerAddressPrefix = ".".join(peerAddressList[:3])

        if commonName != peerAddress:
            self.dbgPrint("Error: address mismatch: " + commonName + ", " + peerAddress)
            return False
        elif groupCommonName != peerAddressPrefix:
            self.dbgPrint("Error: group address mismatch: " + groupCommonName + ", " + peerAddressPrefix)
            return False
        else:
            return CipherUtil.ValidateCertChainSigs(certs)

    def verifyValidationHash(self, hash):
        hasher = SHA.new()
        hasher.update(self.messages["M1"] + self.messages["M2"] + self.messages["M3"] + self.messages["M4"])
        return hash == hasher.digest()

    def dbgPrint(self, msg, forced=False):
        if (self.DEBUG_MODE or forced):
            print(type(self).__name__ + ": " + msg)

    def generateDerivationHash(self):
        hasher = SHA.new()
        hasher.update(
            b"PLS1.0" + self.clientNonce.to_bytes(self.NONCE_LENGTH_BYTES, byteorder='big')
            + self.serverNonce.to_bytes(self.NONCE_LENGTH_BYTES, byteorder='big')
            + self.clientPreKey + self.serverPreKey)
        return hasher.digest()

    def generateValidationHash(self):
        hasher = SHA.new()
        hasher.update(self.messages["M1"] + self.messages["M2"] + self.messages["M3"] + self.messages["M4"])
        return hasher.digest()

    def setKeys(self, block_0):
        blocks = []
        blocks.append(block_0)
        for i in range(4):
            hasher = SHA.new()
            hasher.update(blocks[i])
            blocks.append(hasher.digest())
        keys = b''.join(blocks)[:96]
        self.EKc = keys[:16]
        self.EKs = keys[16:32]
        self.IVc = keys[32:48]
        self.IVs = keys[48:64]
        self.MKc = keys[64:80]
        self.MKs = keys[80:]

    def setEngines(self):
        raise NotImplementedError

    def makePlsData(self, data):
        ciphertext = self.encrypt(data)
        # engine = self.macEngine.copy()
        engine = self.macEngine
        engine.update(ciphertext)
        mac = engine.digest()
        plsData = PlsData.makePlsData(ciphertext, mac)
        return plsData

    def verifyPlsData(self, ciphertext, mac):
        # engine = self.verificationEngine.copy()
        engine = self.verificationEngine
        engine.update(ciphertext)
        return mac == engine.digest()

    def handleError(self, error):
        self.sendPlsClose(error)
        self.stop(error)

    def sendPlsClose(self, error=None):
        if error:
            self.dbgPrint("Sending PlsClose with error: " + error)
        else:
            self.dbgPrint("Sending PlsClose...")
        plsClose = PlsClose.makePlsClose(error)
        self.transport.write(plsClose.__serialize__())

    def stop(self, error=None):
        if error:
            self.dbgPrint("Closing with error: " + error, True)
        else:
            self.dbgPrint("Closing...")
        self.transport.close()
