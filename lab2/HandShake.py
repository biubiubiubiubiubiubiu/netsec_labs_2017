class HandShake(PacketType):
    DEFINITION_IDENTIFIER = "[PROTOCOL]-Handshake"

    DEFINITION_VERSION = "1.0"

    FIELDS = [

    ("Type", UINT8),

    ("SequenceNumber", UINT32({Optional: True})),

    ("Checksum", UINT16),

    ("Acknowledgement", UINT32({Optional: True})),

    ("HLEN", UINT8)
             ]