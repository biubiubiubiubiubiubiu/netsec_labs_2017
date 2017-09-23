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