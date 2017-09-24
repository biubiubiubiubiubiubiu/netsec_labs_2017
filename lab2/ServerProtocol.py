from HandShake import HandShake
from playground.network.packet import PacketType
import asyncio

class ServerProtocol(asyncio.Protocol):
    STATE_SERVER_SYN_ACK = 0
    STATE_SERVER_SYN = 1
    STATE_SERVER_TRANSMISSION = 2

    def __init__(self):
        print("Hello server")
        self.state = ServerProtocol.STATE_SERVER_SYN_ACK
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
                print("Wrong packet type.")

    def connection_lost(self, exc):
        print('The client closed the connection')
        self.transport = None