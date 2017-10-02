from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
from PEEPPacket import PEEPPacket

class PEEPTransport(StackingTransport):
    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol

    def write(self, data):
        if self.protocol:
            print("PEEPTransport: Write got {} bytes of data to package".format(len(data)))
            # Currently no chunking
            pkt = PEEPPacket.makeDataPacket(self.protocol.raisedSeqNum(len(data)), data)
            super().write(pkt.__serialize__())
        else:
            print("PEEPTransport: Undefined protocol, writing anyway...")
            print("PEEPTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
            super().write(data)