from playground.network.common import StackingTransport
from PEEPPacket import PEEPPacket
import time
from threading import Timer


class PEEPTransport(StackingTransport):
    CHUNK_SIZE = 10

    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol

    def write(self, data):
        if self.protocol:
            if not self.protocol.isClosing:
                print("PEEPTransport: Write got {} bytes of data to package".format(len(data)))
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
                    if index <= self.protocol.WINDOW_SIZE:
                        print("sending packet {!r}, sequence number: {!r}".format(index, pkt.SequenceNumber))
                        self.protocol.sentDataCache[ackNumber] = (pkt, time.time())
                        super().write(pkt.__serialize__())
                    else:
                        print("buffering packet {!r}, sequence number: {!r}".format(index, pkt.SequenceNumber))
                        self.protocol.sendingDataBuffer.append((ackNumber, pkt))
                    self.protocol.seqNum += len(sentData)
                print("PEEPTransport: data transmitting finished, number of packets sent: {!r}".format(index))
            else:
                print("PEEPTransport: protocol is closing, unable to write anymore.")

        else:
            print("PEEPTransport: Undefined protocol, writing anyway...")
            print("PEEPTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
            super().write(data)

    def close(self):
        # clear buffer then send RIP
        self.protocol.isClosing = True
        Timer(self.protocol.SCAN_INTERVAL, self.protocol.checkCacheIsEmpty, [self.protocol.prepareForRip]).start()
