# netsec_labs_2017
Lab works for network security 2017

## For Lab2: 
### Test Instructions

For **detailed WriteUp information**, please checkout the file WriteUp.md inside lab2_modular directory.

This is a modular version of our Lab2 protocol. The .playground folder includes our connector code and is pre-initialized with a network switch (switch1) at 20174.1.1.1 and a vnic (v_eth0).

The following commands are used to initialize the environment:

```
(cd lab2_modular)
pnetworking initialize instance
pnetworking enable switch1
pnetworking enable v_eth0
```

The submission includes an Echo client and server as example. Use

```
python3 submission.py server
```

to start the server and

```
python3 submission.py client 20174.1.1.1
```

to make a connection. Once connection_made is called, the client sends a "hello" message to server and receives the correspondent response. Several log messages will be printed at each step of connection.

This submission enables data chunks. If the data bytes is longer than 1024 (a constant in PEEPTransports/PEEPTransport.py that can be modified), it is splitted into several chunks and sent separately to the server. The server will combine them in a cache and pass the completed bytes to application once finished.

