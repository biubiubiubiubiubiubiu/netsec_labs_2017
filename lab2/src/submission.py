from ApplicationLayer import EchoClientProtocol, EchoServerProtocol, EchoControl
import playground
import logging
import asyncio, sys

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.NOTSET)  # this logs *everything*
    logging.getLogger().addHandler(logging.StreamHandler())  # logs to stderr
    testArgs = {}

    args = sys.argv[1:]
    i = 0
    for arg in args:
        if arg.startswith("-"):
            k, v = arg.split("=")
            testArgs[k] = v
        else:
            testArgs[i] = arg
            i += 1
    mode = ""
    remoteAddress = ""
    if len(testArgs) > 0:
        mode = testArgs[0]
    if len(testArgs) > 1:
        remoteAddress = testArgs[1]
    loop = asyncio.get_event_loop()
    # loop.set_debug(enabled=True)

    if mode.lower() == "server":
        coro = playground.getConnector('lab2_protocol').create_playground_server(lambda: EchoServerProtocol(loop), 101)
        server = loop.run_until_complete(coro)
        print("Submission: Server started at {}".format(server.sockets[0].gethostname()))
        loop.run_forever()
        loop.close()
    elif mode.lower() == "client":
        control = EchoControl(loop)
        coro = playground.getConnector('lab2_protocol').create_playground_connection(control.buildProtocol,
                                                                                     remoteAddress, 101)
        transport, protocol = loop.run_until_complete(coro)
        print("Submission: Client Connected. Starting UI t:{}. p:{}".format(transport, protocol))
        loop.run_forever()
        loop.close()
