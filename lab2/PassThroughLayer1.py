from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
import playground
from PEEPTransports.AppTransport import AppTransport

class PassThroughLayer1(StackingProtocol):
    
    def connection_made(self, transport):
        self.transport = transport
        print("PassThroughLayer1: connection_made called, sending higher transport to ClientDemo")
        higherTransport = AppTransport(self.transport)
        self.higherProtocol().connection_made(higherTransport)
    
    def data_received(self, data):
        print("PassThroughLayer1: data received from the other side.")
        self.higherProtocol().data_received(data)

    def connection_lost(self):
        print("PassThroughLayer1: connection lost")
        self.higherProtocol().connection_lost()