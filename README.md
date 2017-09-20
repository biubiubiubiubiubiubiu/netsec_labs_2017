# netsec_labs_2017
Lab works for network security 2017


## PETF

* Protocol Name
	* Playground Control Protocol(PCP)

### Ensuring data received
* ACK NACK Message: Detect incidential damage but not the intended change
	* ACK: e.g: I have received the packet
	* NACK: e.g: I have not received the packet
	* CRC: e.g: Packet is damaged
* Forward Error Connection 前向纠错

* sliding window for acknowledgement

 	e.g:   Sender: 1, 2, 3, 4, 5
 			Receiver: received 1, S can send 6
* Result: ACK / NONACK protocol

### Session Establishment
* Three-way handshake.
	* Client ---SYN---> Server
	* Server ---(SYN-ACK)---> Client
	* Client ---ACK---> Server
	* Include sequence number inside each packet. So sending back ACK with server's generated sequence number means two ends are in same session
	* Problem: 
		* Session Hijack
		* Session Flood 
	* 不加PKI


## Some Poll Results from Lecture:

* 1st Poll: ACK NACK message receiving mechanism,
* 2nd Poll: Session Establishment: Three-way Handshake
* 3rd Poll: No PKI: (https://zh.wikipedia.org/wiki/%E5%85%AC%E9%96%8B%E9%87%91%E9%91%B0%E5%9F%BA%E7%A4%8E%E5%BB%BA%E8%A8%AD)
* 4th Poll: A sliding window based packet receiving mechanism
	e.g.: Assume the window size is 5. Sender firstly sends 5 packets, and waiting for message from receiver. If the sender has received ACK for 1st packet, then the sender can send 6th packet and so on.

## Packet Definitions: SYN SYN-ACK ACK
* SYN:
	* IP 
	* PORT
	* SEQUENCE NUMBER
	* SESSION ID (if reconnecting)
* SYN - ACK
	* IP 
	* PORT
	* SEQUENCE NUMBER
	* EXPECTED SESSION ID (Changed if reconnected)
* ACK
	* SEQUENCE NUMBER
* DATA
	* CONTENT: Bytes
	* SEQUENCE NUMBER

