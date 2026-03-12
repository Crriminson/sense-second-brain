"""
Network utilities — IP detection and QR code generation.
"""

import socket
import subprocess
import platform
import qrcode


def get_local_ip() -> str:
    """
    Find the real WiFi IP address. Skips hotspot/virtual adapters.
    
    Strategy:
      1. UDP socket trick via 8.8.8.8 (picks internet-facing adapter)
      2. If that returns a hotspot IP (192.168.137.x), scan all adapters
      3. Last resort: 127.0.0.1
    """
    # Strategy 1: UDP socket trick — most reliable
    ip = _udp_probe()
    
    # Check if it's a hotspot/virtual IP
    if ip and not _is_virtual_ip(ip):
        return ip
    
    # Strategy 2: Parse all adapters, find the real WiFi one
    print(f"[NET] UDP probe returned virtual IP ({ip}), scanning adapters...")
    real_ip = _scan_adapters()
    if real_ip:
        return real_ip
    
    # Strategy 3: Fallback
    if ip and ip != "127.0.0.1":
        print(f"[NET] Using {ip} (might be hotspot)")
        return ip
    
    return "127.0.0.1"


def _udp_probe() -> str | None:
    """Classic UDP trick — connect to external IP to find local adapter."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def _is_virtual_ip(ip: str) -> bool:
    """Check if IP belongs to a virtual/hotspot adapter."""
    virtual_prefixes = (
        "192.168.137.",   # Windows Mobile Hotspot / ICS
        "192.168.56.",    # VirtualBox Host-Only
        "192.168.59.",    # VirtualBox
        "172.17.",        # Docker default bridge
        "172.18.",        # Docker
        "10.0.2.",        # VirtualBox NAT
        "169.254.",       # APIPA (no DHCP)
        "127.",           # Loopback
    )
    return ip.startswith(virtual_prefixes)


def _scan_adapters() -> str | None:
    """
    Parse network adapters to find real WiFi/Ethernet IP.
    Windows: ipconfig
    Linux/Mac: hostname -I or ip addr
    """
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            lines = result.stdout.split("\n")
            current_adapter = ""
            candidates = []
            
            for line in lines:
                stripped = line.strip()
                
                # Track which adapter section we're in
                if not stripped.startswith("IPv4") and "adapter" in line.lower():
                    current_adapter = line.strip().rstrip(":")
                
                # Extract IPv4 addresses
                if "IPv4 Address" in line or "IPv4" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        ip = parts[-1].strip()
                        
                        # Skip virtual adapters by name
                        skip_names = [
                            "hotspot", "virtual", "vethernet", "vmware",
                            "virtualbox", "docker", "loopback", "bluetooth",
                            "hyper-v",
                        ]
                        is_virtual_adapter = any(
                            s in current_adapter.lower() for s in skip_names
                        )
                        
                        if not _is_virtual_ip(ip) and not is_virtual_adapter:
                            candidates.append((current_adapter, ip))
                            print(f"[NET] Found: {ip} on '{current_adapter}'")
            
            if candidates:
                # Prefer WiFi over Ethernet
                for adapter, ip in candidates:
                    if "wi-fi" in adapter.lower() or "wireless" in adapter.lower():
                        print(f"[NET] Selected WiFi: {ip}")
                        return ip
                # Fall back to first non-virtual
                print(f"[NET] Selected: {candidates[0][1]}")
                return candidates[0][1]
        
        else:
            # Linux / Mac
            try:
                result = subprocess.run(
                    ["hostname", "-I"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                ips = result.stdout.strip().split()
                for ip in ips:
                    if not _is_virtual_ip(ip):
                        return ip
            except Exception:
                pass
    
    except Exception as e:
        print(f"[NET] Adapter scan failed: {e}")
    
    return None


def print_connection_qr():
    """Generates and prints the WebSocket URL and QR code in the terminal."""
    ip = get_local_ip()
    ws_url = f"ws://{ip}:8000/api/phone"
    http_url = f"http://{ip}:8000"
    
    print("\n" + "=" * 50)
    print(f"📱 SCAN TO CONNECT PHONE")
    print(f"🔗 URL: {ws_url}")
    print(f"🌐 Web: {http_url}")
    print(f"📡 IP:  {ip}")
    print("=" * 50 + "\n")
    
    # Warn if we got a suspicious IP
    if _is_virtual_ip(ip):
        print("⚠️  WARNING: Detected IP might be a virtual adapter!")
        print("⚠️  Make sure your phone is on the same WiFi network.")
        print("⚠️  Try disabling Windows Mobile Hotspot.\n")
    
    if ip == "127.0.0.1":
        print("❌ ERROR: Could not detect network IP!")
        print("❌ Make sure WiFi is connected.\n")
    
    # Generate ASCII QR code
    qr = qrcode.QRCode()
    qr.add_data(ws_url)
    try:
        qr.print_ascii(invert=True)
    except Exception:
        qr.print_ascii()
    print("\n")


if __name__ == "__main__":
    try:
        print_connection_qr()
    except ImportError:
        print("Please run: pip install qrcode")