# ai/brain.py
import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"


async def _ask_llm(prompt: str, temperature: float = 0.1, force_json: bool = True) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        body = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 512},
        }
        if force_json:
            body["format"] = "json"

        resp = await client.post(OLLAMA_URL, json=body)
        resp.raise_for_status()
        return resp.json()["response"]


# ═══════════════════════════════════════
#  INTENT CLASSIFICATION
# ═══════════════════════════════════════

async def classify_intent(text: str, active_workspace: str = "General") -> dict:
    """Determine what the user wants from their spoken text."""

    prompt = f"""You are an intent classifier for a note-taking system.

INTENTS:
- create_note: saving a thought, idea, reminder, fact, decision
- query_notes: asking about past notes ("what did I...", "find...")
- switch_workspace: changing project ("switch to...", "let's work on...")
- start_meeting: starting a recording session
- end_meeting: ending a recording session
- list_workspaces: asking what workspaces exist
- list_notes: asking to see notes

Current workspace: {active_workspace}

User said: "{text}"

Respond ONLY in JSON:
{{
    "intent": "<intent>",
    "confidence": 0.0-1.0,
    "text": "<content to save if create_note, else null>",
    "query": "<question if query_notes, else null>",
    "workspace": "<workspace name if mentioned, else null>",
    "tags": ["auto", "detected"],
    "spoken_response": "<brief spoken confirmation>"
}}"""

    try:
        result = await _ask_llm(prompt)
        parsed = json.loads(result)
        return {
            "intent": parsed.get("intent", "create_note"),
            "confidence": parsed.get("confidence", 0.7),
            "text": parsed.get("text", text),
            "query": parsed.get("query"),
            "workspace": parsed.get("workspace"),
            "tags": parsed.get("tags", []),
            "spoken_response": parsed.get("spoken_response", "Done."),
        }
    except Exception as e:
        print(f"[AI] Intent classification failed: {e}")
        return {
            "intent": "create_note",
            "confidence": 0.5,
            "text": text,
            "query": None,
            "workspace": None,
            "tags": [],
            "spoken_response": "Saved as a note.",
        }


# ═══════════════════════════════════════
#  QUESTION ANSWERING (RAG)
# ═══════════════════════════════════════

async def answer_question(question: str, relevant_notes: list[dict]) -> str:
    """Given relevant notes from vector search, synthesize an answer."""

    if not relevant_notes:
        return "I don't have any notes about that yet."

    context = "\n".join([
        f"- [{n.get('workspace', '')}] {n['text'][:200]}"
        for n in relevant_notes
    ])

    prompt = f"""Answer the user's question using ONLY their notes below.
If the notes don't cover it, say so.
Keep it short — this will be spoken aloud.

Question: "{question}"

Notes:
{context}

Answer (plain text, not JSON):"""

    try:
        return await _ask_llm(prompt, temperature=0.3, force_json=False)
    except Exception as e:
        print(f"[AI] Answer failed: {e}")
        return "Sorry, I had trouble answering that."


# ═══════════════════════════════════════
#  RELATIONSHIP CLASSIFICATION
# ═══════════════════════════════════════

async def classify_relationship(new_text: str, existing_text: str) -> dict:
    """Determine how two notes relate to each other."""

    prompt = f"""Compare these two notes.

Note A (existing): "{existing_text[:300]}"
Note B (new): "{new_text[:300]}"

Relationship types:
- "related_to": same topic or theme
- "contradicts": conflicting information or decisions
- "extends": B adds detail or builds on A
- "none": no meaningful connection

Respond ONLY in JSON:
{{
    "rel_type": "related_to|contradicts|extends|none",
    "weight": 0.0-1.0,
    "explanation": "one sentence why"
}}"""

    try:
        result = await _ask_llm(prompt)
        parsed = json.loads(result)
        return {
            "rel_type": parsed.get("rel_type", "related_to"),
            "weight": parsed.get("weight", 0.5),
            "explanation": parsed.get("explanation", ""),
        }
    except Exception:
        return {"rel_type": "related_to", "weight": 0.5, "explanation": ""}


# ═══════════════════════════════════════
#  MEETING SUMMARIZATION
# ═══════════════════════════════════════

async def summarize_transcript(transcript: str) -> dict:
    """Summarize a meeting transcript into summary + action items."""

    prompt = f"""Summarize this meeting transcript.

Transcript:
{transcript[:3000]}

Respond in JSON:
{{
    "summary": "2-3 sentence summary",
    "action_items": ["action item 1", "action item 2"]
}}"""

    try:
        result = await _ask_llm(prompt, temperature=0.2)
        return json.loads(result)
    except Exception:
        return {"summary": "Could not summarize.", "action_items": []}
