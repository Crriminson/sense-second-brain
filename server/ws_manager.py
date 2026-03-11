# ws_manager.py
from fastapi import WebSocket
import json


class WSManager:
    def __init__(self):
        self.ui_connections: list[WebSocket] = []
        self.phone_connections: list[WebSocket] = []

    # ── UI (desktop webapp) ──

    async def connect_ui(self, ws: WebSocket):
        await ws.accept()
        self.ui_connections.append(ws)
        print(f"[WS] UI connected ({len(self.ui_connections)} total)")

    def disconnect_ui(self, ws: WebSocket):
        if ws in self.ui_connections:
            self.ui_connections.remove(ws)

    async def broadcast_ui(self, event_type: str, data: dict):
        msg = json.dumps({"type": event_type, "data": data})
        dead = []
        for ws in self.ui_connections:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.disconnect_ui(d)

    # ── Phone ──

    async def connect_phone(self, ws: WebSocket):
        await ws.accept()
        self.phone_connections.append(ws)
        print(f"[WS] Phone connected ({len(self.phone_connections)} total)")

    def disconnect_phone(self, ws: WebSocket):
        if ws in self.phone_connections:
            self.phone_connections.remove(ws)

    async def send_to_phone(self, event_type: str, data: dict):
        msg = json.dumps({"type": event_type, "data": data})
        dead = []
        for ws in self.phone_connections:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.disconnect_phone(d)


manager = WSManager()
