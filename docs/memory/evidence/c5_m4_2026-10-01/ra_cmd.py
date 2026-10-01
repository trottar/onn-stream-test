#!/usr/bin/env python3
"""C5-M3 (as C5-M1's ra_cmd.py): one RetroArch network command to the local command port.
usage: ra_cmd.py <port> <COMMAND>"""
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(1.5)
s.sendto(sys.argv[2].encode(), ("localhost", int(sys.argv[1])))
try: print(s.recv(4096).decode().strip())
except socket.timeout: print("(no reply)")
