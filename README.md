## Network Security Lab 2


### Instructions
lab2/src/ is a modular version of our Lab2 protocol.

The submission includes an Echo client and server as example. Use

```
python3 submission.py server
```

to start the server and

```
python3 submission.py client [server's playground IP]
```

to make a connection. Once connection_made is called, the client sends a "hello" message to server and receives the correspondent response. Several log messages will be printed at each step of connection.

This submission enables data chunks. If the data bytes is longer than 1024 (a constant in PEEPTransports/PEEPTransport.py that can be modified), it is splitted into several chunks and sent separately to the server. The server will combine them in a cache and pass the completed bytes to application once finished.

#### TODO LIST:
1. Error correction when the packet sent is lost or damaged; implement packet cache and timeout for sender to resend failed packets

2. Two issues to be settled in future:
    * Loss of packets  
        * Choices
            * set up a time-out at data sender's end when it has sent out the last packet. If not received ACK for packet with certain sequence number in some time, it will resend again. I think there should be a limit on retry time.
        * set up time-out for every packet. This can be settled by using tuples.
    * Duplication of packets: only receive first correct packet
        * Send back an ACK to guarantee that this packet has been removed from cache


### Protocol Definitions
* PEEPPacket PacketType Definitions
```Python
class PEEPPacket(PacketType):
    DEFINITION_IDENTIFIER = "PEEP.Packet"

    DEFINITION_VERSION = "1.0"

    FIELDS = [

    ("Type", UINT8),

    ("SequenceNumber", UINT32({Optional: True})),

    ("Checksum", UINT16),

    ("Acknowledgement", UINT32({Optional: True})),

    ("Data", BUFFER({Optional: True})
    
    ]
```

* Status --> Type list
    * SYN -      TYPE 0 
    * SYN-ACK -  TYPE 1
    * ACK -      TYPE 2
    * RIP -      TYPE 3 (:P RIP connection )
    * RIP-ACK -  TYPE 4
    * RST -      TYPE 5

### State Machine List

#### Client Machine
Initial SYN State (state 0)
- prepare checksum for header fields
- Client sends SYN packet (Type=0) to server, transitions to state 1 where it waits for SYN-ACK (Type=1) packet
 
SYN-ACK State (state 1)
- Wait for SYN-ACK packet
-  If not received after a timeout, terminate program
- when received, compute checksum for header fields, if correct then Client sends ACK packet (Type=2) to server, transition to Transmission state (state 2)
- If checksum is not correct, terminate program. (For data packets when handshake is complete we could just send an ACK for the last properly received packet to signal retransmit)
 
Transmission State (state 2)
- Client can now send Data packets (haven't defined yet)
 
Server Protocol
SYN-ACK State (State 0)
- server awaits SYN packet from client and when it receives it, it computes checksum and if correct, transmits SYN-ACK (Type=1) packet, transition to SYN State (state 1)
- if checksum is bad or not received packet then terminate handshake with RST packet and clear buffer.
 
SYN State (state 1)
- server awaits client's ACK (Type = 2) packet, when received and on correct checksum calculation transition to Transmission State (state 2)
- If not received or checksum is bad, terminate handshake with RST packet and clear buffer.
 
Transmission State (State 2)
- Server can now send data packets to client.

#### Checking with seqNum:
- when the type is TYPE_DATA, then we need to check the difference between it's sequence number and stored sequence number (clientSeqNum or serverSeqNum) is the size of data bytes minus 1.
- When the packet is not the initial one, we need to check whether it's sequence number matches with stored sequence number.
