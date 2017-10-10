from .PEEPPacket import PEEPPacket
from .PEEPTransports.PEEPTransport import PEEPTransport
from .PEEPProtocol import PEEPProtocol

class ServerProtocol(PEEPProtocol):
    def __init__(self):
        super().__init__()
        self.state = self.STATE_SERVER_SYN_ACK
        print("Initialized server with state " +
              self.STATE_DESC[self.state])

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PEEPPacket):
                if pkt.verifyChecksum():
                    if (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_SYN,
                            self.STATE_SERVER_SYN_ACK):
                        # the first way handshake, no need to check the sequence num
                        print("Received SYN packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.state = self.STATE_SERVER_SYN
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        synAckPacket = PEEPPacket.makeSynAckPacket(self.raisedSeqNum(), self.partnerSeqNum)
                        print("Sending SYN_ACK packet with sequence number " + str(self.seqNum) +
                              ", current state " + self.STATE_DESC[self.state])
                        self.transport.write(synAckPacket.__serialize__())

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_ACK,
                            self.STATE_SERVER_SYN):
                        # special ack for syn-ack
                        if pkt.Acknowledgement == self.seqNum + 1:
                            print("Received ACK packet with acknowledgement number " +
                                  str(pkt.Acknowledgement))
                            self.state = self.STATE_SERVER_TRANSMISSION
                            higherTransport = PEEPTransport(self.transport, self)
                            self.higherProtocol().connection_made(higherTransport)
                        else:
                            print("Server: Wrong ACK packet: ACK number: {!r}, expected: {!r}".format(
                                pkt.Acknowledgement, self.seqNum + 1))

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_ACK,
                            self.STATE_SERVER_TRANSMISSION):
                        self.processAckPkt(pkt)

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_DATA,
                            self.STATE_SERVER_TRANSMISSION):
                        self.processDataPkt(pkt)

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP,
                            self.STATE_SERVER_TRANSMISSION,
                            self.partnerSeqNum):
                        print("Received RIP packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        ripAckPacket = PEEPPacket.makeRipAckPacket(self.raisedSeqNum(), self.partnerSeqNum)
                        print("Sending RIP-ACK packet with sequence number " + str(self.seqNum) +
                              ", current state " + self.STATE_DESC[self.state])
                        self.transport.write(ripAckPacket.__serialize__())
                        # NOT IMPLEMENTED: send remaining packets in buffer
                        self.sendRip()


                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP_ACK,
                            self.STATE_SERVER_TRANSMISSION,
                            self.partnerSeqNum):
                        print("Received RIP-ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        print("Closing...")
                        self.stop()

                    else:
                        print("Server: Wrong packet: seq num {!r}, type {!r}， current state: {!r}".format(
                            pkt.SequenceNumber, pkt.Type, self.STATE_DESC[self.state]))
                else:
                    print("Wrong packet checksum: " + str(pkt.Checksum))
            else:
                print("Wrong packet class type: {!r}, state: {!r} ".format(str(type(pkt)),
                                                                           self.STATE_DESC[self.state]))