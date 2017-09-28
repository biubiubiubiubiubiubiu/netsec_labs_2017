from HandShake import HandShake
from ClientProtocol import ClientProtocol
from ServerProtocol import ServerProtocol

from playground.network.packet import PacketType
from playground.asyncio_lib.testing import TestLoopEx
from playground.network.testing import MockTransportToStorageStream
from playground.network.testing import MockTransportToProtocol
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
from PassThroughLayer1 import PassThroughLayer1
from PassThroughLayer2 import PassThroughLayer2
import playground
import logging
import asyncio, sys, time

def serverCallback(this, message=None):
    # DEBUG: closing after handshake
    print("Server callback: Handshake successful. Shutting down connection from server side...")
    this.sendRip()

def clientCallback(this, message=None):
    print("Client callback: Handshake successful.")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.NOTSET) # this logs *everything*
    logging.getLogger().addHandler(logging.StreamHandler()) # logs to stderr
    testArgs = {}

    args= sys.argv[1:]
    i = 0
    for arg in args:
        if arg.startswith("-"):
            k,v = arg.split("=")
            testArgs[k]=v
        else:
            testArgs[i] = arg
            i+=1
    mode = ""
    if len(testArgs) > 0:
        mode = testArgs[0]
    if len(testArgs) > 1:
        remoteAddress = testArgs[1]
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    f = StackingProtocolFactory(lambda: ServerProtocol(), lambda: ClientProtocol())
    ptConnector = playground.Connector(protocolStack=f)
    playground.setConnector("passthrough", ptConnector)

    if mode.lower() == "server":
        coro = playground.getConnector('passthrough').create_playground_server(lambda: PassThroughLayer1(), 101)
        server = loop.run_until_complete(coro)
        print("Submission: Server started at {}".format(server.sockets[0].gethostname()))
        loop.run_forever()
        loop.close()
    elif mode.lower() == "client":
        print("Submission: Testing three-way handshake...")
        coro = playground.getConnector('passthrough').create_playground_connection(lambda: PassThroughLayer2(), remoteAddress, 101)
        transport, protocol = loop.run_until_complete(coro)
        print("Client Connected. Starting UI t:{}. p:{}".format(transport, protocol))
        loop.run_forever()
        loop.close()
