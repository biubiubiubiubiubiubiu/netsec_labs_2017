import asyncio
import time
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import STRING, BUFFER
from playground.network.packet.fieldtypes import NamedPacketType, ComplexFieldType, PacketFields, Uint,StringFieldType, PacketFieldType, ListFieldType


class HTMLParsePacket(PacketType):
	DEFINITION_IDENTIFIER = "lab1b.Cuiqing_Li.MyPacket"
	DEFINITION_VERSION = "1.0"

	FIELDS = [
	("file_name",STRING),
	("num_file",Uint),
	("content",STRING),
	("data",BUFFER)
	]




