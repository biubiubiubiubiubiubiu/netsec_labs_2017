## Network Security Lab 3


### Instructions
lab3/src/ is our implementation of PLS protocol.

lab3/docs/prfc/lab3_proposed_prfc.xml is the xml file for prfc.

The submission includes an Echo client and server as example. Use

```
python3 submission.py server
```

to start the server and

```
python3 submission.py client [server's playground IP]
```

to make a connection. Once connection_made is called, the client sends a "hello" message to server and receives the correspondent response. Several log messages will be printed at each step of connection.

The keys needs to be set up for PLS protocol to correctly work.  

Here is the folder structure:
```
submission.py
keys/
    client/
        private.key
        cert.crt
    server/
        private.key
        cert.crt
    group.crt # Intermediate CA
    root.crt
```

Key creation:
```
# Generate private keys
openssl genpkey -algorithm RSA -out private.key -pkeyopt rsa_keygen_bits:2048

# Generate public keys (unused)
openssl rsa -pubout -in private.key -out public.pub

# Generate CSRs
openssl req -new -key private.key -out req.csr

# CA Sign CSRs
openssl x509 -CA ../group.crt -CAkey ../group.key -CAcreateserial -in req.csr -req -days 365 -out cert.crt
```

#### TODO LIST:
1. PRFC Document
