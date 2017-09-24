from HandShake import HandShake
from playground.network.packet import PacketType
import asyncio
import os

class ServerProtocol(asyncio.Protocol):
    STATE_SERVER_SYN_ACK = 0
    STATE_SERVER_SYN = 1
    STATE_SERVER_TRANSMISSION = 2

    def __init__(self):
        print("Hello server")
        self.state = ServerProtocol.STATE_SERVER_SYN_ACK
        self.transport = None
        self.deserializer = PacketType.Deserializer()
        self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
        self.clientSeqNum = None

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            print("Packet received")
            if isinstance(pkt, HandShake):
                print("Handshake!")
                if pkt.Type == HandShake.TYPE_SYN:
                    print("Received Syn packet")
                    self.state = ServerProtocol.STATE_SERVER_SYN
                    self.clientSeqNum = pkt.SequenceNumber + 1
                    synAckPacket = HandShake()
                    synAckPacket.Type = HandShake.TYPE_SYN_ACK
                    synAckPacket.SequenceNumber = self.seqNum
                    synAckPacket.Acknowledgement = pkt.SequenceNumber + 1
                    self.transport.write(synAckPacket.__serialize__())
                elif pkt.Type == HandShake.TYPE_ACK:
                    print("Received Ack packet")
                    self.state = ServerProtocol.STATE_SERVER_TRANSMISSION
                    self.seqNum += 1
                    self.clientSeqNum = pkt.SequenceNumber + 1
                else:
                    print("Wrong packet type")
            else:
                print("Wrong packet class type")

    def connection_lost(self, exc):
        print('The client closed the connection')
        self.transport = None

    def sendData(self, data):
        if self.state == ServerProtocol.STATE_SERVER_TRANSMISSION:
            print("Sending data")
            dataPacket = HandShake()
            dataPacket.Type = None # Handshake.TYPE_DATA
            dataPacket.SequenceNumber = self.seqNum
            dataPacket.Checksum = None # checksum()
            dataPacket.Data = data

        else:
            print("Wrong client state")