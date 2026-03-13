from fastapi import WebSocket
import json

class WSManager:
    def __init__(self):
        self.phone_connections: list[WebSocket] = []

    async def connect_phone(self, ws: WebSocket):
        # Close any existing phone connections first
        for old_ws in self.phone_connections[:]:
            try:
                await old_ws.close(code=4001, reason="New phone connected")
                print("[WS] 📱 Closed old phone connection")
            except Exception:
                pass
            self.phone_connections.remove(old_ws)
        
        self.phone_connections.append(ws)
        print(f"[WS] 📱 Phone connected! Total phones: {len(self.phone_connections)}")

    def disconnect_phone(self, ws: WebSocket):
        if ws in self.phone_connections:
            self.phone_connections.remove(ws)
            print("[WS] 📱 Phone disconnected.")

manager = WSManager()