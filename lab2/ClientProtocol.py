from HandShake import HandShake
from playground.network.packet import PacketType
import asyncio
import os

class ClientProtocol(asyncio.Protocol):
    STATE_CLIENT_INITIAL_SYN = 0
    STATE_CLIENT_SYN_ACK = 1
    STATE_CLIENT_TRANSMISSION = 2

    def __init__(self):
        print("Hello client")
        self.state = ClientProtocol.STATE_CLIENT_INITIAL_SYN
        self.transport = None
        self.deserializer = PacketType.Deserializer()
        self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
        self.serverSeqNum = None

    def connection_made(self, transport):
        self.transport = transport
        if self.state == ClientProtocol.STATE_CLIENT_INITIAL_SYN:
            synPacket = HandShake()
            synPacket.Type = HandShake.TYPE_SYN
            synPacket.SequenceNumber = self.seqNum
            self.transport.write(synPacket.__serialize__())

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            print("Packet received")
            print("Packet received")
            if isinstance(pkt, HandShake):
                print("Handshake!")
                if pkt.Type == HandShake.TYPE_SYN_ACK:
                    print("Received Syn-Ack packet")
                    self.state = ClientProtocol.STATE_CLIENT_TRANSMISSION
                    self.seqNum += 1
                    self.serverSeqNum = pkt.SequenceNumber + 1
                    ackPacket = HandShake()
                    ackPacket.Type = HandShake.TYPE_ACK
                    ackPacket.SequenceNumber = self.seqNum
                    ackPacket.Acknowledgement = pkt.SequenceNumber + 1
                    self.transport.write(ackPacket.__serialize__())
                else:
                    print("Wrong packet type")
            else:
                print("Wrong packet class type")

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.transport = None

    def sendData(self, data):
        if self.state == ClientProtocol.STATE_CLIENT_TRANSMISSION:
            print("Sending data")
            dataPacket = HandShake()
            dataPacket.Type = None # Handshake.TYPE_DATA
            dataPacket.SequenceNumber = self.seqNum
            dataPacket.Checksum = None # checksum()
            dataPacket.Data = data

        else:
            print("Wrong client state")