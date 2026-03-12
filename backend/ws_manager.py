# ws_manager.py
from fastapi import WebSocket
import json

class WSManager:
    def __init__(self):
        self.phone_connections: list[WebSocket] = []

    async def connect_phone(self, ws: WebSocket):
        self.phone_connections.append(ws)
        print(f"[WS] 📱 Phone connected! Total phones: {len(self.phone_connections)}")

    def disconnect_phone(self, ws: WebSocket):
        if ws in self.phone_connections:
            self.phone_connections.remove(ws)
            print("[WS] 📱 Phone disconnected.")

manager = WSManager()
