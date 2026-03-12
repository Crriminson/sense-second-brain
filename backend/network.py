# network.py
import socket
import qrcode
import sys

def get_local_ip():
    """Finds the local IP address of this PC on the WiFi network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to actually connect, just routes a dummy packet
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def print_connection_qr():
    """Generates and prints the WebSocket URL and QR code in the terminal."""
    ip = get_local_ip()
    ws_url = f"ws://{ip}:8000/api/phone"
    
    print("\n" + "="*50)
    print(f"📱 SCAN TO CONNECT PHONE")
    print(f"🔗 URL: {ws_url}")
    print("="*50 + "\n")
    
    # Generate ASCII QR code
    qr = qrcode.QRCode()
    qr.add_data(ws_url)
    try:
        qr.print_ascii(invert=True) # invert=True looks better on dark terminals
    except Exception:
         # Fallback for terminals that might not support the output
        qr.print_ascii()
    print("\n")

if __name__ == "__main__":
    try:
        print_connection_qr()
    except ImportError:
        print("Please run: pip install qrcode")
