from playground.network.packet import PacketType
import asyncio
import os
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
import playground

class AppTransport(StackingTransport):

    def write(self, data):
        print("AppTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
        super().write(data)