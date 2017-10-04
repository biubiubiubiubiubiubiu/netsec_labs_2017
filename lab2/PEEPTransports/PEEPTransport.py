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
            self.dataChunks = self.split(data)
            for dataChunk in dataChunks:
                pkt = PEEPPacket.makeDataPacket(self.protocol.raisedSeqNum(len(data)), data)
                super().write(pkt.__serialize__())
            print("PEEPTransport: data transmitting finished, number of packets sent: {!r}".format(len(self.dataChunks)))
        
        else:
            print("PEEPTransport: Undefined protocol, writing anyway...")
            print("PEEPTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
            super().write(data)

    def split(self, data):
        splittedData = []
        index = 0
        while (index < len(data)):
            n = len(splittedData)
            if (index + MAXBYTE < len(data)):
                splittedData.append((n, data[i: i + MAXBYTE]))
            else:
                splittedData.append((n, data[i:]))
            