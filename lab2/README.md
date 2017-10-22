## Network Security Lab 2

### Protocol Definitions
* HandShake PacketType Definitions

```Python
class HandShake(PacketType):
    DEFINITION_IDENTIFIER = "[PROTOCOL]-Handshake"

    DEFINITION_VERSION = "1.0"

    FIELDS = [

    ("Type", UINT8),

    ("SequenceNumber", UINT32({Optional: True})),

    ("Checksum", UINT16),

    ("Acknowledgement", UINT32({Optional: True})),

    ("HLEN", UINT8)
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