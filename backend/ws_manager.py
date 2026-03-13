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
            try:
                self.phone_connections.remove(old_ws)
            except ValueError:
                pass  # Already removed by disconnect_phone, that's fine
        
        self.phone_connections.append(ws)
        print(f"[WS] 📱 Phone connected! Total phones: {len(self.phone_connections)}")

    def disconnect_phone(self, ws: WebSocket):
        if ws in self.phone_connections:
            self.phone_connections.remove(ws)
            print("[WS] 📱 Phone disconnected.")

    async def broadcast(self, message: dict):
        """Send a message to all connected phone clients."""
        dead = []
        for ws in self.phone_connections[:]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_phone(ws)

manager = WSManager()