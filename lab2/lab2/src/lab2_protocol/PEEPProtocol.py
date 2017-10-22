from .PEEPPacket import PEEPPacket
from playground.network.packet import PacketType
import os
from playground.network.common import StackingProtocol
from threading import Timer
import time
import asyncio


class PEEPProtocol(StackingProtocol):
    # Constants
    WINDOW_SIZE = 10
    TIMEOUT = 3
    SCAN_INTERVAL = 0.1
    DEBUG_MODE = False

    # State definitions
    STATE_DESC = {
        0: "DEFAULT",
        100: "SERVER_SYN_ACK",
        101: "SERVER_SYN",
        102: "SERVER_TRANSMISSION",
        # 103: "SERVER_CLOSING",
        104: "SERVER_CLOSED",
        200: "CLIENT_INITIAL_SYN",
        201: "CLIENT_SYN_ACK",
        202: "CLIENT_TRANSMISSION",
        # 203: "CLIENT_CLOSING",
        204: "CLIENT_CLOSED"
    }

    STATE_DEFAULT = 0

    STATE_SERVER_SYN_ACK = 100
    STATE_SERVER_SYN = 101
    STATE_SERVER_TRANSMISSION = 102
    # STATE_SERVER_CLOSING = 103
    STATE_SERVER_CLOSED = 104

    STATE_CLIENT_INITIAL_SYN = 200
    STATE_CLIENT_SYN_ACK = 201
    STATE_CLIENT_TRANSMISSION = 202
    # STATE_CLIENT_CLOSING = 203
    STATE_CLIENT_CLOSED = 204

    def __init__(self):
        super().__init__()
        self.state = self.STATE_DEFAULT
        self.transport = None
        self.deserializer = PEEPPacket.Deserializer()
        self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
        self.partnerSeqNum = None

        self.sentDataCache = {}
        self.sendingDataBuffer = []
        self.receivedDataBuffer = {}

        # TODO: temporary solution?
        self.isClosing = False

        self.tasks = []

    def connection_made(self, transport):
        self.dbgPrint("Connection made")
        self.transport = transport

    def connection_lost(self, exc):
        self.dbgPrint("PEEPProtocol: Connection closed")
        self.transport = None
        asyncio.gather(*self.tasks).add_done_callback(lambda res: self.higherProtocol().connection_lost(exc))

    def dbgPrint(self, text):
        if self.DEBUG_MODE:
            print(text)

    def raisedSeqNum(self, amount=1):
        self.seqNum += amount
        return self.seqNum

    def stop(self):
        self.dbgPrint("Goodbye!")
        if self.transport:
            self.transport.close()

    def sendSyn(self):
        synPacket = PEEPPacket.makeSynPacket(self.seqNum)
        self.dbgPrint("Sending SYN packet with sequence number " + str(self.seqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.dbgPrint("Packet checksum: " + str(synPacket.Checksum))
        self.transport.write(synPacket.__serialize__())

    def sendSynAck(self):
        synAckPacket = PEEPPacket.makeSynAckPacket(self.seqNum, self.partnerSeqNum)
        self.dbgPrint("Sending SYN_ACK packet with sequence number " + str(self.seqNum) +
                      ", ack number " + str(self.partnerSeqNum) + ", current state " + self.STATE_DESC[self.state])
        self.transport.write(synAckPacket.__serialize__())

    def sendAck(self):
        ackPacket = PEEPPacket.makeAckPacket(self.partnerSeqNum)
        self.dbgPrint("Sending ACK packet with acknowledgement " + str(self.partnerSeqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.transport.write(ackPacket.__serialize__())

    def sendRip(self):
        ripPacket = PEEPPacket.makeRipPacket(self.seqNum, self.partnerSeqNum)
        self.dbgPrint("Sending RIP packet with sequence number " + str(self.seqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.transport.write(ripPacket.__serialize__())

    def sendRipAck(self):
        ripAckPacket = PEEPPacket.makeRipAckPacket(self.partnerSeqNum)
        self.dbgPrint("Sending RIP-ACK packet with ack number " + str(self.partnerSeqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.transport.write(ripAckPacket.__serialize__())

    def processDataPkt(self, pkt):
        if pkt.SequenceNumber == self.partnerSeqNum:
            # If it is ordered, update self.partnerSeqNum and push it up
            self.dbgPrint("Received DATA packet with sequence number " +
                          str(pkt.SequenceNumber))
            self.partnerSeqNum = pkt.SequenceNumber + len(pkt.Data)
            self.higherProtocol().data_received(pkt.Data)
            # Pop and process other packets in buffer
            while self.partnerSeqNum in self.receivedDataBuffer:
                nextPkt = self.receivedDataBuffer.pop(self.partnerSeqNum)
                self.partnerSeqNum = nextPkt.SequenceNumber + len(nextPkt.Data)
                self.higherProtocol().data_received(nextPkt.Data)
        elif pkt.SequenceNumber > self.partnerSeqNum:
            # if the order of pkt is wrong, temporarily append it to buffer
            self.dbgPrint("Received DATA packet with higher sequence number " +
                          str(pkt.SequenceNumber) + ", buffered.")
            self.receivedDataBuffer[pkt.SequenceNumber] = pkt
        else:
            # wrong packet seqNum, discard
            self.dbgPrint("ERROR: Received DATA packet with lower sequence number " +
                          str(pkt.SequenceNumber) + ", discarded.")

        # send an ack anyway
        acknowledgement = self.partnerSeqNum
        ackPacket = PEEPPacket.makeAckPacket(acknowledgement)
        self.dbgPrint("Sending ACK packet with acknowledgement " + str(acknowledgement) +
                      ", current state " + self.STATE_DESC[self.state])
        self.transport.write(ackPacket.__serialize__())

    def processAckPkt(self, pkt):
        self.dbgPrint("Received ACK packet with acknowledgement number " +
                      str(pkt.Acknowledgement))
        latestAckNumber = pkt.Acknowledgement
        for ackNumber in list(self.sentDataCache):
            if ackNumber <= latestAckNumber:
                if len(self.sendingDataBuffer) > 0:
                    (nextAck, dataPkt) = self.sendingDataBuffer.pop(0)
                    self.dbgPrint("Server: Sending next packet in sendingDataBuffer...")
                    self.sentDataCache[nextAck] = (dataPkt, time.time())
                    self.transport.write(dataPkt.__serialize__())
                self.dbgPrint("Server: Received ACK for dataSeq: {!r}, removing".format(
                    self.sentDataCache[ackNumber][0].SequenceNumber))
                del self.sentDataCache[ackNumber]

    async def checkState(self, states, callback):
        while self.state not in states:
            await asyncio.sleep(self.TIMEOUT)
            if self.state not in states:
                self.dbgPrint("Timeout on state " + self.STATE_DESC[self.state] +
                              ", expected " + str([self.STATE_DESC[state] for state in states]))
                callback()

    async def scanCache(self):
        while not self.isClosed():
            for ackNumber in self.sentDataCache:
                (dataPkt, timestamp) = self.sentDataCache[ackNumber]
                currentTime = time.time()
                if currentTime - timestamp >= self.TIMEOUT:
                    # resend data packet after timeout
                    self.dbgPrint("Sending packet " + str(dataPkt.SequenceNumber) + " in cache...")
                    self.transport.write(dataPkt.__serialize__())
                    self.sentDataCache[ackNumber] = (dataPkt, currentTime)
            await asyncio.sleep(self.SCAN_INTERVAL)

    async def checkCacheIsEmpty(self, callback):
        while self.sentDataCache:
            await asyncio.sleep(self.SCAN_INTERVAL)
        callback()

    def prepareForRip(self):
        raise NotImplementedError("PEEPProtocol: prepareForRip() not implemented")

    def isClosed(self):
        raise NotImplementedError("PEEPProtocol: isClosed() not implemented")
