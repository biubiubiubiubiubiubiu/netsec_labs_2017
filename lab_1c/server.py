import asyncio
import time
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import STRING, BUFFER
from playground.network.packet.fieldtypes import NamedPacketType, ComplexFieldType, PacketFields, Uint,StringFieldType, PacketFieldType, ListFieldType
from HTMLParsePacket import HTMLParsePacket


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



loop = asyncio.get_event_loop()
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

