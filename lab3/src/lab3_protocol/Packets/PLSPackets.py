from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, UINT8, UINT32, UINT64, BUFFER, LIST, STRING
from playground.network.packet.fieldtypes.attributes import Optional
import zlib

class PlsBasicType(PacketType):
  DEFINITION_IDENTIFIER = "netsecfall2017.pls.Base"
  DEFINITION_VERSION = "1.0"


class PlsHello(PlsBasicType):
  DEFINITION_IDENTIFIER = "netsecfall2017.pls.hello"
  DEFINITION_VERSION = "1.0"
  FIELDS = [
    ("Nonce", UINT64),
    ("Certs", LIST(BUFFER))
  ]

  @classmethod 
  def makeHelloPacket(cls, nonce, certs):
    pkt = cls()
    pkt.Nonce = nonce
    pkt.Certs = certs
    return pkt

class PlsKeyExchange(PlsBasicType):
  DEFINITION_IDENTIFIER = "netsecfall2017.pls.keyexchange"
  DEFINITION_VERSION = "1.0"
  FIELDS = [
    ("PreKey", BUFFER),
    ("NoncePlusOne", UINT64)
  ]

  @classmethod
  def makePlsKeyExchange(cls, preKey, noncePlusOne):
    pkt = cls()
    pkt.PreKey = preKey
    pkt.NoncePlusOne = noncePlusOne
    return pkt

class PlsHandshakeDone(PlsBasicType):
  DEFINITION_IDENTIFIER = "netsecfall2017.pls.handshakedone"
  DEFINITION_VERSION = "1.0"
  FIELDS = [
    ("ValidationHash", BUFFER)
  ]

  @classmethod
  def makePlsHandshakeDone(cls, validationHash):
    pkt = cls()
    pkt.ValidationHash = validationHash
    return pkt

class PlsData(PlsBasicType):
  DEFINITION_IDENTIFIER = "netsecfall2017.pls.data"
  DEFINITION_VERSION = "1.0"
  FIELDS = [
    ("Ciphertext", BUFFER),
    ("Mac", BUFFER)
  ]

  @classmethod
  def makePlsData(cls, ciphertext, mac):
    pkt = cls()
    pkt.Ciphertext = ciphertext
    pkt.Mac = mac
    return pkt

class PlsClose(PlsBasicType):
  DEFINITION_IDENTIFIER = "netsecfall2017.pls.close"
  DEFINITION_VERSION = "1.0"
  FIELDS = [
    ("Error", STRING({Optional:True}))
  ]

  @classmethod
  def makePlsData(cls, error):
    pkt = cls()
    pkt.Error = error
    return pkt