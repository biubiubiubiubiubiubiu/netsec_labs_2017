from playground.network.common import StackingTransport
from ..PEEPPacket import PEEPPacket
import time
import asyncio
import random


class PEEPTransport(StackingTransport):
    CHUNK_SIZE = 1024

    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol

    def write(self, data):
        if self.protocol:
            if not self.protocol.isClosing():
                self.protocol.dbgPrint("PEEPTransport: Write got {} bytes of data to package".format(len(data)))
                # Create data chunks
                i = 0
                index = 0
                sentData = None
                while (i < len(data)):
                    if (i + self.CHUNK_SIZE < len(data)):
                        sentData = data[i: i + self.CHUNK_SIZE]
                    else:
                        sentData = data[i:]
                    i += len(sentData)
                    pkt = PEEPPacket.makeDataPacket(self.protocol.seqNum, sentData)
                    index += 1
                    ackNumber = self.protocol.seqNum + len(sentData)
                    if len(self.protocol.sentDataCache) <= self.protocol.WINDOW_SIZE:
                        self.protocol.dbgPrint(
                            "PEEPTransport: Sending packet {!r}, sequence number: {!r}".format(index,
                                                                                               pkt.SequenceNumber))
                        self.protocol.transport.write(pkt.__serialize__())
                        self.protocol.sentDataCache[ackNumber] = (pkt, time.time())
                        # determine the transmission is successful or not
                        # sent_val = random.uniform(0, 1)
                        # if (sent_val > self.protocol.LOSS_RATE):
                        #     print("packet is sent out successfully, sequenceNum: {!r}, sent_val: {!r}".format(pkt.SequenceNumber, sent_val))
                        #     # super().write(pkt.__serialize__())
                        # else:
                        #     print("packet failed to send out, sequenceNum: {!r}, sent_val: {!r}".format(pkt.SequenceNumber, sent_val))
                    else:
                        self.protocol.dbgPrint(
                            "PEEPTransport: Buffering packet {!r}, sequence number: {!r}".format(index,
                                                                                                 pkt.SequenceNumber))
                        self.protocol.sendingDataBuffer.append((ackNumber, pkt))
                    self.protocol.seqNum += len(sentData)
                self.protocol.dbgPrint(
                    "PEEPTransport: Batch transmission finished, number of packets sent: {!r}".format(index))
            else:
                self.protocol.dbgPrint("PEEPTransport: protocol is closing, unable to write anymore.")

        else:
            self.protocol.dbgPrint("PEEPTransport: Undefined protocol, writing anyway...")
            self.protocol.dbgPrint("PEEPTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
            super().write(data)

    def close(self):
        # clear buffer then send RIP
        self.protocol.dbgPrint(
            "PEEPTransport: Transport closing, protocol state " + self.protocol.STATE_DESC[self.protocol.state]
            + ", seq " + str(self.protocol.seqNum) + ", partnerSeq " + str(self.protocol.partnerSeqNum))
        self.protocol.dbgPrint(
            "PEEPTransport: Current cache size " + str(len(self.protocol.sentDataCache)) + ", buffer size "
            + str(len(self.protocol.sendingDataBuffer)) + ", receive buffer "
            + str(len(self.protocol.receivedDataBuffer)) + ": " + str(list(self.protocol.receivedDataBuffer.keys())))
        if not self.protocol.isClosing():
            self.protocol.tasks.append(asyncio.ensure_future(self.protocol.checkAllSent(self.protocol.prepareForRip)))
        else:
            self.protocol.dbgPrint("PEEPTransport: Protocol is already closing.")
