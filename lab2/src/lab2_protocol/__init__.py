from .ClientProtocol import ClientProtocol
from .ServerProtocol import ServerProtocol
import playground

lab2Connector = playground.Connector(protocolStack=(lambda: ClientProtocol(), lambda: ServerProtocol()))
playground.setConnector("lab2_protocol", lab2Connector)