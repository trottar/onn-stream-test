# feasibility probe (not item code): can another thread reset a TCP connection whose writer is blocked in sendall?
import ctypes, ipaddress, socket, struct, threading, time
LOOP = str(ipaddress.ip_address(0x7F000001))
libc = ctypes.CDLL(None, use_errno=True)
class SA(ctypes.Structure):
    _fields_ = [("sa_family", ctypes.c_ushort), ("sa_data", ctypes.c_char * 14)]
def run(mode):
    ls = socket.socket(); ls.bind((LOOP, 0)); ls.listen(1)
    c = socket.create_connection(ls.getsockname()); s, _ = ls.accept()
    res = {}
    def writer():
        try:
            while True: s.sendall(b"x" * 65536)
        except OSError as e: res["writer"] = type(e).__name__
    t = threading.Thread(target=writer); t.start(); time.sleep(0.3)   # blocked: the client reads nothing
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    if mode == "af_unspec":
        rc = libc.connect(s.fileno(), ctypes.byref(SA(socket.AF_UNSPEC)), ctypes.sizeof(SA)); res["rc"] = rc
    else:
        s.shutdown(socket.SHUT_RDWR)
    t.join(3); res["writer_unblocked"] = not t.is_alive()
    got = 0
    try:
        while True:
            d = c.recv(1 << 20)
            if not d: res["client"] = "EOF"; break
            got += len(d)
    except OSError as e: res["client"] = type(e).__name__
    res["client_bytes_before"] = got
    s.close(); c.close(); ls.close()
    return res
for m in ("af_unspec", "shutdown"): print(m, run(m))
