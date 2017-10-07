from .PEEPPacket import PEEPPacket
from .PEEPTransports.PEEPTransport import PEEPTransport
from .PEEPProtocol import PEEPProtocol

class ClientProtocol(PEEPProtocol):
    def __init__(self):
        super().__init__()
        self.state = self.STATE_CLIENT_INITIAL_SYN
        print("Initialized client with state " +
              self.STATE_DESC[self.state])

    def connection_made(self, transport):
        super().connection_made(transport)
        if self.state == self.STATE_CLIENT_INITIAL_SYN:
            synPacket = PEEPPacket.makeSynPacket(self.seqNum)
            print("Sending SYN packet with sequence number " + str(self.seqNum) +
                  ", current state " + self.STATE_DESC[self.state])
            print("Packet checksum: " + str(synPacket.Checksum))
            self.transport.write(synPacket.__serialize__())
            self.state = self.STATE_CLIENT_SYN_ACK

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PEEPPacket):
                if pkt.verifyChecksum():
                    if (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_SYN_ACK,
                            self.STATE_CLIENT_SYN_ACK):
                        # check ack num
                        if (pkt.Acknowledgement - 1 == self.seqNum):
                            print("Received SYN-ACK packet with sequence number " +
                                  str(pkt.SequenceNumber))
                            self.state = self.STATE_CLIENT_TRANSMISSION
                            self.partnerSeqNum = pkt.SequenceNumber + 1
                            ackPacket = PEEPPacket.makeAckPacket(self.raisedSeqNum(), self.partnerSeqNum)
                            print("Sending ACK packet with sequence number " + str(self.seqNum) +
                                  ", current state " + self.STATE_DESC[self.state])
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
                            self.STATE_CLIENT_TRANSMISSION,
                            self.partnerSeqNum):
                        print("Received ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        dataRemoveSeq = pkt.Acknowledgement - 1
                        if dataRemoveSeq in self.sentDataCache:
                            print("Client: Received ACK for dataSeq: {!r}, removing".format(dataRemoveSeq))
                            del self.sentDataCache[dataRemoveSeq]
                        self.partnerSeqNum = pkt.SequenceNumber + 1

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_DATA,
                            self.STATE_CLIENT_TRANSMISSION):
                        print("Received DATA packet with sequence number " +
                              str(pkt.SequenceNumber))
                        if pkt.SequenceNumber - self.partnerSeqNum <= PEEPTransport.MAXBYTE:
                            # If it is, send an ack on this packet, update self.partnerSeqNum, push it up
                            self.processDataPkt(pkt)
                            if len(self.receivedDataCache) > 0:
                                # Sort the list, if there is a matching sequence number inside the list, push it up
                                self.receivedDataCache = sorted(self.receivedDataCache, key=lambda pkt: pkt.SequenceNumber)
                                while (self.receivedDataCache[0].SequenceNumber - self.partnerSeqNum <= PEEPTransport.MAXBYTE):
                                    self.processDataPkt(self.receivedDataCache.pop(0))
                        elif pkt.SequenceNumber >= self.partnerSeqNum \
                             and pkt.SequenceNumber < self.partnerSeqNum + PEEPProtocol.RECIPIENT_WINDOW_SIZE * PEEPProtocol.MAXBYTE:
                            # if the order of pkt is wrong, simply append it to cache
                            self.receivedDataCache.append(pkt)
                        else:
                            # wrong packet seqNum, discard
                            print("Received DATA packet with wrong sequence number " +
                                  str(pkt.SequenceNumber) + ", discard.")

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP,
                            self.STATE_CLIENT_TRANSMISSION,
                            self.partnerSeqNum):
                        print("Received RIP packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        ripAckPacket = PEEPPacket.makeRipAckPacket(self.raisedSeqNum(), self.partnerSeqNum)
                        print("Sending RIP-ACK packet with sequence number " + str(self.seqNum) +
                            ", current state " + self.STATE_DESC[self.state])
                        self.transport.write(ripAckPacket.__serialize__())
                        print("Closing...")
                        self.stop()
                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP_ACK,
                            self.STATE_CLIENT_TRANSMISSION,
                            self.partnerSeqNum):
                        print("Received RIP-ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                    else:
                        print("Client: Wrong packet: seq num {!r}, type {!r}， current state: {!r}".format(
                            pkt.SequenceNumber, pkt.Type, self.STATE_DESC[self.state]))
                else:
                    print("Wrong packet checksum: " + str(pkt.Checksum))
            else:
                print("Wrong packet class type: {!r}, state: {!r} ".format(str(type(pkt)),
                                                                           self.STATE_DESC[self.state]))
