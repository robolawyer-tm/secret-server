import socket
import subprocess

def get_connected_peers():
    """
    Reads the system ARP table and 'ip neighbor' to find IP addresses 
    of devices that are currently connected/reachable on the network.
    Supports both IPv4 and IPv6.
    """
    peers = set()
    
    # 1. Try /proc/net/arp (Leagcy/Standard IPv4)
    try:
        with open('/proc/net/arp', 'r') as f:
            lines = f.readlines()
            # Skip header line
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 1:
                    ip = parts[0]
                    # basic validity check for IPv4
                    if ip.count('.') == 3:
                        peers.add(ip)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Warning: Could not read ARP table: {e}")

    # 2. Try 'ip neighbor' (IPv4 + IPv6, more robust)
    try:
        # Run ip neighbor command
        output = subprocess.check_output(['ip', 'neighbor'], text=True)
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 1:
                ip = parts[0]
                # Add to peers (accepts IPv4 and IPv6)
                peers.add(ip)
    except FileNotFoundError:
        # ip command might not be installed
        pass
    except Exception as e:
        print(f"Warning: Could not run ip neighbor: {e}")
        
    return peers

def get_local_ip():
    """
    Determines the local IP address of the device by attempting to check
    route to a public IP (does not actually connect).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 8.8.8.8 doesn't need to be reachable, just helps select the default interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_same_subnet(ip1, ip2, mask_octets=3):
    """
    Checks if two IPs are in the same subnet (defaulting to /24 - first 3 octets).
    """
    try:
        parts1 = ip1.split('.')
        parts2 = ip2.split('.')
        
        if len(parts1) != 4 or len(parts2) != 4:
            return False
            
        return parts1[:mask_octets] == parts2[:mask_octets]
    except Exception:
        return False

if __name__ == "__main__":
    print("--- Network Diagnostic Check ---")
    
    local_ip = get_local_ip()
    print(f"1. Detected Local IP: {local_ip}")
    
    peers = get_connected_peers()
    print(f"2. ARP/Neighbor Peers found: {list(peers)}")
    
    # Test Subnet logic
    test_ip = local_ip.rsplit('.', 1)[0] + '.123'
    result = is_same_subnet(local_ip, test_ip)
    print(f"3. Subnet Check Test: {local_ip} vs {test_ip} -> {'MATCH (Pass)' if result else 'FAIL'}")
    
    print("--------------------------------")
