# ai/intents.py
"""
Intent classification.

Takes raw text from the user.
Returns structured intent with all extracted information.
NEVER throws. Always returns a valid dict.
"""

from . import provider
from config import settings


# ═══════════════════════════════════════
#  KNOWN INTENTS AND ACTIONS
# ═══════════════════════════════════════

VALID_INTENTS = {
    "create_note",
    "query_notes",
    "switch_workspace",
    "start_meeting",
    "end_meeting",
    "list_workspaces",
    "list_notes",
    "pc_command",
}

VALID_PC_ACTIONS = {
    "open_app", "close_app", "open_url", "open_folder",
    "screenshot", "set_volume", "media_play", "media_next",
    "toggle_dark_mode", "lock_screen", "focus_mode",
    "shutdown_timer", "cancel_shutdown", "type_text",
    "notify", "list_running",
}


# ═══════════════════════════════════════
#  PROMPT
# ═══════════════════════════════════════

INTENT_PROMPT = """You are an intent classifier for Second Brain, a voice-controlled personal workspace that can also control the user's computer.

Given the user's spoken input, determine what they want and extract all relevant information.

INTENTS:
- create_note: saving a thought, idea, reminder, fact, decision (DEFAULT — if unsure, use this)
- query_notes: asking about past notes ("what did I...", "find...", "when did I...")
- switch_workspace: changing project context ("switch to...", "let's work on...", "open project...")
- start_meeting: starting a recording session ("start meeting", "begin recording")
- end_meeting: ending a recording session ("end meeting", "stop recording")
- list_workspaces: asking what workspaces exist ("show workspaces", "what projects do I have")
- list_notes: asking to see notes ("show my notes", "what have I written")
- pc_command: controlling the computer ("open...", "close...", "volume...", "focus mode", "dark mode", "screenshot")

PC ACTIONS (only if intent is pc_command):
open_app, close_app, open_url, open_folder, screenshot, set_volume, media_play, media_next, toggle_dark_mode, lock_screen, focus_mode, shutdown_timer, cancel_shutdown, type_text, notify, list_running

Current workspace: {active_workspace}

User said: "{text}"

Respond in JSON:
{{
    "intent": "<intent>",
    "confidence": 0.0-1.0,
    "text": "<content to save if create_note, else null>",
    "query": "<question if query_notes, else null>",
    "workspace": "<workspace name if mentioned, else null>",
    "tags": ["auto", "detected", "tags"],
    "spoken_response": "<brief natural spoken confirmation>",
    "pc_actions": [
        {{"action": "<action_name>", "params": {{"target": "..."}}}}
    ]
}}

RULES:
1. If intent is NOT pc_command, pc_actions must be empty list []
2. If user wants BOTH a note and a PC action, choose the more important one
3. If unsure, default to create_note
4. spoken_response should be natural and brief — it will be spoken aloud
5. tags should be 1-4 relevant keywords from the content"""


# ═══════════════════════════════════════
#  CLASSIFICATION
# ═══════════════════════════════════════

async def classify(text: str, active_workspace: str = "General") -> dict:
    """
    Classify user intent from spoken text.
    
    ALWAYS returns a valid dict. Never throws.
    If AI fails entirely, defaults to create_note with the raw text.
    """
    prompt = INTENT_PROMPT.format(
        text=text,
        active_workspace=active_workspace,
    )

    raw = await provider.ask(
        prompt,
        temperature=0.1,
        json_mode=True,
        timeout=settings.TIMEOUT_INTENT,
    )

    # Parse and validate
    parsed = provider.parse_json(raw)

    if parsed:
        return _validate(parsed, text)
    else:
        return _fallback(text)


# ═══════════════════════════════════════
#  VALIDATION
# ═══════════════════════════════════════

def _validate(parsed: dict, original_text: str) -> dict:
    """
    Validate and sanitize LLM output.
    Every field is checked. Invalid values get defaults.
    The LLM can hallucinate whatever it wants — this function
    ensures the output is always clean and usable.
    """
    # Intent
    intent = parsed.get("intent", "create_note")
    if intent not in VALID_INTENTS:
        intent = "create_note"

    # Confidence
    confidence = parsed.get("confidence", 0.7)
    try:
        confidence = float(confidence)
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.5

    # Text content
    text = parsed.get("text")
    if text is not None and not isinstance(text, str):
        text = str(text)
    # If intent is create_note but no text extracted, use original
    if intent == "create_note" and not text:
        text = original_text

    # Query
    query = parsed.get("query")
    if query is not None and not isinstance(query, str):
        query = str(query)
    # If intent is query_notes but no query extracted, use original
    if intent == "query_notes" and not query:
        query = original_text

    # Workspace
    workspace = parsed.get("workspace")
    if workspace is not None and not isinstance(workspace, str):
        workspace = str(workspace)

    # Tags
    tags = parsed.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    tags = [str(t).strip() for t in tags if t and str(t).strip()]
    tags = tags[:5]  # cap at 5 tags

    # Spoken response
    spoken = parsed.get("spoken_response", "")
    if not isinstance(spoken, str) or not spoken.strip():
        spoken = _default_spoken(intent)

    # PC actions — validate each action
    pc_actions = []
    if intent == "pc_command":
        raw_actions = parsed.get("pc_actions", [])
        if isinstance(raw_actions, list):
            for action in raw_actions:
                if isinstance(action, dict):
                    action_name = action.get("action", "")
                    if action_name in VALID_PC_ACTIONS:
                        params = action.get("params", {})
                        if not isinstance(params, dict):
                            params = {}
                        pc_actions.append({
                            "action": action_name,
                            "params": params,
                        })

        # If intent is pc_command but no valid actions found,
        # switch to create_note
        if not pc_actions:
            intent = "create_note"
            text = original_text
            spoken = "I wasn't sure what command you wanted, so I saved it as a note."

    return {
        "intent": intent,
        "confidence": confidence,
        "text": text,
        "query": query,
        "workspace": workspace,
        "tags": tags,
        "spoken_response": spoken,
        "pc_actions": pc_actions,
    }


def _fallback(text: str) -> dict:
    """When AI completely fails, save as note."""
    return {
        "intent": "create_note",
        "confidence": 0.3,
        "text": text,
        "query": None,
        "workspace": None,
        "tags": [],
        "spoken_response": "I saved that as a note.",
        "pc_actions": [],
    }


def _default_spoken(intent: str) -> str:
    """Default spoken response per intent when LLM doesn't provide one."""
    defaults = {
        "create_note": "Got it, noted.",
        "query_notes": "Let me check.",
        "switch_workspace": "Switching workspace.",
        "start_meeting": "Starting meeting mode.",
        "end_meeting": "Meeting ended.",
        "list_workspaces": "Here are your workspaces.",
        "list_notes": "Here are your recent notes.",
        "pc_command": "Done.",
    }
    return defaults.get(intent, "Done.")
