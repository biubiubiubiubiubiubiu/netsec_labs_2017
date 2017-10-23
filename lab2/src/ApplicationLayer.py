from playground.network.packet.fieldtypes import BOOL, STRING
from playground.network.common import PlaygroundAddress

# MessageDefinition is the base class of all automatically serializable messages
from playground.network.packet import PacketType
import playground

import sys, time, os, logging, asyncio


class EchoPacket(PacketType):
    """
    EchoProtocolPacket is a simple message for sending a bit of 
    data and getting the same data back as a response (echo). The
    "header" is simply a 1-byte boolean that indicates whether or
    not it is the original message or the echo.
    """

    # We can use **ANY** string for the identifier. A common convention is to
    # Do a fully qualified name of some set of messages.
    DEFINITION_IDENTIFIER = "test.EchoPacket"

    # Message version needs to be x.y where x is the "major" version
    # and y is the "minor" version. All Major versions should be
    # backwards compatible. Look at "ClientToClientMessage" for
    # an example of multiple versions
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("original", BOOL),
        ("message", STRING)
    ]


class EchoServerProtocol(asyncio.Protocol):
    """
    This is our class for the Server's protocol. It simply receives
    an EchoProtocolMessage and sends back a response
    """

    def __init__(self, loop=None):
        self.deserializer = EchoPacket.Deserializer()
        self.loop = loop
        self.transport = None

    def connection_made(self, transport):
        print("Received a connection from {}".format(transport.get_extra_info("peername")))
        self.transport = transport

    def connection_lost(self, reason=None):
        print("Lost connection to client. Cleaning up.")
        if self.loop:
            self.loop.stop()

    def data_received(self, data):
        self.deserializer.update(data)
        for echoPacket in self.deserializer.nextPackets():
            if echoPacket.original:
                print("Got {} from client.".format(echoPacket.message))

                if echoPacket.message == "__QUIT__":
                    print("Client instructed server to quit. Terminating")
                    self.transport.close()
                    return

                responsePacket = EchoPacket()
                responsePacket.original = False  # To prevent potentially infinte loops?
                responsePacket.message = echoPacket.message

                self.transport.write(responsePacket.__serialize__())

            else:
                print("Got a packet from client not marked as 'original'. Dropping")


class EchoClientProtocol(asyncio.Protocol):
    """
    This is our class for the Client's protocol. It provides an interface
    for sending a message. When it receives a response, it prints it out.
    """

    def __init__(self, loop=None, callback=None):
        self.buffer = ""
        self.loop = loop
        if callback:
            self.callback = callback
        else:
            self.callback = print
        self.transport = None
        self.deserializer = EchoPacket.Deserializer()

    def close(self):
        self.__sendMessageActual("__QUIT__")

    def connection_made(self, transport):
        print("Connected to {}".format(transport.get_extra_info("peername")))
        self.transport = transport
        self.send("Hello world!")

    def data_received(self, data):
        self.deserializer.update(data)
        for echoPacket in self.deserializer.nextPackets():
            if echoPacket.original == False:
                self.callback(echoPacket.message)
            else:
                print("Got a message from server marked as original. Dropping.")

    def connection_lost(self, reason=None):
        print("Lost connection to server. Cleaning up.")
        if self.loop:
            self.loop.stop()

    def send(self, data):
        print("EchoClientProtocol: Sending echo message...")
        echoPacket = EchoPacket(original=True, message=data)

        self.transport.write(echoPacket.__serialize__())


class EchoControl:
    def __init__(self, loop=None):
        self.txProtocol = None
        self.loop = loop

    def buildProtocol(self):
        self.txProtocol = EchoClientProtocol(self.loop, self.callback)
        return self.txProtocol

    def connect(self, txProtocol):
        self.txProtocol = txProtocol
        print("Echo Connection to Server Established!")
        # self.txProtocol = txProtocol
        # sys.stdout.write("Enter Message: ")
        # sys.stdout.flush()
        # asyncio.get_event_loop().add_reader(sys.stdin, self.stdinAlert)

    def callback(self, message):
        print("Server Response: {}".format(message))
        # self.txProtocol.send("__QUIT__")
        print("Closing EchoProtocol...")
        self.txProtocol.transport.close()

    def stdinAlert(self):
        data = sys.stdin.readline()
        if data and data[-1] == "\n":
            data = data[:-1]  # strip off \n
        self.txProtocol.send(data)
