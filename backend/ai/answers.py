"""
Question answering and meeting summarization.

Takes a question + relevant notes (from vector search) + edge context.
Synthesizes a natural answer.

Also handles meeting transcript summarization.

NEVER throws. Always returns usable output.
"""

from . import provider
from config import settings


# ═══════════════════════════════════════
#  PROMPTS
# ═══════════════════════════════════════

ANSWER_PROMPT = """You are Second Brain — a personal AI that recalls the user's past notes.

You are retrieving the user's OWN memories. Talk like a chill friend who remembers things for them.

RULES — follow these STRICTLY:
1. ONLY use information from the provided notes. Never invent facts.
2. Maximum 2 sentences. This gets spoken aloud — brevity is everything.
3. NO hedging. No "unfortunately", "it seems like", "I'm not sure", "it appears".
4. NO yapping. No filler. No restating the question. Just answer.
5. If names sound similar (Bhole/Bole, Suvarna/Swarna), treat them as the SAME person.
   Whisper speech-to-text often misspells names — assume phonetic matches are the same.
6. If notes contradict each other, mention it briefly: "You said X, but later said Y."
7. If you genuinely don't have the info, just say "Nothing in your notes about that."
8. Speak like a person, not a database. Warm, direct, zero fluff.

GOOD examples:
  "Yeah, you noted that Pratham is from EXTC B."
  "You said Aditya Bhole's bottle is red."
  "Nothing in your notes about that."
  "You mentioned the API uses JWT tokens, but later said to switch to OAuth."

BAD examples (never do this):
  "Unfortunately, I was unable to find comprehensive information about..."
  "It seems like you may have mentioned something related to..."
  "Based on the available notes, it appears that..."
  "I found a note that mentions X, but it doesn't have additional details..."

Question: "{question}"

Notes:
{context}

{edge_context}

Answer:"""


SUMMARIZE_PROMPT = """Summarize this meeting transcript.

Extract:
1. A brief 2 sentence summary of what was discussed
2. Concrete action items (things someone needs to DO)

Keep it tight. No filler.

Transcript:
{transcript}

Respond in JSON:
{{
    "summary": "<2 sentence summary>",
    "action_items": ["<specific action 1>", "<specific action 2>"]
}}

If no clear action items exist, return an empty list.
Do NOT invent action items that aren't in the transcript."""


# ═══════════════════════════════════════
#  QUESTION ANSWERING
# ═══════════════════════════════════════

async def answer(
    question: str,
    relevant_notes: list[dict],
    edge_context: list[dict] = [],
) -> str:
    """
    Given a question and relevant notes, synthesize an answer.

    relevant_notes: from vector search
        [{ "text": "...", "workspace": "...", "similarity": 0.87 }]

    edge_context: relationships between those notes
        [{ "rel_type": "contradicts", "source_text": "...", "target_text": "..." }]

    Returns: natural language answer string.
    """
    if not relevant_notes:
        return "Nothing in your notes about that."

    # Build context from notes — compact, no fluff
    context_parts = []
    for i, note in enumerate(relevant_notes):
        text = note.get("text", "")[:200]
        workspace = note.get("workspace", "")
        context_parts.append(f"[{workspace}] {text}")
    context = "\n".join(context_parts)

    # Build edge context — only include if meaningful
    edge_text = ""
    if edge_context:
        edge_parts = []
        for edge in edge_context:
            rel = edge.get("rel_type", "related_to")
            if rel == "contradicts":
                src = edge.get("source_text", "")[:60]
                tgt = edge.get("target_text", "")[:60]
                edge_parts.append(f"CONTRADICTION: \"{src}\" vs \"{tgt}\"")
            elif rel == "extends":
                src = edge.get("source_text", "")[:60]
                tgt = edge.get("target_text", "")[:60]
                edge_parts.append(f"RELATED: \"{tgt}\" builds on \"{src}\"")
        if edge_parts:
            edge_text = "Relationships:\n" + "\n".join(edge_parts)

    prompt = ANSWER_PROMPT.format(
        question=question,
        context=context,
        edge_context=edge_text,
    )

    result = await provider.ask(
        prompt,
        temperature=0.3,
        json_mode=False,
        timeout=settings.TIMEOUT_ANSWER,
    )

    if result and result.strip():
        # Strip any quotes the LLM might wrap the answer in
        answer_text = result.strip().strip('"').strip("'")
        return answer_text
    else:
        return "Couldn't pull that up right now. Try asking again?"


# ═══════════════════════════════════════
#  GENERAL KNOWLEDGE ANSWER
# ═══════════════════════════════════════

GENERAL_PROMPT = """Answer this question directly. 2-3 sentences max.
Talk like a knowledgeable friend — warm, clear, no lecture tone.
This will be spoken aloud so keep it natural.

Question: "{question}"

Answer:"""


async def answer_general(question: str) -> str:
    """
    Answer a general knowledge question (not from user's notes).
    Used by the general_query intent handler.
    """
    prompt = GENERAL_PROMPT.format(question=question)

    result = await provider.ask(
        prompt,
        temperature=0.4,
        json_mode=False,
        timeout=settings.TIMEOUT_ANSWER,
    )

    if result and result.strip():
        return result.strip().strip('"').strip("'")
    else:
        return "I blanked on that one. Try asking differently?"


# ═══════════════════════════════════════
#  MEETING SUMMARIZATION
# ═══════════════════════════════════════

async def summarize(transcript: str) -> dict:
    """
    Summarize a meeting transcript.

    Returns:
        {
            "summary": "2 sentence summary",
            "action_items": ["item 1", "item 2"]
        }

    NEVER throws. Returns fallback if AI fails.
    """
    if not transcript or not transcript.strip():
        return {
            "summary": "Empty meeting — nothing recorded.",
            "action_items": [],
        }

    # Truncate very long transcripts
    truncated = transcript[:4000]
    if len(transcript) > 4000:
        truncated += "\n[... transcript truncated ...]"

    prompt = SUMMARIZE_PROMPT.format(transcript=truncated)

    raw = await provider.ask(
        prompt,
        temperature=0.2,
        json_mode=True,
        timeout=settings.TIMEOUT_SUMMARIZE,
    )

    parsed = provider.parse_json(raw)

    if parsed:
        return _validate_summary(parsed)
    else:
        return {
            "summary": "Meeting ended. Couldn't summarize — raw transcript is saved.",
            "action_items": [],
        }


def _validate_summary(parsed: dict) -> dict:
    """Validate summarization output."""
    summary = parsed.get("summary", "")
    if not isinstance(summary, str) or not summary.strip():
        summary = "Meeting summary unavailable."

    action_items = parsed.get("action_items", [])
    if not isinstance(action_items, list):
        action_items = []
    action_items = [
        str(item).strip()
        for item in action_items
        if item and str(item).strip()
    ]

    return {
        "summary": summary.strip(),
        "action_items": action_items,
    }