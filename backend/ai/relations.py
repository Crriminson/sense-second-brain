# ai/relations.py
"""
Relationship classification between two notes.

Given two notes, determines if they are related, contradictory,
or if one extends the other.

Called in the background after a note is saved.
Results are stored as edges in the knowledge graph.

NEVER throws. Returns "related_to" as safe default.
"""

from . import provider
from config import settings


# ═══════════════════════════════════════
#  PROMPT
# ═══════════════════════════════════════

RELATION_PROMPT = """Compare these two notes from a personal knowledge workspace.

Note A (existing): "{text_a}"
Note B (new): "{text_b}"

Determine their relationship:
- "related_to": same topic or theme, no conflict
- "contradicts": conflicting information, decisions, or opinions
- "extends": B adds detail, elaborates, or builds upon A
- "none": no meaningful connection

Respond in JSON:
{{
    "rel_type": "related_to|contradicts|extends|none",
    "weight": 0.0-1.0,
    "explanation": "one sentence explaining the relationship"
}}

RULES:
1. "contradicts" means they CANNOT both be true/current (e.g., "use Postgres" vs "use MongoDB")
2. "extends" means B would not fully make sense without A
3. If they merely share a keyword but aren't meaningfully connected, use "none"
4. weight = how strong/obvious the connection is (0.9+ = very clear, 0.5 = somewhat)"""


VALID_RELATIONS = {"related_to", "contradicts", "extends", "none"}


# ═══════════════════════════════════════
#  CLASSIFICATION
# ═══════════════════════════════════════

async def classify(text_a: str, text_b: str) -> dict:
    """
    Determine the relationship between two notes.
    
    text_a: existing note
    text_b: new note
    
    Returns:
        {
            "rel_type": "related_to" | "contradicts" | "extends" | "none",
            "weight": 0.0-1.0,
            "explanation": "one sentence"
        }
    
    NEVER throws. Defaults to "related_to" if AI fails.
    """
    # Truncate to save tokens and speed up
    a_truncated = text_a[:400]
    b_truncated = text_b[:400]

    prompt = RELATION_PROMPT.format(
        text_a=a_truncated,
        text_b=b_truncated,
    )

    raw = await provider.ask(
        prompt,
        temperature=0.1,
        json_mode=True,
        timeout=settings.TIMEOUT_RELATION,
    )

    parsed = provider.parse_json(raw)

    if parsed:
        return _validate(parsed)
    else:
        return _fallback()


def _validate(parsed: dict) -> dict:
    """Validate relationship output."""
    rel_type = parsed.get("rel_type", "related_to")
    if rel_type not in VALID_RELATIONS:
        rel_type = "related_to"

    weight = parsed.get("weight", 0.5)
    try:
        weight = float(weight)
        weight = max(0.0, min(1.0, weight))
    except (TypeError, ValueError):
        weight = 0.5

    explanation = parsed.get("explanation", "")
    if not isinstance(explanation, str):
        explanation = ""

    return {
        "rel_type": rel_type,
        "weight": weight,
        "explanation": explanation.strip(),
    }


def _fallback() -> dict:
    """Safe default when AI fails."""
    return {
        "rel_type": "related_to",
        "weight": 0.5,
        "explanation": "Relationship could not be determined.",
    }
