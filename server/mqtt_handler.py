# mqtt_handler.py
import json
import asyncio

_mqtt_client = None
_running = False
_on_presence = None
_on_button = None


def set_callbacks(on_presence=None, on_button=None):
    global _on_presence, _on_button
    _on_presence = on_presence
    _on_button = on_button


async def publish_feedback(signal: str):
    if _mqtt_client:
        try:
            await _mqtt_client.publish(
                "secondbrain/feedback",
                json.dumps({"signal": signal})
            )
        except Exception as e:
            print(f"[MQTT] Publish failed: {e}")


async def start_mqtt():
    global _mqtt_client, _running

    BROKER = "localhost"
    PORT = 1883

    try:
        import aiomqtt
    except ImportError:
        print("[MQTT] aiomqtt not installed — ESP32 features disabled")
        print("[MQTT] System works fine without it")
        while True:
            await asyncio.sleep(3600)
        return

    _running = True

    while _running:
        try:
            async with aiomqtt.Client(BROKER, PORT) as client:
                _mqtt_client = client
                print(f"[MQTT] Connected to {BROKER}:{PORT}")

                await client.subscribe("secondbrain/presence")
                await client.subscribe("secondbrain/button")

                async for message in client.messages:
                    topic = str(message.topic)
                    try:
                        payload = json.loads(message.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

                    if topic == "secondbrain/presence" and _on_presence:
                        await _on_presence(payload)
                    elif topic == "secondbrain/button" and _on_button:
                        await _on_button(payload)

        except Exception as e:
            _mqtt_client = None
            if _running:
                print(f"[MQTT] Connection failed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)


async def stop_mqtt():
    global _running
    _running = False
