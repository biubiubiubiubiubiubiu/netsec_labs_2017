from HandShake import HandShake
from ClientProtocol import ClientProtocol
from ServerProtocol import ServerProtocol

from playground.network.packet import PacketType
from playground.asyncio_lib.testing import TestLoopEx
from playground.network.testing import MockTransportToStorageStream
from playground.network.testing import MockTransportToProtocol
import playground
import logging
import asyncio, sys, time

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

  
    if mode.lower() == "server":
        coro = playground.getConnector().create_playground_server(lambda: ServerProtocol(), 101)
        server = loop.run_until_complete(coro)
        print("Submission: Server started at {}".format(server.sockets[0].gethostname()))
        loop.run_forever()
        loop.close()
    elif mode.lower() == "client":
        print("Submission: Testing three-way handshake...")
        coro = playground.getConnector().create_playground_connection(lambda: ClientProtocol(), remoteAddress, 101)
        transport, protocol = loop.run_until_complete(coro)
        print("Customer Connected. Starting UI t:{}. p:{}".format(transport, protocol))