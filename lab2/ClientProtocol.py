from HandShake import HandShake
from playground.network.packet import PacketType
import asyncio

class ClientProtocol(asyncio.Protocol):
    STATE_CLIENT_INITIAL_SYN = 0
    STATE_CLIENT_SYN_ACK = 1
    STATE_CLIENT_TRANSMISSION = 2

    def __init__(self):
        print("Hello client")
        self.state = ClientProtocol.STATE_CLIENT_INITIAL_SYN
        self.transport = None
        self.deserializer = PacketType.Deserializer()

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            print("Packet received")
            if isinstance(pkt, HandShake):
                print("Handshake!")
            else:
                print("Wrong packet type")

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.transport = None