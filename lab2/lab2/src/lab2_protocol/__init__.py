from .ClientProtocol import ClientProtocol
from .ServerProtocol import ServerProtocol
import playground

myPeepConnector = playground.Connector(protocolStack=(ClientProtocol, ServerProtocol))
playground.setConnector("lab2_protocol", myPeepConnector)
playground.setConnector("my_team_lab2_protocol", myPeepConnector)
