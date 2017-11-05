from playground.network.common import StackingTransport

class PLSTransport(StackingTransport):
    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol

    def write(self, data):
        self.protocol.dbgPrint("Write got {} bytes of data to pass to lower layer".format(len(data)))
        plsData = self.protocol.makePlsData(data)
        super().write(plsData.__serialize__())

    def close(self):
        self.protocol.sendPlsClose()
        # super().close()