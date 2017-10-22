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
                        self.sendSynAck()
                        self.seqNum += 1
                        self.tasks.append(asyncio.ensure_future(
                            self.checkState([self.STATE_SERVER_TRANSMISSION, self.STATE_SERVER_CLOSED],
                                            self.sendSynAck)))

                    elif (pkt.Type, self.state) == (
                            PEEPPacket.TYPE_ACK,
                            self.STATE_SERVER_SYN):
                        # special ack for syn-ack
                        if pkt.Acknowledgement >= self.seqNum:
                            self.dbgPrint("Received ACK packet with acknowledgement number " +
                                          str(pkt.Acknowledgement))
                            self.state = self.STATE_SERVER_TRANSMISSION
                            higherTransport = PEEPTransport(self.transport, self)
                            self.higherProtocol().connection_made(higherTransport)
                            self.tasks.append(asyncio.ensure_future(self.scanCache()))
                        else:
                            self.dbgPrint("Server: Wrong ACK packet: ACK number: {!r}, expected: {!r}".format(
                                pkt.Acknowledgement, self.seqNum))

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
                        self.dbgPrint("Received RIP packet with sequence number " +
                                      str(pkt.SequenceNumber))
                        # TODO: what if RIP arrives before last DATA?
                        self.partnerSeqNum = pkt.SequenceNumber + 1
                        self.sendRipAck()
                        # send rip after no remaining packets in buffer
                        self.isClosing = True
                        self.tasks.append(asyncio.ensure_future(self.checkCacheIsEmpty(self.prepareForRip)))

                    elif (pkt.Type, self.state, pkt.Acknowledgement) == (
                            PEEPPacket.TYPE_RIP_ACK,
                            self.STATE_SERVER_TRANSMISSION,
                            self.seqNum + 1):
                        self.dbgPrint("Received RIP-ACK packet with ack number " +
                                      str(pkt.Acknowledgement))
                        self.state = self.STATE_SERVER_CLOSED
                        self.dbgPrint("Closing...")
                        self.stop()

                    else:
                        self.dbgPrint("Server: Wrong packet: seq num {!r}, type {!r}， current state: {!r}".format(
                            pkt.SequenceNumber, pkt.Type, self.STATE_DESC[self.state]))
                else:
                    self.dbgPrint("Wrong packet checksum: " + str(pkt.Checksum))
            else:
                self.dbgPrint("Wrong packet class type: {!r}, state: {!r} ".format(str(type(pkt)),
                                                                                   self.STATE_DESC[self.state]))

    def prepareForRip(self):
        self.dbgPrint("Server: preparing for RIP...")
        self.sendRip()
        self.tasks.append(asyncio.ensure_future(self.checkState([self.STATE_SERVER_CLOSED], self.sendRip)))

    def isClosed(self):
        return self.state == self.STATE_SERVER_CLOSED
