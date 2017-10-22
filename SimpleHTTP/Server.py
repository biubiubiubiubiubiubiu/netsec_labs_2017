import socket               # Import socket module
import sys

HOST = '127.0.0.1'
PORT = 8888
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object 
try:
	s.bind((HOST, PORT))
except socket.error as msg:
	print("didn't bind correctly. Erro : {}".format(str(msg[0])))
	sys.exit()

print("now bind correctly")
s.listen(10)
print("the server is listening")


def clientThread(conn):
	con.send("Hi, I am andy, give me some math problems to solve")

	while True:
		data = conn.recv(2048)
		reply = "Ok..." + data
		if not data:
			break
		conn.sendall(reply)
	conn.close()

while True:
	conn, addr = s.accept()
	print("Connected with {} : {}".format(str(addr[0]),str(addr[1])))
	start_new_thread(clientThread,(conn,))


s.close()



