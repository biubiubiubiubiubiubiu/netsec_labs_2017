import asyncio, sys
import time
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import STRING, BUFFER
from playground.network.packet.fieldtypes import NamedPacketType, ComplexFieldType, PacketFields, Uint, StringFieldType, PacketFieldType, ListFieldType
#from HTMLParsePacket import HTMLParsePacket
from playground.asyncio_lib.testing import TestLoopEx
from playground.network.testing import MockTransportToStorageStream
from playground.network.testing import MockTransportToProtocol
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
import playground
import logging
from HandShake import HandShake

class HTMLParsePacket(PacketType):
	DEFINITION_IDENTIFIER = "lab1b.Cuiqing_Li.MyPacket"
	DEFINITION_VERSION = "1.0"

	FIELDS = [
	   ("file_name",STRING),
	   ("num_file",Uint),
	   ("content",STRING),
	   ("data",BUFFER)
	]

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


class ServerProtocol(asyncio.Protocol):
	def __init__(self):
		self.transport = None
		self._deserializer = None

	def connection_made(self,transport):
		#logging.debug("hello server is here")
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
	def __init__(self,packet,loop):
		self.packet = packet
		self.transport = None 


	def connection_made(self,transport):
		#logging.debug("hello client is here")
		pybytes = self.packet.__serialize__()
		# print(type(pybytes))
		# print(pybytes)
		transport.write(pybytes)

	def data_received(self, data):
		#logging.debug("hello data is sent")
		print("Got feedback from server side: {} ".format(data.decode()))

	def connection_lost(self,exc):
		self.transport = None
		self.loop.stop()



class passThrough1(StackingProtocol):
	def __init__(self):
		super(passThrough1,self).__init__()
		self.transport = None

	def connection_made(self,transport):
		self.transport = transport
		highertransport = StackingTransport(self.transport)
		self.higherProtocol().connection_made(highertransport)

	def data_received(self,data):
		self.higherProtocol().data_received(data)

	def connection_lost(self,exc):
		pass
		self.highertrasnport = None



class passThrough2(StackingProtocol):
	def __init__(self):
		self.transport = None
		#self.highertrasnport = None

	def connection_made(self,transport):
		self.transport = transport
		highertransport = StackingTransport(self.transport)
		self.higherProtocol().connection_made(highertransport)

	def data_received(self,data):
		self.higherProtocol().data_received(data)
	
	def connection_lost(self,exc):
		pass
		# self.highertrasnport = None



name = sys.argv[1]
loop = asyncio.get_event_loop()
loop.set_debug(enabled = True)
f = StackingProtocolFactory(lambda:passThrough1(),lambda:passThrough2())
ptConnector = playground.Connector(protocolStack=f)
playground.setConnector("passthrough",ptConnector)

if name == "server":
	coro = playground.getConnector('passthrough').create_playground_server(lambda: ServerProtocol(), 8888)
	server = loop.run_until_complete(coro)
	print("Echo Server Started at {}".format(server.sockets[0].gethostname()))
	loop.run_forever()
	loop.close()
else:
	coro = playground.getConnector('passthrough').create_playground_connection(lambda: ClientProtocol(packet2, loop),"20174.1.1.1",8888)
	transport, protocol = loop.run_until_complete(coro)
	print("Echo Client Connected. Starting UI t:{}. p:{}".format(transport, protocol))
	loop.run_forever()
	loop.close()