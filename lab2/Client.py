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
