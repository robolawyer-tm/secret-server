
import socket

def get_local_ip():
    try:
        # We don't need to actually connect, just tell the socket where we WANT to go
        # and it will tell us which interface/IP it would use.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return f"Error: {e}"

print(f"Detected IP: {get_local_ip()}")
