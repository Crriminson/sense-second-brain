import asyncio
import os
import sys

# Add backend directory to sys.path so we can import internal modules just like the actual app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.pipeline import process_text
from engine import memory

async def test_calendar_context():
    # Turn 1
    text1 = "I have a Math assignment deadline for tomorrow"
    print("\n[USER_TURN] 1:", text1)
    res1 = await process_text(text1)
    
    # Simulate adding to memory (done inside process_text automatically)
    print("AI Response:", res1.get("spoken_response"))
    print("Classified intent:", res1.get("intent"))
    
    # Turn 2
    text2 = "add it to my Google calendar"
    print("\n[USER_TURN] 2:", text2)
    res2 = await process_text(text2)
    print("AI Response:", res2.get("spoken_response"))
    print("Classified intent:", res2.get("intent"))
    print("Actions outputed:", res2.get("data", {}))

if __name__ == "__main__":
    asyncio.run(test_calendar_context())
