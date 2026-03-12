from ai import classify, answer, relate
from store import notes, vectors
from . import tasks

# Main process_text() + intent handlers

async def process_text(text: str):
    # 1. Classify intent
    intent = classify(text)
    
    # 2. Handle intent
    if intent == "question":
        return answer(text)
    elif intent == "note":
        # Save note
        notes.create_note(text)
        # Add to vector store
        vectors.add(text, {"type": "note"})
        # Trigger background tasks
        tasks.compute_edges.delay(text)
        return "Note saved."
    else:
        return "I'm not sure what you mean."
