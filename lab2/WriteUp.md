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


* Data Transmission 
      The bytes from the client side will be processed in the PEEPTransport (PEEP transport is used to split data into chunks, and convert data type into the TYPE.DATA). After that, the converted data will be sent to the other side,which is the server side. At the same time, we also need to checksum, if it is correct, then we need to check sequence number. In other words, the sequence number in the server side should be previous client number plus the length of data minus one. After checking it correctly, then we can conitnue to transfer data to appliaation layer.   