from .PEEPPacket import PEEPPacket
from playground.network.packet import PacketType
import os
from playground.network.common import StackingProtocol

class PEEPProtocol(StackingProtocol):
    # Constants
    WINDOW_SIZE = 4
    RECIPIENT_WINDOW_SIZE = 100

    # State definitions
    STATE_DESC = {
        0: "DEFAULT",
        100: "SERVER_SYN_ACK",
        101: "SERVER_SYN",
        102: "SERVER_TRANSMISSION",
        200: "CLIENT_INITIAL_SYN",
        201: "CLIENT_SYN_ACK",
        202: "CLIENT_TRANSMISSION"
    }

    STATE_DEFAULT = 0

    STATE_SERVER_SYN_ACK = 100
    STATE_SERVER_SYN = 101
    STATE_SERVER_TRANSMISSION = 102

    STATE_CLIENT_INITIAL_SYN = 200
    STATE_CLIENT_SYN_ACK = 201
    STATE_CLIENT_TRANSMISSION = 202

    def __init__(self):
        super().__init__()
        self.state = self.STATE_DEFAULT
        self.transport = None
        self.deserializer = PacketType.Deserializer()
        self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
        self.partnerSeqNum = None
        self.receivedDataCache = []
        self.sentDataCache = {}
        self.readyDataCache = []
        self.receivedAckCache = {}
        self.sentAckCache = {}

    def connection_made(self, transport):
        print("Connection made")
        self.transport = transport

    def connection_lost(self, exc):
        print('The partner closed the connection')
        self.transport = None
        self.stop()

    def raisedSeqNum(self, amount=1):
        self.seqNum += amount
        return self.seqNum

    def stop(self):
        print("Goodbye!")
        if self.transport:
            self.transport.close()

    def sendRip(self):
        self.seqNum += 1
        ripPacket = PEEPPacket.makeRipPacket(self.seqNum, self.partnerSeqNum)
        print("Sending RIP packet with sequence number " + str(self.seqNum) +
              ", current state " + self.STATE_DESC[self.state])
        self.transport.write(ripPacket.__serialize__())

    def processDataPkt(self, pkt):
        self.partnerSeqNum = pkt.SequenceNumber + 1
        ackPacket = PEEPPacket.makeAckPacket(self.raisedSeqNum(), self.partnerSeqNum)
        print("Sending ACK packet with sequence number " + str(self.seqNum) + ",ack number " + str(self.partnerSeqNum)+
            ", current state " + self.STATE_DESC[self.state])
        self.transport.write(ackPacket.__serialize__())
        self.higherProtocol().data_received(pkt.Data)
