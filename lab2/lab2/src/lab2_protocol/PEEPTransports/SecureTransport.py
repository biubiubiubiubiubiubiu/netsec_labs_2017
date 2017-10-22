from playground.network.common import StackingTransport


class SecureTransport(StackingTransport):
    def write(self, data):
        print("SecureTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
        super().write(data)
