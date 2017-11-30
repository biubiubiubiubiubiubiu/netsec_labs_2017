import playground
from .Protocols.ServerProtocol import ServerProtocol
from .Protocols.ClientProtocol import ClientProtocol
from .Protocols.ServerPLSProtocol import ServerPLSProtocol
from .Protocols.ClientPLSProtocol import ClientPLSProtocol
from playground.network.common import StackingProtocolFactory

clientStack = StackingProtocolFactory(ClientProtocol, ClientPLSProtocol)
serverStack = StackingProtocolFactory(ServerProtocol, ServerPLSProtocol)
myPlsConnector = playground.Connector(protocolStack=(clientStack, serverStack))
clientPlsConnector = playground.Connector(protocolStack=clientStack)
serverPlsConnector = playground.Connector(protocolStack=serverStack)
myPeepConnector = playground.Connector(protocolStack=(ClientProtocol, ServerProtocol))
clientPeepConnector = playground.Connector(protocolStack=StackingProtocolFactory(ClientProtocol))
serverPeepConnector = playground.Connector(protocolStack=StackingProtocolFactory(ServerProtocol))

playground.setConnector("lab3_protocol", myPlsConnector)
playground.setConnector("my_team_lab3_protocol", myPlsConnector)
playground.setConnector("lab3_client_protocol", clientPlsConnector)
playground.setConnector("lab3_server_protocol", serverPlsConnector)
playground.setConnector("lab2_protocol", myPeepConnector)
playground.setConnector("lab2_client_protocol", clientPeepConnector)
playground.setConnector("ilab2_protocol", clientPeepConnector)
playground.setConnector("lab2_server_protocol", serverPeepConnector)