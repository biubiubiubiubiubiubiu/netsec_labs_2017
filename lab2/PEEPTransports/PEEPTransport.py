from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
from PEEPPacket import PEEPPacket

class PEEPTransport(StackingTransport):

    MAXBYTE = 1024

    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol

    def write(self, data):
        if self.protocol:
            print("PEEPTransport: Write got {} bytes of data to package".format(len(data)))
            # Currently no chunking
            i = 0
            index = 1
            while (i < len(data)):
                print("sending {!r} packet".format(index))
                sentData = None
                if (i + self.MAXBYTE < len(data)):
                    sentData = data[i: i + self.MAXBYTE]
                else:
                    sentData = data[i:]
                i += self.MAXBYTE
                pkt = PEEPPacket.makeDataPacket(self.protocol.raisedSeqNum(len(sentData)), sentData)
                self.protocol.sentDataCache.append(sentData)
                index += 1
                super().write(pkt.__serialize__())
            print("PEEPTransport: data transmitting finished, number of packets sent: {!r}".format( + 1))
        
        else:
            print("PEEPTransport: Undefined protocol, writing anyway...")
            print("PEEPTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
            super().write(data)
            