from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, UINT16, UINT8
from playground.network.packet.fieldtypes.attributes import Optional
import asyncio

class HandShake(PacketType):
    DEFINITION_IDENTIFIER = "[PROTOCOL]-Handshake"
    DEFINITION_VERSION = "1.0"

    FIELDS = [
        ("Type", UINT8),
        ("SequenceNumber", UINT32({Optional: True})),
        ("Checksum", UINT16),
        ("Acknowledgement", UINT32({Optional: True})),
        ("Data", STRING({Optional: True}))
    ]

class ClientProtocol(asyncio.Protocol):
    STATE_CLIENT_INITIAL_SYN = 0
    STATE_CLIENT_SYN_ACK = 1
    STATE_CLIENT_TRANSMISSION = 2

    def __init__(self):
        print("Hello client")
        self.state = ClientProtocol.STATE_CLIENT_INITIAL_SYN


class ServerProtocol(asyncio.Protocol):
    STATE_SERVER_SYN_ACK = 0
    STATE_SERVER_SYN = 1
    STATE_SERVER_TRANSMISSION = 2

    def __init__(self):
        print("Hello server")
        self.state = ServerProtocol.STATE_SERVER_SYN_ACK