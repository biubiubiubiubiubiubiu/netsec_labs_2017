import playground
from .Protocols.ServerProtocol import ServerProtocol
from .Protocols.ClientProtocol import ClientProtocol
from .Protocols.PLSProtocol import PLSProtocol
from playground.network.common import StackingProtocolFactory

clientStack = StackingProtocolFactory(PLSProtocol, ClientProtocol)
serverStack = StackingProtocolFactory(PLSProtocol, ServerProtocol)
myPeepConnector = playground.Connector(protocolStack=(clientStack, serverStack))
# myPeepConnector = playground.Connector(protocolStack=(ClientProtocol, ServerProtocol))
playground.setConnector("lab2_protocol", myPeepConnector)
playground.setConnector("my_team_lab2_protocol", myPeepConnector)
