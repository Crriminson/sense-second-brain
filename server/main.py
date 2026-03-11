# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio
import json

from database import init_db, db_router
from vector import init_vector
from orchestration import process_text
from orchestration.pipeline import end_meeting_session
from ws_manager import manager
from mqtt_handler import set_callbacks, start_mqtt, stop_mqtt
import database.crud as crud


# ═══════════════════════════════════════
#  APP SETUP
# ═══════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_vector()
    mqtt_task = asyncio.create_task(start_mqtt())
    print("[SERVER] Second Brain is online")
    yield
    await stop_mqtt()
    mqtt_task.cancel()


app = FastAPI(title="Second Brain", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════
#  MQTT CALLBACKS
# ═══════════════════════════════════════

async def on_presence(payload: dict):
    status = payload.get("status", "")
    if status == "detected":
        await manager.send_to_phone("activate", {"reason": "presence"})
        await manager.broadcast_ui("presence", {"status": "active"})
    elif status == "away":
        await manager.broadcast_ui("presence", {"status": "away"})


async def on_button(payload: dict):
    action = payload.get("action", "")

    if action == "short_press":
        await manager.send_to_phone("start_capture", {"mode": "note"})

    elif action == "long_press":
        try:
            session = await crud.start_session()
            await manager.send_to_phone("start_capture", {
                "mode": "meeting", "session_id": session["id"]
            })
            await manager.broadcast_ui("session_started", session)
        except Exception as e:
            print(f"[MQTT] Start session failed: {e}")

    elif action == "double_press":
        active = await crud.get_active_session()
        if active:
            result = await end_meeting_session(active["id"])
            await manager.broadcast_ui("session_ended", result)


set_callbacks(on_presence=on_presence, on_button=on_button)


# ═══════════════════════════════════════
#  WEBSOCKET — UI (desktop webapp)
# ═══════════════════════════════════════

@app.websocket("/api/ui")
async def ui_ws(websocket: WebSocket):
    await manager.connect_ui(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_ui(websocket)


# ═══════════════════════════════════════
#  WEBSOCKET — Phone
# ═══════════════════════════════════════

@app.websocket("/api/phone")
async def phone_ws(websocket: WebSocket):
    """
    Phone sends text (from Android STT).
    Server processes and responds.

    Phone sends:  {"type": "text_input", "text": "..."}
    Phone sends:  {"type": "transcript_chunk", "session_id": "...", "text": "..."}
    Server sends: {"type": "response", "intent": "...", "spoken_response": "..."}
    Server sends: {"type": "speak", "text": "..."} (phone uses TTS)
    """
    await manager.connect_phone(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "")

            if msg_type == "text_input":
                # User said something → process it
                text = data.get("text", "").strip()
                if not text:
                    continue

                result = await process_text(text)

                await websocket.send_text(json.dumps({
                    "type": "response",
                    "intent": result.get("intent", "unknown"),
                    "spoken_response": result.get("spoken_response", ""),
                    "data": result,
                }))

                # Tell phone to speak the response
                spoken = result.get("spoken_response", "")
                if spoken:
                    await websocket.send_text(json.dumps({
                        "type": "speak",
                        "text": spoken,
                    }))

            elif msg_type == "transcript_chunk":
                # Meeting mode: append chunk to active session
                session_id = data.get("session_id", "")
                chunk = data.get("text", "")
                if session_id and chunk:
                    await crud.append_transcript(session_id, chunk)
                    await manager.broadcast_ui("transcript_chunk", {
                        "session_id": session_id,
                        "text": chunk,
                    })

    except WebSocketDisconnect:
        manager.disconnect_phone(websocket)


# ═══════════════════════════════════════
#  REST — Process (typed input / testing)
# ═══════════════════════════════════════

class TextInput(BaseModel):
    text: str


@app.post("/api/process")
async def api_process(data: TextInput):
    return await process_text(data.text)


# ═══════════════════════════════════════
#  MOUNT DATABASE ROUTES
# ═══════════════════════════════════════

app.include_router(db_router, prefix="/api")


# ═══════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "alive"}
