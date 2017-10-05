## Network Security Lab2

* Purpose/Technical backgrounds:

    Everything we did was based on lab1

    * Handshake was implemented in three ways

    * Realized data transmission between the client and server

    * Check errors in the process of transmitting data

    * Implemented TCP Four Wave to shut down both the client and server

* Session Establishment:

    In the process of Handshake, we defined three packet types that are seperately TYPE_SYN, TYPE_SYN_ACK and TYPE_ACK to mark the type of packets that were being sent. Also, "INITIAL_SYN", "SYN_ACK" and "TRANSMISSION" were defined to note the state of the client and the server. 
    
    * SYN:

      As the picture below shows, in the begenning, the state of both Client and Server is "INITIAL_SYN". At first, Client sends a TYPE_SYN packet with a sequence number (seq=x) to the Server and its state changes to "TYPE_SYN_ACK" wating for a feedback of Client. 

    * SYN_ACK:

      When Server receives the TYPE_SYN packet, it sends back a TYPE_SYN-ACK packet with a new serquence number(seq=y) and an acknowledgement(ack=x+1). At the same time, the sate of Server changes from "INITIAL_SYN" to "SYN_ACK". 

      
    * ACK:

      Then Client recieives the TYPE_SYN_ACK packet from Server and resend a new acknowledgement(ack=y+1) and a sequence number(seq=x+1). The state of Client changes to "SYN_ACK" that means ready for data transmission. 
      
      At this time, when Server receives the TYPE_ACK packet form Client, it changes the state to "SYN_ACK". So the session is successfully established and data is able to be transmitted. 


      ![png](/images/Tcp-handshake.png)


* Data Transmission:

     * Application Layer Start Transmitting:

       When Application layer transmits serialized data to lower PEEP layer, we defined PEEPTransport to split the data into several chunks if the length of data is larger than the max size. 
     
    * Transmitting between PEEPs:
     
      Then packet the chunks into PEEP packet with sequence number and send them to the receiver's PEEP layer in order. Then do the checksum to guarantee the integrity of the packet. After checksum, compare the sequence number of received packets with previously stored ones. If they are the same, the receiver's PEEP layer updates the previously stored sequence number and compare the updated one with the next coming sequence number  of the packet from the sender. If the packets are not sent in order, the receiver's PEEP layer defines a structure to store the packets sent in a wrong order and later check them.  
      
    
     