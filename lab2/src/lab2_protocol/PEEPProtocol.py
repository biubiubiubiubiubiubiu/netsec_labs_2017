from .PEEPPacket import PEEPPacket
from playground.network.packet import PacketType
import os
from playground.network.common import StackingProtocol
from threading import Timer
import time
import asyncio, random


class PEEPProtocol(StackingProtocol):
    # Constants
    WINDOW_SIZE = 10
    TIMEOUT = 0.5
    MAX_RIP_RETRIES = 4
    SCAN_INTERVAL = 0.01
    DEBUG_MODE = False
    # change the value to change the transmission unreliability
    LOSS_RATE = 0

    # State definitions
    STATE_DESC = {
        0: "DEFAULT",
        100: "SERVER_SYN_ACK",
        101: "SERVER_SYN",
        102: "SERVER_TRANSMISSION",
        103: "SERVER_CLOSING",
        104: "SERVER_CLOSED",
        200: "CLIENT_INITIAL_SYN",
        201: "CLIENT_SYN_ACK",
        202: "CLIENT_TRANSMISSION",
        203: "CLIENT_CLOSING",
        204: "CLIENT_CLOSED"
    }

    STATE_DEFAULT = 0

    STATE_SERVER_SYN_ACK = 100
    STATE_SERVER_SYN = 101
    STATE_SERVER_TRANSMISSION = 102
    STATE_SERVER_CLOSING = 103
    STATE_SERVER_CLOSED = 104

    STATE_CLIENT_INITIAL_SYN = 200
    STATE_CLIENT_SYN_ACK = 201
    STATE_CLIENT_TRANSMISSION = 202
    STATE_CLIENT_CLOSING = 203
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

        self.tasks = []

    def connection_made(self, transport):
        self.dbgPrint("Connection made")
        self.transport = transport

    def connection_lost(self, exc):
        self.dbgPrint("Connection closed")
        self.transport = None
        self.higherProtocol().connection_lost(exc)

    def dbgPrint(self, text):
        if self.DEBUG_MODE:
            print(type(self).__name__ + ": " + text)

    def raisedSeqNum(self, amount=1):
        self.seqNum += amount
        return self.seqNum

    def stop(self):
        self.dbgPrint("Goodbye! Remaining task number: " + str(len(self.tasks)))
        future = asyncio.gather(*self.tasks, return_exceptions=True)
        future.add_done_callback(lambda res: self.transport.lowerTransport().close())
        future.cancel()

    def sendSyn(self):
        synPacket = PEEPPacket.makeSynPacket(self.seqNum)
        self.dbgPrint("Sending SYN packet with sequence number " + str(self.seqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.writeWithRate(synPacket, "Syn")

    def sendSynAck(self, synAck_seqNum):
        synAckPacket = PEEPPacket.makeSynAckPacket(synAck_seqNum, self.partnerSeqNum)
        self.dbgPrint("Sending SYN_ACK packet with sequence number " + str(synAck_seqNum) +
                      ", ack number " + str(self.partnerSeqNum) + ", current state " + self.STATE_DESC[self.state])

        self.writeWithRate(synAckPacket, "SynAck")

    def sendAck(self):
        ackPacket = PEEPPacket.makeAckPacket(self.partnerSeqNum)
        self.dbgPrint("Sending ACK packet with acknowledgement " + str(self.partnerSeqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.writeWithRate(ackPacket, "Ack")

    def sendRip(self):
        ripPacket = PEEPPacket.makeRipPacket(self.seqNum, self.partnerSeqNum)
        self.dbgPrint("Sending RIP packet with sequence number " + str(self.seqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.writeWithRate(ripPacket, "Rip")

    def sendRipAck(self):
        ripAckPacket = PEEPPacket.makeRipAckPacket(self.partnerSeqNum)
        self.dbgPrint("Sending RIP-ACK packet with ack number " + str(self.partnerSeqNum) +
                      ", current state " + self.STATE_DESC[self.state])
        self.writeWithRate(ripAckPacket, "RipAck")
        # self.transport.write(ripAckPacket.__serialize__())

    def processDataPkt(self, pkt):
        if self.isClosing():
            self.dbgPrint("Closing, ignored data packet with seq " + str(pkt.SequenceNumber))
        elif pkt.SequenceNumber == self.partnerSeqNum:
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
                          str(pkt.SequenceNumber) + ",current: {!r}, discarded.".format(self.partnerSeqNum))

        # send an ack anyway
        acknowledgement = self.partnerSeqNum
        ackPacket = PEEPPacket.makeAckPacket(acknowledgement)
        self.dbgPrint("Sending ACK packet with acknowledgement " + str(acknowledgement) +
                      ", current state " + self.STATE_DESC[self.state])
        self.writeWithRate(ackPacket, "Ack")

    def processAckPkt(self, pkt):
        self.dbgPrint("Received ACK packet with acknowledgement number " +
                      str(pkt.Acknowledgement))
        latestAckNumber = pkt.Acknowledgement
        for ackNumber in list(self.sentDataCache):
            if ackNumber <= latestAckNumber:
                if len(self.sendingDataBuffer) > 0:
                    (nextAck, dataPkt) = self.sendingDataBuffer.pop(0)
                    self.dbgPrint("Sending next packet " + str(nextAck) + " in sendingDataBuffer...")
                    self.sentDataCache[nextAck] = (dataPkt, time.time())
                    self.writeWithRate(dataPkt, "Data")
                self.dbgPrint("Received ACK for dataSeq: {!r}, removing".format(
                    self.sentDataCache[ackNumber][0].SequenceNumber))
                del self.sentDataCache[ackNumber]

    async def checkState(self, states, callback, maxRetry=-1):
        retry = maxRetry
        while self.state not in states and retry != 0:
            self.dbgPrint("checkState at time " + str(time.time()))
            await asyncio.sleep(self.TIMEOUT)
            self.dbgPrint("checkState (after sleep) at time " + str(time.time()))
            if self.state not in states:
                self.dbgPrint("Timeout on state " + self.STATE_DESC[self.state] +
                              ", expected " + str([self.STATE_DESC[state] for state in states]))
                callback()
            if retry > 0:
                retry -= 1

    async def scanCache(self):
        while not self.isClosing():
            for ackNumber in self.sentDataCache:
                (dataPkt, timestamp) = self.sentDataCache[ackNumber]
                currentTime = time.time()
                if currentTime - timestamp >= self.TIMEOUT:
                    # resend data packet after timeout
                    self.dbgPrint("Resending packet " + str(dataPkt.SequenceNumber) + " in cache...")
                    self.writeWithRate(dataPkt, "Data")
                    self.sentDataCache[ackNumber] = (dataPkt, currentTime)
            await asyncio.sleep(self.SCAN_INTERVAL)

    async def checkAllSent(self, callback):
        while self.sentDataCache or self.sendingDataBuffer:
            await asyncio.sleep(self.SCAN_INTERVAL)
        callback()

    def writeWithRate(self, pkt, pktType):
        sent_val = random.uniform(0, 1)
        if sent_val > self.LOSS_RATE and self.transport:
            # self.dbgPrint(
            #     "{!r} packet in cache is sent out successfully, sequenceNum: {!r}, sent_val: {!r}".format(pktType,
            #                                                                                               pkt.SequenceNumber,
            #                                                                                               sent_val))
            self.transport.write(pkt.__serialize__())
        else:
            self.dbgPrint(
                "{!r} packet failed to send out successfully, sequenceNum: {!r}, sent_val: {!r}".format(pktType,
                                                                                                        pkt.SequenceNumber,
                                                                                                        sent_val))

    def prepareForRip(self):
        raise NotImplementedError("prepareForRip() not implemented")

    def isClosing(self):
        raise NotImplementedError("isClosing() not implemented")
