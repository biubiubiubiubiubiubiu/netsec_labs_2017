import asyncio
import time
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import STRING, BUFFER
from playground.network.packet.fieldtypes import NamedPacketType, ComplexFieldType, PacketFields, Uint,StringFieldType, PacketFieldType, ListFieldType
from HTMLParsePacket import HTMLParsePacket



class ClientProtocol(asyncio.Protocol):
	def __init__(self,packet,loop):
		self.packet = packet
		self.loop = loop


	def connection_made(self,transport):
		pybytes = self.packet.__serialize__()
		#print(type(pybytes))
		#print(pybytes)
		transport.write(pybytes)


	def data_received(self, data):
		print("Got feedback from server side: {} ".format(data.decode()))

	def connection_lost(self,exc):
		self.transport = None
		self.loop.stop()


loop = asyncio.get_event_loop()
packet2 = HTMLParsePacket()
packet2.file_name = "hello_world.html"
packet2.num_file = 1;
packet2.content = "Hi here is website about world"
packet2.data = b"Hi Here is website for you to know the world"

coro = loop.create_connection(lambda: ClientProtocol(packet2, loop),
                              '127.0.0.1', 8888)
loop.run_until_complete(coro)
loop.run_forever()
loop.close()

