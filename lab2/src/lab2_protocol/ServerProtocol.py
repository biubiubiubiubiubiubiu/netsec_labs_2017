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
                        # self.seqNum += 1
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        synAckPacket = PEEPPacket.makeSynAckPacket(self.raisedSeqNum(), self.partnerSeqNum)
                        print("Sending SYN_ACK packet with sequence number " + str(self.seqNum) +
                              ", current state " + self.STATE_DESC[self.state])
                        self.transport.write(synAckPacket.__serialize__())

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_ACK,
                            self.STATE_SERVER_SYN,
                            self.partnerSeqNum):
                        if pkt.Acknowledgement - 1 == self.seqNum:
                            print("Received ACK packet with sequence number " +
                                  str(pkt.SequenceNumber))
                            self.partnerSeqNum = pkt.SequenceNumber + 1
                            self.state = self.STATE_SERVER_TRANSMISSION
                            higherTransport = PEEPTransport(self.transport, self)
                            self.higherProtocol().connection_made(higherTransport)
                        else:
                            print("Server: Wrong ACK packet: ACK number: {!r}, expected: {!r}".format(
                                pkt.Acknowledgement - 1, self.seqNum))

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_ACK,
                            self.STATE_SERVER_TRANSMISSION,
                            self.partnerSeqNum):
                        print("Received ACK packet with sequence number " +
                              str(pkt.SequenceNumber))
                        dataRemoveSeq = pkt.Acknowledgement - 1
                        if dataRemoveSeq in self.sentDataCache:
                            print("Server: Received ACK for dataSeq: {!r}, removing".format(dataRemoveSeq))
                            del self.sentDataCache[dataRemoveSeq]
                            if len(self.readyDataCache) > 0:
                                (sequenceNumber, dataPkt) = self.readyDataCache.pop(0)
                                print("Server: Sending next packet in readyDataCache...")
                                self.sentDataCache[sequenceNumber] = dataPkt
                                self.transport.write(dataPkt.__serialize__())
                        self.partnerSeqNum = pkt.SequenceNumber + 1


                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_DATA,
                            self.STATE_SERVER_TRANSMISSION):
                        print("Received DATA packet with sequence number " +
                              str(pkt.SequenceNumber))
                        if pkt.SequenceNumber - self.partnerSeqNum <= PEEPTransport.MAXBYTE:
                            # If it is, send an ack on this packet, update self.partnerSeqNum, push it up
                            self.processDataPkt(pkt)
                            if len(self.receivedDataCache) > 0:
                                # Sort the list, if there is a matching sequence number inside the list, push it up
                                self.receivedDataCache = sorted(self.receivedDataCache,
                                                                key=lambda pkt: pkt.SequenceNumber)
                                while (self.receivedDataCache[
                                           0].SequenceNumber - self.partnerSeqNum <= PEEPTransport.MAXBYTE):
                                    self.processDataPkt(self.receivedDataCache.pop(0))
                        elif pkt.SequenceNumber >= self.partnerSeqNum \
                                and pkt.SequenceNumber < self.partnerSeqNum + PEEPProtocol.RECIPIENT_WINDOW_SIZE * PEEPTransport.MAXBYTE:
                            # if the order of pkt is wrong, simply append it to cache
                            self.receivedDataCache.append(pkt)
                        else:
                            # wrong packet seqNum, discard
                            print("Received DATA packet with wrong sequence number " +
                                  str(pkt.SequenceNumber) + ", discard.")

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