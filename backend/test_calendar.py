import asyncio
import os
import sys

# Add backend directory to sys.path so we can import internal modules just like the actual app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.pipeline import process_text

async def test_calendar():
    text = "Schedule a meeting with Nikhil tomorrow at 3 PM for 2 hours."
    print("Testing input:", text)
    result = await process_text(text)
    print("\n\nResult JSON:\n", result)

if __name__ == "__main__":
    asyncio.run(test_calendar())
