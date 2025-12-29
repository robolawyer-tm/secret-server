#!/usr/bin/env python3
"""
detect_hotspot.py

Standalone Android-safe hotspot network detector.
Works even when:
- ip / ip route are blocked
- /proc/net/* is blocked
- hostname -I is missing
- Termux has restricted permissions

Uses only Python sockets, which Android allows.
"""

import socket
import ipaddress

def detect_hotspot_network():
    # Create a UDP socket (no packets actually sent)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a non-local address; Android assigns LAN IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    # Android hotspot networks are always /24
    network = ipaddress.ip_network(ip + "/24", strict=False)
    return ip, network


if __name__ == "__main__":
    ip, net = detect_hotspot_network()
    print("Hotspot IP Address:", ip)
    print("Hotspot Network:", net)
    print("Network Range:", list(net.hosts())[0], "→", list(net.hosts())[-1])

