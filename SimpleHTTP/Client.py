import socket               # Import socket module
import sys

try:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
	print("Error to create socket")
	sys.exit()
print("socked has been created")

host = "127.0.0.1"
port = 8888

try:
	remote_ip = socket.gethostbyname(host)
except socket.gaierror:
	print("host name cannot be found")
	sys.exit()


s.connect((remote_ip, port))

print("socket connected to {} on ip : {}".format(str(host),str(remote_ip)))

message = "what is 1+1 = ?"

try: 
	s.sendall(message)
except socket.error:
	print("send failed")
	sys.exit()
reply = s.recv(4096)

print("reply")