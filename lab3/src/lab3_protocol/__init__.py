import playground
from .Protocols.ServerProtocol import ServerProtocol
from .Protocols.ClientProtocol import ClientProtocol
from .Protocols.ServerPLSProtocol import ServerPLSProtocol
from .Protocols.ClientPLSProtocol import ClientPLSProtocol
from playground.network.common import StackingProtocolFactory

clientStack = StackingProtocolFactory(ClientPLSProtocol, ClientProtocol)
serverStack = StackingProtocolFactory(ServerPLSProtocol, ServerProtocol)
myPeepConnector = playground.Connector(protocolStack=(clientStack, serverStack))
# myPeepConnector = playground.Connector(protocolStack=(ClientProtocol, ServerProtocol))
playground.setConnector("lab3_protocol", myPeepConnector)
playground.setConnector("my_team_lab3_protocol", myPeepConnector)
