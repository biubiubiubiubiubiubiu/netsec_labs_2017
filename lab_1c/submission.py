import asyncio, sys
import time
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import STRING, BUFFER
from playground.network.packet.fieldtypes import NamedPacketType, ComplexFieldType, PacketFields, Uint, StringFieldType, PacketFieldType, ListFieldType
#from HTMLParsePacket import HTMLParsePacket
from playground.asyncio_lib.testing import TestLoopEx
from playground.network.testing import MockTransportToStorageStream
from playground.network.testing import MockTransportToProtocol

class HTMLParsePacket(PacketType):
	DEFINITION_IDENTIFIER = "lab1b.Cuiqing_Li.MyPacket"
	DEFINITION_VERSION = "1.0"

	FIELDS = [
	("file_name",STRING),
	("num_file",Uint),
	("content",STRING),
	("data",BUFFER)
	]


class ServerProtocol(asyncio.Protocol):
	def __init__(self):
		self.transport = None
		self._deserializer = None

	def connection_made(self,transport):
		client_name = transport.get_extra_info('peername')
		self.transport = transport
		self._deserializer = PacketType.Deserializer()

	def data_received(self, data):
		#print("log first")
		self._deserializer.update(data)
		print("server side: data has been received!")
		for pat in self._deserializer.nextPackets():
			print(pat)

		print("send feed back to client to say: data has been processed")
		self.transport.write("Hi client: data has been processed, good to go!".encode())

	def connection_lost(self,exc):
		self.transport = None


class ClientProtocol(asyncio.Protocol):
	def __init__(self,packet):
		self.packet = packet
		# self.transport = loop


	def connection_made(self,transport):
		pybytes = self.packet.__serialize__()
		# print(type(pybytes))
		# print(pybytes)
		transport.write(pybytes)

	def data_received(self, data):
		print("Got feedback from server side: {} ".format(data.decode()))

	def connection_lost(self,exc):
		self.transport = None
		self.loop.stop()



packet1 = HTMLParsePacket()
packet1.file_name = "hello_guys.html"
packet1.num_file = 2
packet1.content = "Hello guys"
packet1.data = b"Let us Chat";


packet2 = HTMLParsePacket()
packet2.file_name = "hello_world.html"
packet2.num_file = 1;
packet2.content = "Hi, here is website about world"
packet2.data = b"Hi Here is website for you to know the world"


def Normal_Unit_Test():
	loop = asyncio.get_event_loop()
	if sys.argv[1]=='server':
		corotinue = loop.create_server(ServerProtocol,"127.0.0.1",8888)
		server = loop.run_until_complete(corotinue)
		print("I am current serving on : {}".format(server.sockets[0].getsockname()))
		try:
			loop.run_forever()
		except KeyboardInterrupt:
			pass
		server.close()
		loop.run_until_complete(server.wait_closed())
		loop.close()
	else:
		coro = loop.create_connection(lambda: ClientProtocol(packet2, loop),'127.0.0.1', 8888)
		loop.run_until_complete(coro)
		loop.run_forever()
		loop.close()


def BasicUnitTest():
	asyncio.set_event_loop(TestLoopEx())
	client = ClientProtocol(packet2)
	server = ServerProtocol()
	transportToServer = MockTransportToProtocol(server)
	transportToClient = MockTransportToProtocol(client)
	server.connection_made(transportToClient)
	client.connection_made(transportToServer)


BasicUnitTest()

# Normal_Unit_Test()



