from PEEPPacket import PEEPPacket
from playground.network.packet import PacketType
import os
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
from PEEPTransports.PEEPTransport import PEEPTransport


class ClientProtocol(StackingProtocol):
    STATE_DESC = {
        0: "INITIAL_SYN",
        1: "SYN_ACK",
        2: "TRANSMISSION"
    }

    STATE_CLIENT_INITIAL_SYN = 0
    STATE_CLIENT_SYN_ACK = 1
    STATE_CLIENT_TRANSMISSION = 2

    def __init__(self, loop=None, callback=None):
        super().__init__()
        self.state = ClientProtocol.STATE_CLIENT_INITIAL_SYN
        print("Initializing client with state " +
              ClientProtocol.STATE_DESC[self.state])
        self.transport = None
        self.deserializer = PacketType.Deserializer()
        self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
        self.serverSeqNum = None
        self.loop = loop
        self.callback = callback
        self.receivedDataCache = []
        self.sentDataCache = {}

    def connection_made(self, transport):
        self.transport = transport
        if self.state == ClientProtocol.STATE_CLIENT_INITIAL_SYN:
            synPacket = PEEPPacket.makeSynPacket(self.seqNum)
            print("Sending SYN packet with sequence number " + str(self.seqNum) +
                  ", current state " + ClientProtocol.STATE_DESC[self.state])
            print("Packet checksum: " + str(synPacket.Checksum))
            self.transport.write(synPacket.__serialize__())
            self.state = ClientProtocol.STATE_CLIENT_SYN_ACK

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PEEPPacket):
                if pkt.verifyChecksum():
                    if (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_SYN_ACK,
                            ClientProtocol.STATE_CLIENT_SYN_ACK):
                        # check ack num
                        if (pkt.Acknowledgement - 1 == self.seqNum):
                            print("Received SYN-ACK packet with sequence number " +
                                  str(pkt.SequenceNumber))
                            self.state = ClientProtocol.STATE_CLIENT_TRANSMISSION
                            self.serverSeqNum = pkt.SequenceNumber + 1
                            ackPacket = PEEPPacket.makeAckPacket(self.raisedSeqNum(), self.serverSeqNum)
                            print("Sending ACK packet with sequence number " + str(self.seqNum) +
                                  ", current state " + ClientProtocol.STATE_DESC[self.state])
                            self.transport.write(ackPacket.__serialize__())
                            # if self.callback:
                            #     self.callback(
                            #         self, {"type": PEEPPacket.TYPE_SYN_ACK, "state": self.state})
                            higherTransport = PEEPTransport(self.transport, self)
                            self.higherProtocol().connection_made(higherTransport)
                        else:
                            print("Client: Wrong SYN_ACK packet: ACK number: {!r}, expected: {!r}".format(
                                pkt.Acknowledgement - 1, self.seqNum))

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_ACK,
                            ClientProtocol.STATE_CLIENT_TRANSMISSION,
                            self.serverSeqNum):
                        print("Received ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        dataRemoveSeq = pkt.Acknowledgement - 1
                        if dataRemoveSeq in self.sentDataCache:
                            print("Client: Received ACK for dataSeq: {!r}, removing".format(dataRemoveSeq))
                            del self.sentDataCache[dataRemoveSeq]
                        self.serverSeqNum = pkt.SequenceNumber + 1

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_DATA,
                            ClientProtocol.STATE_CLIENT_TRANSMISSION):
                        print("Received DATA packet with sequence number " +
                              str(pkt.SequenceNumber))
                        if pkt.SequenceNumber - self.serverSeqNum <= PEEPTransport.MAXBYTE:
                            # If it is, send an ack on this packet, update self.clientSeqNum, push it up
                            self.processDataPkt(pkt)
                            if len(self.receivedDataCache) > 0:
                                # Sort the list, if there is a matching sequence number inside the list, push it up
                                self.receivedDataCache = sorted(self.receivedDataCache, key=lambda pkt: pkt.SequenceNumber)
                                while (self.receivedDataCache[0].SequenceNumber - self.serverSeqNum <= PEEPTransport.MAXBYTE):
                                    self.processDataPkt(self.receivedDataCache.pop(0))
                        else:
                            # if the order of pkt is wrong, simply append it to cache
                            self.receivedDataCache.append(pkt)

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP,
                            ClientProtocol.STATE_CLIENT_TRANSMISSION,
                            self.serverSeqNum):
                        print("Received RIP packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.serverSeqNum = pkt.SequenceNumber + 1
                        ripAckPacket = PEEPPacket.makeRipAckPacket(self.raisedSeqNum(), self.serverSeqNum)
                        print("Sending RIP-ACK packet with sequence number " + str(self.seqNum) +
                            ", current state " + ClientProtocol.STATE_DESC[self.state])
                        self.transport.write(ripAckPacket.__serialize__())
                        print("Closing...")
                        self.stop()
                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP_ACK,
                            ClientProtocol.STATE_CLIENT_TRANSMISSION,
                            self.serverSeqNum):
                        print("Received RIP-ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.serverSeqNum = pkt.SequenceNumber + 1
                    else:
                        print("Client: Wrong packet: seq num {!r}, type {!r}， current state: {!r}".format(
                            pkt.SequenceNumber, pkt.Type, ClientProtocol.STATE_DESC[self.state]))
                else:
                    print("Wrong packet checksum: " + str(pkt.Checksum))
            else:
                print("Wrong packet class type: {!r}, state: {!r} ".format(str(type(pkt)),
                                                                           ClientProtocol.STATE_DESC[self.state]))

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.transport = None
        self.stop()

    def raisedSeqNum(self, amount=1):
        self.seqNum += amount
        return self.seqNum

    def stop(self):
        print("Goodbye!")
        if self.transport:
            self.transport.close()
        if self.loop:
            self.loop.stop()

    def sendRip(self):
        self.seqNum += 1
        ripPacket = PEEPPacket.makeRipPacket(self.seqNum, self.serverSeqNum)
        print("Sending RIP packet with sequence number " + str(self.seqNum) +
              ", current state " + ClientProtocol.STATE_DESC[self.state])
        self.transport.write(ripPacket.__serialize__())

    def processDataPkt(self, pkt):
        self.serverSeqNum = pkt.SequenceNumber + 1
        ackPacket = PEEPPacket.makeAckPacket(self.raisedSeqNum(), self.serverSeqNum)
        print("Sending ACK packet with sequence number " + str(self.seqNum) + ",ack number " + str(self.serverSeqNum)+
            ", current state " + ClientProtocol.STATE_DESC[self.state])
        self.transport.write(ackPacket.__serialize__())
        self.higherProtocol().data_received(pkt.Data)