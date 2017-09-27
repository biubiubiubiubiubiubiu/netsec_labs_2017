from HandShake import HandShake
from playground.network.packet import PacketType
import asyncio
import os


class ServerProtocol(asyncio.Protocol):
    STATE_DESC = {
        0: "SYN_ACK",
        1: "SYN",
        2: "TRANSMISSION"
    }

    STATE_SERVER_SYN_ACK = 0
    STATE_SERVER_SYN = 1
    STATE_SERVER_TRANSMISSION = 2

    def __init__(self, loop=None, callback=None):
        print("Hello server")
        self.state = ServerProtocol.STATE_SERVER_SYN_ACK
        self.transport = None
        self.deserializer = PacketType.Deserializer()
        self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
        self.clientSeqNum = None
        self.loop = loop
        self.callback = callback

    def connection_made(self, transport):
        print("connection made!")
        self.transport = transport

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, HandShake):
                if pkt.Type == HandShake.TYPE_SYN:
                    print("Received SYN packet with sequence number " +
                          str(pkt.SequenceNumber))
                    self.state = ServerProtocol.STATE_SERVER_SYN
                    self.clientSeqNum = pkt.SequenceNumber + 1
                    synAckPacket = HandShake()
                    synAckPacket.Type = HandShake.TYPE_SYN_ACK
                    synAckPacket.SequenceNumber = self.seqNum
                    synAckPacket.Acknowledgement = self.clientSeqNum
                    print("Sending SYN_ACK packet with sequence number " + str(self.seqNum) +
                          ", current state " + ServerProtocol.STATE_DESC[self.state])
                    self.transport.write(synAckPacket.__serialize__())
                elif pkt.Type == HandShake.TYPE_ACK:
                    print("Received ACK packet with sequence number " +
                          str(pkt.SequenceNumber))
                    self.state = ServerProtocol.STATE_SERVER_TRANSMISSION
                    self.seqNum += 1
                    self.clientSeqNum = pkt.SequenceNumber + 1
                    if self.callback:
                        self.callback(
                            self, {"type": HandShake.TYPE_ACK, "state": self.state})
                elif pkt.Type == HandShake.TYPE_RIP:
                    print("Received RIP packet with sequence number " +
                          str(pkt.SequenceNumber))
                    self.seqNum += 1
                    self.clientSeqNum = pkt.SequenceNumber + 1
                    ripAckPacket = HandShake()
                    ripAckPacket.Type = HandShake.TYPE_RIP_ACK
                    ripAckPacket.SequenceNumber = self.seqNum
                    ripAckPacket.Acknowledgement = self.clientSeqNum
                    print("Sending RIP-ACK packet with sequence number " + str(self.seqNum) +
                          ", current state " + ServerProtocol.STATE_DESC[self.state])
                    self.transport.write(ripAckPacket.__serialize__())
                    # NOT IMPLEMENTED: send remaining packets in buffer
                    self.sendRip()
                elif pkt.Type == HandShake.TYPE_RIP_ACK:
                    print("Received RIP-ACK packet with sequence number " +
                          str(pkt.SequenceNumber))
                    print("Closing...")
                    self.stop()
                else:
                    print("Wrong packet type: " + str(pkt.Type))
            else:
                print("Wrong packet class type")

    def connection_lost(self, exc):
        print('The client closed the connection')
        self.transport = None
        self.stop()

    def stop(self):
        if self.transport:
            self.transport.close()
        if self.loop:
            print("Goodbye!")
            self.loop.stop()

    def sendRip(self):
        ripPacket = HandShake()
        ripPacket.Type = HandShake.TYPE_RIP
        ripPacket.SequenceNumber = self.seqNum
        ripPacket.Acknowledgement = self.clientSeqNum
        print("Sending RIP packet with sequence number " + str(self.seqNum) +
              ", current state " + ServerProtocol.STATE_DESC[self.state])
        self.transport.write(ripPacket.__serialize__())

    # def sendData(self, data):
    #     if self.state == ServerProtocol.STATE_SERVER_TRANSMISSION:
    #         print("Sending data")
    #         dataPacket = HandShake()
    #         dataPacket.Type = None # Handshake.TYPE_DATA
    #         dataPacket.SequenceNumber = self.seqNum
    #         dataPacket.Checksum = None # checksum()
    #         dataPacket.Data = data
    #     else:
    #         print("Wrong client state")
