# ai/answers.py
"""
Question answering and meeting summarization.

Takes a question + relevant notes (from vector search) + edge context.
Synthesizes a natural language answer.

Also handles meeting transcript summarization.

NEVER throws. Always returns usable output.
"""

from . import provider
from config import settings


# ═══════════════════════════════════════
#  PROMPTS
# ═══════════════════════════════════════

ANSWER_PROMPT = """You are the memory retrieval system for Second Brain, a personal knowledge workspace.

The user is asking about something from their past notes. Answer based ONLY on the notes provided below.

Rules:
1. Only use information from the provided notes
2. If the notes don't contain enough info, say so honestly
3. If there are contradictions between notes, mention them
4. Keep the answer short and conversational — it will be spoken aloud
5. Reference timeframes if available ("you mentioned last Tuesday...")

Question: "{question}"

Relevant notes:
{context}

{edge_context}

Answer (conversational, 2-4 sentences max):"""


SUMMARIZE_PROMPT = """Summarize this meeting transcript.

Extract:
1. A brief 2-3 sentence summary of what was discussed
2. Concrete action items (things someone needs to DO)

Transcript:
{transcript}

Respond in JSON:
{{
    "summary": "<2-3 sentence summary>",
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
        return "I don't have any notes about that yet."

    # Build context from notes
    context_parts = []
    for i, note in enumerate(relevant_notes):
        text = note.get("text", "")
        workspace = note.get("workspace", "")
        similarity = note.get("similarity", 0)
        context_parts.append(
            f"[Note {i+1}] (workspace: {workspace}, relevance: {similarity})\n{text[:300]}"
        )
    context = "\n---\n".join(context_parts)

    # Build edge context
    edge_text = ""
    if edge_context:
        edge_parts = []
        for edge in edge_context:
            rel = edge.get("rel_type", "related_to")
            if rel == "contradicts":
                src = edge.get("source_text", "")[:80]
                tgt = edge.get("target_text", "")[:80]
                edge_parts.append(
                    f"⚠️ CONTRADICTION: \"{src}\" conflicts with \"{tgt}\""
                )
            elif rel == "extends":
                src = edge.get("source_text", "")[:80]
                tgt = edge.get("target_text", "")[:80]
                edge_parts.append(
                    f"📎 BUILDS ON: \"{tgt}\" expands on \"{src}\""
                )
        if edge_parts:
            edge_text = "Known relationships between notes:\n" + "\n".join(edge_parts)

    prompt = ANSWER_PROMPT.format(
        question=question,
        context=context,
        edge_context=edge_text,
    )

    # Don't force JSON — we want natural language
    result = await provider.ask(
        prompt,
        temperature=0.3,
        json_mode=False,
        timeout=settings.TIMEOUT_ANSWER,
    )

    if result and result.strip():
        return result.strip()
    else:
        return "Sorry, I had trouble answering that. Try asking differently?"


# ═══════════════════════════════════════
#  MEETING SUMMARIZATION
# ═══════════════════════════════════════

async def summarize(transcript: str) -> dict:
    """
    Summarize a meeting transcript.
    
    Returns:
        {
            "summary": "2-3 sentence summary",
            "action_items": ["item 1", "item 2"]
        }
    
    NEVER throws. Returns fallback if AI fails.
    """
    if not transcript or not transcript.strip():
        return {
            "summary": "Empty meeting — no transcript recorded.",
            "action_items": [],
        }

    # Truncate very long transcripts
    # Most models have 4k-8k context window
    truncated = transcript[:4000]
    if len(transcript) > 4000:
        truncated += "\n[... transcript truncated for summarization ...]"

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
            "summary": "Meeting ended. I had trouble summarizing — the raw transcript is saved.",
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
    action_items = [str(item).strip() for item in action_items if item and str(item).strip()]

    return {
        "summary": summary.strip(),
        "action_items": action_items,
    }
