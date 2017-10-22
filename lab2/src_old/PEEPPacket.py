from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, UINT8, UINT32, BUFFER
from playground.network.packet.fieldtypes.attributes import Optional
import zlib

class PEEPPacket(PacketType):
    TYPE_SYN = 0
    TYPE_SYN_ACK = 1
    TYPE_ACK = 2
    TYPE_RIP = 3
    TYPE_RIP_ACK = 4
    TYPE_RST = 5
    TYPE_DATA = 6

    DEFINITION_IDENTIFIER = "PEEP.Packet"
    DEFINITION_VERSION = "1.0"

    FIELDS = [
        ("Type", UINT8),
        ("SequenceNumber", UINT32({Optional: True})),
        ("Checksum", UINT16({Optional: True})),
        ("Acknowledgement", UINT32({Optional: True})),
        ("Data", BUFFER({Optional: True}))
    ]

    def calculateChecksum(self):
        oldChecksum = self.Checksum
        self.Checksum = 0
        bytes = self.__serialize__()
        self.Checksum = oldChecksum
        return zlib.adler32(bytes) & 0xffff

    def updateChecksum(self):
        self.Checksum = self.calculateChecksum()

    def verifyChecksum(self):
        return self.Checksum == self.calculateChecksum()

    @classmethod
    def makeSynPacket(cls, seq):
        pkt = cls()
        pkt.Type = cls.TYPE_SYN
        pkt.SequenceNumber = seq
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeSynAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_SYN_ACK
        pkt.SequenceNumber = seq
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_ACK
        pkt.SequenceNumber = seq
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeRipPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_RIP
        pkt.SequenceNumber = seq
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeRipAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_RIP_ACK
        pkt.SequenceNumber = seq
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeDataPacket(cls, seq, data):
        pkt = cls()
        pkt.Type = cls.TYPE_DATA
        pkt.SequenceNumber = seq
        pkt.Data = data
        pkt.updateChecksum()
        return pkt
