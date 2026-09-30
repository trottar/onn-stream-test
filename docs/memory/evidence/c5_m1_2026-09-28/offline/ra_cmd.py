import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(1.5)
s.sendto(sys.argv[2].encode(), ("<ipv4>", int(sys.argv[1])))
try: print(s.recv(4096).decode().strip())
except socket.timeout: print("(no reply)")
