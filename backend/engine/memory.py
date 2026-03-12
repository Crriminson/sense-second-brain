"""
Short-term conversation memory.

Rolling window of recent turns kept in RAM.
Fed into the intent prompt so the LLM understands context like
"put that in personal" after "remind me to buy milk."

Resets on server restart — that's fine. This is working memory,
not long-term storage (that's what notes + user_profile handle).

Called by pipeline:
  - add_turn(user_text, ai_response, intent)  → after every process_text
  - get_recent(n)                              → during _build_context
"""

from collections import deque
from datetime import datetime


_MAX_TURNS = 20
_history: deque[dict] = deque(maxlen=_MAX_TURNS)


def add_turn(user_text: str, ai_response: str, intent: str) -> None:
    """
    Record one conversation turn.
    Called at the end of every process_text, after the handler runs.
    """
    _history.append({
        "user": user_text.strip(),
        "ai": ai_response.strip() if ai_response else "",
        "intent": intent,
        "time": datetime.now().strftime("%H:%M"),
    })


def get_recent(n: int = 5) -> str:
    """
    Return last N turns as a formatted string for the prompt.

    Example output:
      [10:23] User: remind me to buy milk
      [10:23] AI: Saved to General. That's note #4. [create_note]
      [10:24] User: put that in personal
      [10:24] AI: Switched to Personal. 2 notes here. [switch_workspace]

    Returns empty string if no history — the prompt builder
    checks for this and skips the section.
    """
    if not _history:
        return ""

    recent = list(_history)[-n:]
    lines = []

    for turn in recent:
        ts = turn["time"]
        lines.append(f"[{ts}] User: {turn['user']}")
        if turn["ai"]:
            lines.append(f"[{ts}] AI: {turn['ai']} [{turn['intent']}]")

    return "\n".join(lines)


def get_last_turn() -> dict | None:
    """
    Get the most recent turn. Useful for handlers that need
    to reference what just happened (e.g., delete_note deleting
    what was just created).
    """
    if not _history:
        return None
    return _history[-1]


def get_last_intent() -> str | None:
    """Quick check: what did the user just do?"""
    if not _history:
        return None
    return _history[-1]["intent"]


def get_last_user_text() -> str | None:
    """What did the user just say?"""
    if not _history:
        return None
    return _history[-1]["user"]


def clear() -> None:
    """Wipe memory. For testing or session reset."""
    _history.clear()


def count() -> int:
    """How many turns are stored."""
    return len(_history)