# engine/pipeline.py
from ai import intents

async def process_text(text: str) -> dict:
    """
    Takes text from the phone, runs it through AI, 
    and returns what the system should do/say.
    """
    print(f"[ENGINE] Processing: '{text}'")
    
    # Run the AI classification we tested earlier
    classified = await intents.classify(text, active_workspace="General")
    
    # We will add database saving here later, 
    # but for now, let's just return the AI's response to test the loop!
    
    print(f"[ENGINE] AI decided intent is: {classified['intent']}")
    print(f"[ENGINE] AI wants to say: {classified['spoken_response']}")
    
    return classified
