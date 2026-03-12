from fastapi import WebSocket

# WebSocket endpoints (phone + UI)

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process message via engine
            # engine.process(data)
            await websocket.send_text(f"Received: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
