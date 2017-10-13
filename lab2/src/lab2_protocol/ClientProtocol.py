from .PEEPPacket import PEEPPacket
from .PEEPTransports.PEEPTransport import PEEPTransport
from .PEEPProtocol import PEEPProtocol
from threading import Timer


class ClientProtocol(PEEPProtocol):
    def __init__(self):
        super().__init__()
        self.state = self.STATE_CLIENT_INITIAL_SYN
        self.dbgPrint("Initialized client with state " +
                      self.STATE_DESC[self.state])

    def connection_made(self, transport):
        super().connection_made(transport)
        if self.state == self.STATE_CLIENT_INITIAL_SYN:
            self.sendSyn()
            self.state = self.STATE_CLIENT_SYN_ACK
            Timer(self.TIMEOUT, self.checkState,
                  [[self.STATE_CLIENT_TRANSMISSION, self.STATE_CLIENT_CLOSED], self.sendSyn]).start()

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PEEPPacket):
                if pkt.verifyChecksum():
                    if pkt.Type == PEEPPacket.TYPE_SYN_ACK:
                        if self.state == self.STATE_CLIENT_SYN_ACK:
                            # check ack num
                            if (pkt.Acknowledgement >= self.seqNum + 1):
                                self.dbgPrint("Received SYN-ACK packet with sequence number " +
                                              str(pkt.SequenceNumber) + ", ack number " +
                                              str(pkt.Acknowledgement))
                                self.state = self.STATE_CLIENT_TRANSMISSION
                                self.partnerSeqNum = pkt.SequenceNumber + 1
                                self.sendAck()
                                self.seqNum += 1
                                higherTransport = PEEPTransport(self.transport, self)
                                self.higherProtocol().connection_made(higherTransport)
                                Timer(self.SCAN_INTERVAL, self.scanCache).start()
                            else:
                                self.dbgPrint("Client: Wrong SYN_ACK packet: ACK number: {!r}, expected: {!r}".format(
                                    pkt.Acknowledgement, self.seqNum + 1))
                        else:
                            # duplicate, send ack anyway
                            self.sendAck()

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_ACK,
                            self.STATE_CLIENT_TRANSMISSION):
                        self.processAckPkt(pkt)

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_DATA,
                            self.STATE_CLIENT_TRANSMISSION):
                        self.processDataPkt(pkt)

                    elif (pkt.Type, self.state, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP,
                            self.STATE_CLIENT_TRANSMISSION,
                            self.partnerSeqNum):
                        self.dbgPrint("Received RIP packet with sequence number " +
                                      str(pkt.SequenceNumber))
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        # send rip ack and stop after cache is empty
                        Timer(self.SCAN_INTERVAL, self.checkCacheIsEmpty, [self.ripAckAndStop]).start()

                    elif (pkt.Type, self.state, pkt.Acknowledgement) == (
                            PEEPPacket.TYPE_RIP_ACK,
                            self.STATE_CLIENT_TRANSMISSION,
                            self.seqNum + 1):
                        self.dbgPrint("Received RIP-ACK packet with ack number " +
                                      str(pkt.Acknowledgement))
                        # TODO what to o after client receiving RIP-ACK?
                        # self.state = self.STATE_CLIENT_CLOSED
                    else:
                        self.dbgPrint("Client: Wrong packet: seq num {!r}, type {!r}， current state: {!r}".format(
                            pkt.SequenceNumber, pkt.Type, self.STATE_DESC[self.state]))
                else:
                    self.dbgPrint("Wrong packet checksum: " + str(pkt.Checksum))
            else:
                self.dbgPrint("Wrong packet class type: {!r}, state: {!r} ".format(str(type(pkt)),
                                                                                   self.STATE_DESC[self.state]))

    def prepareForRip(self):
        self.sendRip()
        Timer(self.TIMEOUT, self.checkState, [[self.STATE_CLIENT_CLOSED], self.sendRip]).start()

    def ripAckAndStop(self):
        self.sendRipAck()
        self.dbgPrint("Closing...")
        self.state = self.STATE_CLIENT_CLOSED
        # TODO: how to call transport.close() in a timer?
        # self.stop()

    def isClosed(self):
        return self.state == self.STATE_CLIENT_CLOSED
