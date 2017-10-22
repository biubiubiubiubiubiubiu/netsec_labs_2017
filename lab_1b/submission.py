from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import STRING,BUFFER
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


def Unit_Test():
	packet1 = HTMLParsePacket()
	packet1.file_name = "hello_world.html"
	packet1.num_file = 1
	packet1.content = ""
	packet1.data = b"";


	packet2 = HTMLParsePacket()
	packet2.file_name = "hello_world.html"
	packet2.num_file = 1;
	packet2.content = "Hi here is website about world"
	packet2.data = b"Hi Here is website for you to know the world"

	packet3 = HTMLParsePacket()
	packet3.file_name = "hello_JHU.html"
	packet3.num_file = 2
	packet3.content = ""
	packet3.data = b""

	pktBytes = packet1.__serialize__() + packet2.__serialize__() + packet3.__serialize__()
	deserializer = PacketType.Deserializer()
	print("staring with {} bytes of data".format(len(pktBytes)))
	while len(pktBytes) > 0:
		chunk,pktBytes = pktBytes[:10] , pktBytes[10:]
		deserializer.update(chunk)
		print("another 10 bytes loaded into deserializer. left = {}".format(len(pktBytes)))

		for packet in deserializer.nextPackets():
			print("got a packet")

			if packet == packet1:
				print("this is packet 1")
			elif packet == packet2:
				print("this is packet 2")
			elif packet == packet3:
				print("this is packet 3")






Unit_Test()

