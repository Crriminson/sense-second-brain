from fastapi import WebSocket
import json


class WSManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect_phone(self, ws: WebSocket):
        """Register a new WebSocket client (phone or browser). Allow multiple connections."""
        self.connections.append(ws)
        print(f"[WS] 📱 Client connected! Total connections: {len(self.connections)}")

    def disconnect_phone(self, ws: WebSocket):
        try:
            self.connections.remove(ws)
            print(f"[WS] 📱 Client disconnected. Remaining: {len(self.connections)}")
        except ValueError:
            pass  # Already removed

    async def broadcast(self, message: dict):
        """Send a message to all connected clients (phone + browsers)."""
        dead = []
        for ws in self.connections[:]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_phone(ws)


manager = WSManager()