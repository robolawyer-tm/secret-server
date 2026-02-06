import socket
import subprocess
import ipaddress

def get_hotspot_interface_ifconfig():
    """Find hotspot interface via ifconfig."""
    try:
        # Run ifconfig (available in Termux/busybox)
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            # Look for common hotspot interface keywords
            if any(kw in line.lower() for kw in ('wlan', 'ap', 'tether', 'hotspot', 'rndis')):
                parts = line.strip().split(':')
                if len(parts) > 0:
                    iface = parts[0].strip()
                    # Filter out unreasonable names
                    if iface and len(iface) < 20 and 'lo' not in iface:  
                        return iface
    except Exception as e:
        print(f"Warning: Error detecting hotspot interface: {e}")
    return None

def get_interface_ip(iface):
    """Get IP address for specific interface."""
    try:
        result = subprocess.run(['ifconfig', iface], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'inet ' in line:
                # Extract IP from 'inet addr:X.X.X.X' or 'inet X.X.X.X'
                parts = line.split('inet ')
                if len(parts) > 1:
                    ip_part = parts[1].strip().split()
                    if ip_part:
                        ip = ip_part[0].strip('addr:') 
                        if ip != '127.0.0.1':
                            return ip
    except Exception:
        pass
    return None

def get_ip_from_socket():
    """
    Get local IP via UDP socket (doesn't send data).
    Robust on Android even without shell command permissions.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        s.close()
        return IP
    except Exception:
        return None

def get_hotspot_info():
    """
    Get hotspot interface, IP, and calculated /24 subnet.
    Returns: (subnet_cidr_str, gateway_ip, interface_name)
    """
    # Strategy 1: 'ip addr' command (Modern Linux/Android)
    try:
        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
        # Simplified parsing: look for common hotspot interface names
        current_iface = None
        for line in result.stdout.splitlines():
            # roughly parse lines
            parts = line.strip().split()
            if not parts: continue
            
            # Line starting with number is interface
            if line[0].isdigit() and ':' in line:
                iface_name = parts[1].strip(':')
                if any(kw in iface_name.lower() for kw in ('wlan', 'ap', 'tether', 'rndis')):
                    current_iface = iface_name
                else:
                    current_iface = None
            
            # active interface block
            if current_iface and 'inet' in parts and '/' in line:
                # found an IP on a hotspot-like interface!
                # parts usually: inet 192.168.1.1/24 ...
                for p in parts:
                    if '/' in p and p[0].isdigit():
                        try:
                            network = ipaddress.ip_network(p, strict=False)
                            return str(network), str(network.network_address), current_iface
                        except ValueError:
                            pass
    except Exception:
        pass

    # Strategy 2: 'ifconfig' (Legacy/Termux)
    iface = get_hotspot_interface_ifconfig()
    if iface:
        ip = get_interface_ip(iface)
        if ip:
            try:
                network = ipaddress.ip_network(f"{ip}/24", strict=False)
                return str(network), ip, iface
            except ValueError:
                pass
    
    # Strategy 3: Socket Fallback (Best Guess)
    # If we can't find the interface, we get the local IP and assume IT is the hotspot 
    # (or we are connected TO a hotspot).
    # This is a bit looser but ensures we don't block valid traffic if commands fail.
    local_ip = get_ip_from_socket()
    if local_ip and not local_ip.startswith('127.'):
        try:
             network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
             return str(network), local_ip, "unknown"
        except ValueError:
             pass

    return None, None, None

def is_ip_in_hotspot_subnet(ip_addr):
    """
    Checks if a given IP address belongs to the current Hotspot Subnet.
    """
    subnet_cidr, _, _ = get_hotspot_info()
    if not subnet_cidr:
        return False
        
    try:
        network = ipaddress.ip_network(subnet_cidr)
        ip = ipaddress.ip_address(ip_addr)
        return ip in network
    except ValueError:
        return False

def get_connected_peers():
    """
    Reads the system ARP table and 'ip neighbor' to find IP addresses 
    of devices that are currently connected/reachable on the network.
    Supports both IPv4 and IPv6.
    """
    peers = set()
    
    # 1. Try /proc/net/arp (Legacy/Standard IPv4)
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
