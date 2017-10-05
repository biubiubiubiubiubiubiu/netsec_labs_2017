from PEEPPacket import PEEPPacket
from playground.network.packet import PacketType
import os
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
from PEEPTransports.PEEPTransport import PEEPTransport

class ServerProtocol(StackingProtocol):
    STATE_DESC = {
        0: "SYN_ACK",
        0.5: "STATE_SERVER_WAITING_ACK",
        1: "SYN",
        2: "TRANSMISSION"
    }

    STATE_SERVER_SYN_ACK = 0
    STATE_SERVER_SYN = 1
    STATE_SERVER_TRANSMISSION = 2

    def __init__(self, loop=None, callback=None):
        super().__init__()
        print("Hello server")
        self.state = ServerProtocol.STATE_SERVER_SYN_ACK
        self.transport = None
        self.deserializer = PacketType.Deserializer()
        self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
        self.clientSeqNum = None
        self.loop = loop
        self.callback = callback
        self.receivedDataCache = []
        self.sentDataCache = {}

    def connection_made(self, transport):
        print("connection made!")
        self.transport = transport

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PEEPPacket):
                if pkt.verifyChecksum():
                    if (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_SYN,
                            ServerProtocol.STATE_SERVER_SYN_ACK):
                        # the first way handshake, no need to check the sequence num
                        print("Received SYN packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.state = ServerProtocol.STATE_SERVER_SYN
                        # self.seqNum += 1
                        self.clientSeqNum = pkt.SequenceNumber + 1
                        synAckPacket = PEEPPacket.makeSynAckPacket(self.raisedSeqNum(), self.clientSeqNum)
                        print("Sending SYN_ACK packet with sequence number " + str(self.seqNum) +
                              ", current state " + ServerProtocol.STATE_DESC[self.state])
                        self.transport.write(synAckPacket.__serialize__())

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_ACK,
                            ServerProtocol.STATE_SERVER_SYN,
                            self.clientSeqNum):
                        if pkt.Acknowledgement - 1 == self.seqNum:
                            print("Received ACK packet with sequence number " +
                                  str(pkt.SequenceNumber))
                            self.clientSeqNum = pkt.SequenceNumber + 1
                            self.state = ServerProtocol.STATE_SERVER_TRANSMISSION
                            higherTransport = PEEPTransport(self.transport, self)
                            self.higherProtocol().connection_made(higherTransport)
                        else:
                            print("Server: Wrong ACK packet: ACK number: {!r}, expected: {!r}".format(
                                pkt.Acknowledgement - 1, self.seqNum))

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_ACK,
                            ServerProtocol.STATE_SERVER_TRANSMISSION,
                            self.clientSeqNum):
                        print("Received ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        dataRemoveSeq = pkt.Acknowledgement - 1
                        if dataRemoveSeq in self.sentDataCache:
                            print("Server: Received ACK for dataSeq: {!r}, removing".format(dataRemoveSeq))
                            del self.sentDataCache[dataRemoveSeq]
                        self.clientSeqNum = pkt.SequenceNumber + 1


                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_DATA,
                            ServerProtocol.STATE_SERVER_TRANSMISSION):
                        print("Received DATA packet with sequence number " +
                              str(pkt.SequenceNumber))
                        if pkt.SequenceNumber - self.clientSeqNum <= PEEPTransport.MAXBYTE:
                            # If it is, send an ack on this packet, update self.clientSeqNum, push it up
                            self.processDataPkt(pkt)
                            if len(self.receivedDataCache) > 0:
                                # Sort the list, if there is a matching sequence number inside the list, push it up
                                self.receivedDataCache = sorted(self.receivedDataCache,
                                                                key=lambda pkt: pkt.SequenceNumber)
                                while (self.receivedDataCache[
                                           0].SequenceNumber - self.clientSeqNum <= PEEPTransport.MAXBYTE):
                                    self.processDataPkt(self.receivedDataCache.pop(0))
                        else:
                            # if the order of pkt is wrong, simply append it to cache
                            self.receivedDataCache.append(pkt)

                            # self.clientSeqNum = pkt.SequenceNumber + 1
                            # self.higherProtocol().data_received(pkt.Data)
                            # # if self.callback:
                            # #     self.callback(
                            # #         self, {"type": PEEPPacket.TYPE_DATA, "state": self.state})
                            # ackPacket = PEEPPacket.makeAckPacket(self.raisedSeqNum(), self.clientSeqNum)

                            # self.transport.write(ackPacket.__serialize__())


                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP,
                            ServerProtocol.STATE_SERVER_TRANSMISSION,
                            self.clientSeqNum):
                        print("Received RIP packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.clientSeqNum = pkt.SequenceNumber + 1
                        ripAckPacket = PEEPPacket.makeRipAckPacket(self.raisedSeqNum(), self.clientSeqNum)
                        print("Sending RIP-ACK packet with sequence number " + str(self.seqNum) +
                              ", current state " + ServerProtocol.STATE_DESC[self.state])
                        self.transport.write(ripAckPacket.__serialize__())
                        # NOT IMPLEMENTED: send remaining packets in buffer
                        self.sendRip()


                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP_ACK,
                            ServerProtocol.STATE_SERVER_TRANSMISSION,
                            self.clientSeqNum):
                        print("Received RIP-ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        print("Closing...")
                        self.stop()

                    else:
                        print("Server: Wrong packet: seq num {!r}, type {!r}， current state: {!r}".format(
                            pkt.SequenceNumber, pkt.Type, ServerProtocol.STATE_DESC[self.state]))
                else:
                    print("Wrong packet checksum: " + str(pkt.Checksum))
            else:
                print("Wrong packet class type: {!r}, state: {!r} ".format(str(type(pkt)),
                                                                           ServerProtocol.STATE_DESC[self.state]))

    def connection_lost(self, exc):
        print('The client closed the connection')
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
        ripPacket = PEEPPacket.makeRipPacket(self.seqNum, self.clientSeqNum)
        print("Sending RIP packet with sequence number " + str(self.seqNum) +
              ", current state " + ServerProtocol.STATE_DESC[self.state])
        self.transport.write(ripPacket.__serialize__())

    def processDataPkt(self, pkt):
        self.clientSeqNum = pkt.SequenceNumber + 1
        ackPacket = PEEPPacket.makeAckPacket(self.raisedSeqNum(), self.clientSeqNum)
        print("Sending ACK packet with sequence number " + str(self.seqNum) + ",ack number " + str(self.clientSeqNum)+
            ", current state " + ServerProtocol.STATE_DESC[self.state])
        self.transport.write(ackPacket.__serialize__())
        self.higherProtocol().data_received(pkt.Data)