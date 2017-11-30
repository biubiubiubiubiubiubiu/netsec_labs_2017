import playground
from .Protocols.ServerProtocol import ServerProtocol
from .Protocols.ClientProtocol import ClientProtocol
from .Protocols.ServerPLSProtocol import ServerPLSProtocol
from .Protocols.ClientPLSProtocol import ClientPLSProtocol
from playground.network.common import StackingProtocolFactory

clientStack = StackingProtocolFactory(ClientPLSProtocol, ClientProtocol)
serverStack = StackingProtocolFactory(ServerPLSProtocol, ServerProtocol)
myPlsConnector = playground.Connector(protocolStack=(clientStack, serverStack))
clientPlsConnector = playground.Connector(protocolStack=clientStack)
myPeepConnector = playground.Connector(protocolStack=(ClientProtocol, ServerProtocol))
clientPeepConnector = playground.Connector(protocolStack=StackingProtocolFactory(ClientProtocol))

playground.setConnector("lab3_protocol", myPlsConnector)
playground.setConnector("my_team_lab3_protocol", myPlsConnector)
playground.setConnector("lab3_client_protocol", clientPlsConnector)
playground.setConnector("lab2_protocol", myPeepConnector)
playground.setConnector("lab2_client_protocol", clientPeepConnector)