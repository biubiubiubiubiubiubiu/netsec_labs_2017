from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, UINT8, UINT32, BUFFER
from playground.network.packet.fieldtypes.attributes import Optional

class PEEPPacket(PacketType):
    TYPE_SYN = 0
    TYPE_SYN_ACK = 1
    TYPE_ACK = 2
    TYPE_RIP = 3
    TYPE_RIP_ACK = 4
    TYPE_RST = 5

    DEFINITION_IDENTIFIER = "[PROTOCOL]-Handshake"
    DEFINITION_VERSION = "1.0"

    FIELDS = [
        ("Type", UINT8),
        ("SequenceNumber", UINT32({Optional: True})),
        ("Checksum", UINT16({Optional: True})),
        ("Acknowledgement", UINT32({Optional: True})),
        ("Data", BUFFER({Optional: True}))
    ]
