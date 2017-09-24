from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16, STRING, UINT8, UINT32
from playground.network.packet.fieldtypes.attributes import Optional

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
