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

        self.sentDataCache = {}
        self.sendingDataBuffer = []
        self.receivedDataBuffer = {}

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

    def processDataPkt(self, pkt, needAck=True):
        if pkt.SequenceNumber == self.partnerSeqNum:
            # If it is ordered, update self.partnerSeqNum and push it up
            print("Received DATA packet with sequence number " +
                  str(pkt.SequenceNumber))
            self.partnerSeqNum = pkt.SequenceNumber + len(pkt.Data)
            self.higherProtocol().data_received(pkt.Data)
            # Recursively pop and process next packet in buffer if it exists
            if self.partnerSeqNum in self.receivedDataBuffer:
                self.processDataPkt(self.receivedDataBuffer.pop(self.partnerSeqNum), False)
        elif pkt.SequenceNumber > self.partnerSeqNum:
            # if the order of pkt is wrong, temporarily append it to buffer
            print("Received DATA packet with higher sequence number " +
                  str(pkt.SequenceNumber) + ", buffered.")
            self.receivedDataBuffer[pkt.SequenceNumber] = pkt
        else:
            # wrong packet seqNum, discard
            print("ERROR: Received DATA packet with lower sequence number " +
                  str(pkt.SequenceNumber) + ", discarded.")

        # send an ack anyway
        if needAck:
            acknowledgement = pkt.SequenceNumber + len(pkt.Data)
            ackPacket = PEEPPacket.makeAckPacket(acknowledgement)
            print("Sending ACK packet with acknowledgement " + str(acknowledgement) +
                  ", current state " + self.STATE_DESC[self.state])
            self.transport.write(ackPacket.__serialize__())

    def processAckPkt(self, pkt):
        print("Received ACK packet with acknowledgement number " +
              str(pkt.Acknowledgement))
        dataRemoveSeq = pkt.Acknowledgement
        if dataRemoveSeq in self.sentDataCache:
            print("Server: Received ACK for dataSeq: {!r}, removing".format(dataRemoveSeq))
            del self.sentDataCache[dataRemoveSeq]
            if len(self.sendingDataBuffer) > 0:
                (ackNumber, dataPkt) = self.sendingDataBuffer.pop(0)
                print("Server: Sending next packet in readyDataCache...")
                self.sentDataCache[ackNumber] = dataPkt
                self.transport.write(dataPkt.__serialize__())
