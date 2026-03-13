import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.pipeline import process_text

async def test_shell():
    text = "can you create a folder in project on my desktop"
    print("\n[USER] 1:", text)
    res = await process_text(text)
    
    print("AI Response:", res.get("spoken_response"))
    print("Classified intent:", res.get("intent"))
    print("Actions outputed:", res.get("data", {}))

if __name__ == "__main__":
    asyncio.run(test_shell())
