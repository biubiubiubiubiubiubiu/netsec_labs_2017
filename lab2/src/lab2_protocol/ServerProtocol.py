from .PEEPPacket import PEEPPacket
from .PEEPTransports.PEEPTransport import PEEPTransport
from .PEEPProtocol import PEEPProtocol
from threading import Timer
import asyncio


class ServerProtocol(PEEPProtocol):
    def __init__(self):
        super().__init__()
        self.state = self.STATE_SERVER_SYN_ACK
        self.dbgPrint("Initialized server with state " +
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
                        self.dbgPrint("Received SYN packet with sequence number " +
                                      str(pkt.SequenceNumber))
                        self.state = self.STATE_SERVER_SYN
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        synAck_seq = self.seqNum
                        self.sendSynAck(synAck_seq)
                        self.seqNum += 1
                        self.tasks.append(asyncio.ensure_future(
                            self.checkState(
                                [self.STATE_SERVER_TRANSMISSION, self.STATE_SERVER_CLOSING, self.STATE_SERVER_CLOSED],
                                lambda: self.sendSynAck(synAck_seq))))

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_ACK,
                            self.STATE_SERVER_SYN):
                        # special ack for syn-ack
                        if pkt.Acknowledgement == self.seqNum:
                            self.dbgPrint("Received ACK packet with acknowledgement number " +
                                          str(pkt.Acknowledgement))
                            self.state = self.STATE_SERVER_TRANSMISSION
                            higherTransport = PEEPTransport(self.transport, self)
                            self.higherProtocol().connection_made(higherTransport)
                            self.tasks.append(asyncio.ensure_future(self.scanCache()))
                        else:
                            self.dbgPrint("Server: Wrong ACK packet: ACK number: {!r}, expected: {!r}".format(
                                pkt.Acknowledgement, self.seqNum))


                    elif pkt.Type == PEEPPacket.TYPE_ACK:
                        if self.state in (self.STATE_SERVER_TRANSMISSION, self.STATE_SERVER_CLOSING):
                            self.processAckPkt(pkt)

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_DATA,
                            self.STATE_SERVER_TRANSMISSION):
                        self.processDataPkt(pkt)

                    elif (pkt.Type, pkt.SequenceNumber) == (
                            PEEPPacket.TYPE_RIP,
                            self.partnerSeqNum):
                        self.dbgPrint("Received RIP packet with sequence number " +
                                      str(pkt.SequenceNumber))
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        # send rip ack and stop immediately
                        self.ripAckAndStop()

                    elif (pkt.Type, self.state, pkt.Acknowledgement) == (
                            PEEPPacket.TYPE_RIP_ACK,
                            self.STATE_SERVER_CLOSING,
                            self.seqNum + 1):
                        self.dbgPrint("Received RIP-ACK packet with ack number " +
                                      str(pkt.Acknowledgement))
                        self.state = self.STATE_SERVER_CLOSED
                        self.dbgPrint("Closing...")
                        self.stop()

                    else:
                        self.dbgPrint("Server: Wrong packet: seq num {!r}, type {!r}， current state: {!r}".format(
                            pkt.SequenceNumber, PEEPPacket.TYPE_DESC[pkt.Type], self.STATE_DESC[self.state]))
                else:
                    self.dbgPrint("Wrong packet checksum: " + str(pkt.Checksum))
            else:
                self.dbgPrint("Wrong packet class type: {!r}, state: {!r} ".format(str(type(pkt)),
                                                                                   self.STATE_DESC[self.state]))

    def prepareForRip(self):
        self.dbgPrint("Preparing for RIP...")
        if self.state != self.STATE_SERVER_CLOSED:
            self.state = self.STATE_SERVER_CLOSING
            self.sendRip()
            self.tasks.append(
                asyncio.ensure_future(self.checkState([self.STATE_SERVER_CLOSED], self.sendRip, self.MAX_RIP_RETRIES)))

    def ripAckAndStop(self):
        self.sendRipAck()
        self.dbgPrint("Closing...")
        self.state = self.STATE_SERVER_CLOSED
        self.stop()

    def isClosing(self):
        return self.state == self.STATE_SERVER_CLOSING or self.state == self.STATE_SERVER_CLOSED
