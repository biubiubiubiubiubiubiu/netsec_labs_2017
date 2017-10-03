from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
from PEEPPacket import PEEPPacket

class PEEPTransport(StackingTransport):
    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol

    def write(self, data):
        if self.protocol:
            print("PEEPTransport: Write got {} bytes of data to package".format(len(data)))
            # Currently add chunking
            i = 0
            n = 0
            self.chunk = list()
            while(i < len(data)):
                if i + 1024 > len(data):
                    self.chunk[n]=data[i:i+1024]
                    i = i + 1024
                    n = n + 1
                    pkt = PEEPPacket.makeDataPacket(self.protocol.raisedSeqNum(len(chunk[n])), chunk[n])
                    super().write(pkt.__serialize__())
                else:
                    self.chunk[n]=data[i]
                    pkt = PEEPPacket.makeDataPacket(self.protocol.raisedSeqNum(len(chunk[n])), chunk[n])
                    super().write(pkt.__serialize__())

        else:
            print("PEEPTransport: Undefined protocol, writing anyway...")
            print("PEEPTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
            super().write(data)