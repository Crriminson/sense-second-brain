# interfaces/sockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import traceback
from datetime import datetime
from ws_manager import manager
from engine.pipeline import process_text

router = APIRouter()

@router.websocket("/api/phone")
async def phone_websocket(websocket: WebSocket):
    print("[WS] === NEW CONNECTION ATTEMPT ===")
    try:
        # 1. Accept the connection
        print("[WS] Calling websocket.accept()...")
        await websocket.accept()
        print("[WS] ✅ Connection accepted")
        
        # 2. Send welcome message FIRST before anything else
        try:
            msg = {"type": "connected", "message": "Welcome to Second Brain"}
            print(f"[WS] Sending welcome: {msg}")
            await websocket.send_text(json.dumps(msg))
            print("[WS] ✅ Welcome message sent")
        except Exception as send_err:
            print(f"[WS] ❌ Failed to send welcome: {send_err}")
            traceback.print_exc()
            return
        
        # 3. Now register with manager
        try:
            print("[WS] Registering with manager...")
            await manager.connect_phone(websocket)
            print("[WS] ✅ Registered with manager")
        except Exception as mgr_err:
            print(f"[WS] ❌ Manager error: {mgr_err}")
            traceback.print_exc()
            return
        
        # 4. Keep listening for messages
        print("[WS] Entering receive loop...")
        while True:
            try:
                print("[WS] Waiting for message...")
                raw_data = await websocket.receive_text()
                print(f"[WS] ✅ Received: {raw_data[:100]}")
                
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    print(f"[WS] ❌ Invalid JSON: {raw_data}")
                    await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                    continue
                
                msg_type = data.get("type")
                print(f"[WS] Message type: {msg_type}")
                
                # Handshake
                if msg_type == "handshake":
                    print("[WS] → Handshake received")
                    await websocket.send_text(json.dumps({"type": "handshake_ack", "message": "Handshake OK"}))
                    print("[WS] → Sent handshake_ack")
                
                # Ping
                elif msg_type == "ping":
                    print("[WS] → Ping received")
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    print("[WS] → Sent pong")
                
                # Text input
                elif msg_type == "text_input":
                    user_text = data.get("text", "").strip()
                    print(f"[WS] → Text input: {user_text[:50]}")
                    
                    if not user_text:
                        await websocket.send_text(json.dumps({"type": "error", "message": "Empty text"}))
                        continue
                    
                    try:
                        print("[WS] Processing text...")
                        result = await process_text(user_text)
                        response = {
                            "type": "speak",
                            "text": result.get("spoken_response", "Got it"),
                            "intent": result.get("intent"),
                            "data": result.get("data", {}),
                        }
                        print(f"[WS] → Sending response: {response}")
                        try:
                            await websocket.send_text(json.dumps(response))
                            print("[WS] → Response sent")
                        except (WebSocketDisconnect, RuntimeError):
                            print("[WS] ⚠️ Client disconnected before response could be sent")
                            manager.disconnect_phone(websocket)
                            return
                    except Exception as proc_err:
                        print(f"[WS] ❌ Processing error: {proc_err}")
                        traceback.print_exc()
                        try:
                            await websocket.send_text(json.dumps({"type": "error", "message": str(proc_err)}))
                        except (WebSocketDisconnect, RuntimeError):
                            print("[WS] ⚠️ Client gone, couldn't send error")
                            manager.disconnect_phone(websocket)
                            return
                
                else:
                    print(f"[WS] Unknown type: {msg_type}")
                    
            except WebSocketDisconnect:
                print("[WS] Client disconnected (normal)")
                manager.disconnect_phone(websocket)
                break
            except Exception as inner_err:
                print(f"[WS] ❌ Receive loop error: {inner_err}")
                traceback.print_exc()
                try:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Server error"}))
                except:
                    pass
                break
                
    except Exception as e:
        print(f"[WS] ❌ Handler error: {e}")
        traceback.print_exc()
        try:
            manager.disconnect_phone(websocket)
        except:
            pass
