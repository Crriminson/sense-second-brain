# interfaces/sockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from ws_manager import manager
from engine.pipeline import process_text

router = APIRouter()

@router.websocket("/api/phone")
async def phone_websocket(websocket: WebSocket):
    # 1. Accept the connection
    await manager.connect_phone(websocket)
    
    try:
        # 2. Keep listening for messages from the phone forever
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                print(f"[WS] Received invalid JSON: {raw_data}")
                continue
            
            # If the phone sends us recognized speech...
            if data.get("type") == "text_input":
                user_text = data.get("text", "")
                
                # 3. Send it to the Brain
                result = await process_text(user_text)
                
                # 4. Send the response back to the phone to speak!
                await websocket.send_text(json.dumps({
                    "type": "speak",
                    "text": result["spoken_response"]
                }))
            else:
                 print(f"[WS] Received unknown type: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect_phone(websocket)
    except Exception as e:
        print(f"[WS Error] {e}")
        manager.disconnect_phone(websocket)
