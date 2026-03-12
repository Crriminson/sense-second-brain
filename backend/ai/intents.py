"""
Intent classification with context-aware prompting and few-shot examples.
12 intents. Dynamic context. Few-shot examples for every intent.
Tone: chill, human, zero fluff.
"""

from . import provider
from config import settings


# ═══════════════════════════════════════
#  VALID INTENTS AND ACTIONS
# ═══════════════════════════════════════

VALID_INTENTS = {
    "create_note",
    "update_note",
    "query_notes",
    "delete_note",
    "list_notes",
    "switch_workspace",
    "list_workspaces",
    "start_meeting",
    "end_meeting",
    "pc_command",
    "general_query",
    "greeting",
}

VALID_PC_ACTIONS = {
    "open_app", "close_app", "open_url", "open_folder",
    "screenshot", "set_volume", "volume_up", "volume_down",
    "media_play", "media_pause", "media_next", "media_prev",
    "toggle_dark_mode", "lock_screen", "focus_mode",
    "shutdown_timer", "cancel_shutdown", "type_text",
}


# ═══════════════════════════════════════
#  PROMPT BUILDER
# ═══════════════════════════════════════

def build_prompt(text: str, context: dict) -> str:
    active_ws = context.get("active_workspace", "General")
    ws_summaries = context.get("workspace_summaries", "General (0 notes)")
    tag_cloud = context.get("tag_cloud", "")
    recent = context.get("recent_notes", "")
    conv = context.get("conversation_history", "")
    profile = context.get("user_profile", "")

    sections = []

    sections.append(f"""CURRENT STATE:
- Active workspace: "{active_ws}"
- Workspaces: [{ws_summaries}]""")

    if tag_cloud:
        sections.append(f"- Common tags: [{tag_cloud}]")

    if profile and "no profile" not in profile.lower():
        sections.append(f"\nUSER PROFILE:\n{profile}")

    if recent:
        sections.append(f"\nRECENT NOTES IN THIS WORKSPACE:\n{recent}")

    if conv and "no conversation" not in conv.lower():
        sections.append(f"\nLAST CONVERSATION:\n{conv}")

    context_block = "\n".join(sections)

    return f"""You are Second Brain — a voice-controlled personal workspace assistant.
You manage notes, workspaces, answer questions, and control the PC.
Your responses will be spoken aloud.

TONE: Talk like a chill, helpful friend. Short and warm. No corporate speak.
  GOOD: "Got it, saved." / "Switched to Hackathon, you've got 4 notes here."
  BAD:  "I have successfully processed your request and saved the note."

SPEECH-TO-TEXT WARNING: The input comes from Whisper STT which often:
  - Misspells names: "Bole" = "Bhole", "Suvarna" = "Swarna"
  - Mishears words: "and meeting" = "end meeting", "it's to" = "switch to"
  - Drops words or merges them
  ALWAYS interpret charitably. Guess what the user MEANT, not what was literally said.

{context_block}

CLASSIFY the user's message into exactly ONE intent.

═══ INTENTS ═══

create_note — User wants to SAVE a new thought, idea, reminder, fact, or decision.
  "remind me to call the dentist tomorrow" → create_note
  "the API endpoint is /api/v2/users" → create_note
  "I decided we should use PostgreSQL" → create_note
  "meeting with John at 3pm on Friday" → create_note
  "note to self buy groceries" → create_note
  "the bug was caused by a race condition" → create_note
  "Aditya scored 95 in the exam" → create_note
  "we need to fix the auth flow before launch" → create_note

update_note — User wants to ADD information to an EXISTING note or EDIT a previous note.
  "in the note about hack overflow, add Aditya's name" → update_note
  "add to that — he's from EXTC B" → update_note
  "the hackathon note also includes Naman" → update_note
  "update the API note with the new endpoint" → update_note
  "that note about Pratham — he's also the team lead" → update_note
  "actually change that to PostgreSQL not MySQL" → update_note

query_notes — User asks about something from THEIR OWN past notes/memories.
  "what did I say about the database?" → query_notes
  "find my notes on authentication" → query_notes
  "what was that API endpoint I saved?" → query_notes
  "who is Pratham?" → query_notes
  "do I have anything about deployment?" → query_notes
  "what were the action items from last meeting?" → query_notes
  "tell me about Aditya Bhole" → query_notes
  "what's the bottle colour I mentioned?" → query_notes
  "explain what I just said" → query_notes

general_query — User asks a GENERAL KNOWLEDGE question (NOT about their own notes).
  "explain how JWT tokens work" → general_query
  "what is machine learning?" → general_query
  "how do I center a div in CSS?" → general_query
  "what's the capital of France?" → general_query
  "what is 7 times 4" → general_query
  "how does async await work in Python?" → general_query
  "what's the weather like" → general_query
  "what time is it" → general_query
  KEY: If the user is asking you to EXPLAIN something or ANSWER a factual question, this is it.
  If they're asking about THEIR OWN notes/memories, use query_notes instead.

delete_note — User wants to DELETE or REMOVE a note.
  "delete that last note" → delete_note
  "remove that" → delete_note
  "undo that note" → delete_note
  "scratch that" → delete_note
  "delete all notes" → delete_note
  "clear this workspace" → delete_note
  "get rid of the last thing I said" → delete_note
  "never mind don't save that" → delete_note

switch_workspace — User wants to SWITCH to or CREATE a workspace/project.
  "switch to Project X" → switch_workspace, workspace: "Project X"
  "let's work on the hackathon" → switch_workspace, workspace: "hackathon"
  "go to my research project" → switch_workspace, workspace: "research"
  "open the marketing workspace" → switch_workspace, workspace: "marketing"
  "create a workspace called YouTube" → switch_workspace, workspace: "YouTube"
  "create a workspace named hack overflow" → switch_workspace, workspace: "hack overflow"
  "make a new workspace for school" → switch_workspace, workspace: "school"
  "I want to work on personal stuff" → switch_workspace, workspace: "personal"
  "switch to general" → switch_workspace, workspace: "General"
  "it's to general" → switch_workspace, workspace: "General"
  KEY: Creating a workspace IS switching to it. If the name doesn't exist, the system creates it automatically.
  KEY: "it's to X" is Whisper mishearing "switch to X" — treat it as switch_workspace.

list_workspaces — User wants to SEE what workspaces exist.
  "what workspaces do I have" → list_workspaces
  "show my projects" → list_workspaces
  "list workspaces" → list_workspaces
  "how many workspaces" → list_workspaces

list_notes — User wants to SEE their recent notes.
  "show my notes" → list_notes
  "what have I written today" → list_notes
  "show recent notes" → list_notes
  "what's in this workspace" → list_notes

start_meeting — User wants to START recording a meeting/session.
  "start meeting" → start_meeting
  "begin recording" → start_meeting
  "record this conversation" → start_meeting
  "start a session" → start_meeting
  "start a meeting" → start_meeting

end_meeting — User wants to STOP recording a meeting/session.
  "end meeting" → end_meeting
  "end the meeting" → end_meeting
  "and meeting" → end_meeting  (Whisper often mishears "end" as "and")
  "stop recording" → end_meeting
  "we're done" → end_meeting
  "end the session" → end_meeting
  "finish meeting" → end_meeting

pc_command — User wants to CONTROL their computer.
  "open Chrome" → pc_command, action: open_app, target: "chrome"
  "open YouTube" → pc_command, action: open_url, target: "https://youtube.com"
  "close Discord" → pc_command, action: close_app, target: "discord"
  "close settings" → pc_command, action: close_app, target: "settings"
  "play music" → pc_command, action: media_play
  "pause" → pc_command, action: media_pause
  "next song" → pc_command, action: media_next
  "volume up" → pc_command, action: volume_up
  "set volume to 30" → pc_command, action: set_volume, level: 30
  "take a screenshot" → pc_command, action: screenshot
  "lock screen" → pc_command, action: lock_screen
  "turn on focus mode" → pc_command, action: focus_mode
  "dark mode" → pc_command, action: toggle_dark_mode
  "open VS Code" → pc_command, action: open_app, target: "vscode"
  "open my documents folder" → pc_command, action: open_folder, target: "documents"

greeting — Conversational message. NOT a note. NOT a command.
  "hey" → greeting
  "hi there" → greeting
  "thanks" → greeting
  "thank you" → greeting
  "bye" → greeting
  "good morning" → greeting
  "what can you do?" → greeting
  "help" → greeting
  "never mind" → greeting
  "cool" → greeting
  "ok" → greeting

═══ RULES ═══
1. ONE intent per message. Pick the PRIMARY intent.
2. If truly unsure, default to create_note — saving is safer than losing.
3. query_notes = asking about THEIR notes. general_query = asking you to EXPLAIN/CALCULATE something.
4. "scratch that" / "undo" / "delete" → delete_note, NOT create_note.
5. DO NOT save greetings or "ok"/"cool"/"thanks" as notes.
6. "create a workspace" = switch_workspace. The system auto-creates if it doesn't exist.
7. Match workspace names fuzzily — "hackathon" matches "Hack Overflow".
8. spoken_response: 1-2 sentences max. Warm and natural. No corporate speak.
9. tags: reuse tags from the tag cloud when possible. 1-4 tags. Lowercase.
10. pc_actions must be EMPTY [] unless intent is pc_command.
11. For update_note: set "text" to the NEW content to add, "query" to identify WHICH note.
12. Whisper mishears things. "and meeting" = "end meeting". "it's to" = "switch to". Be smart about it.

User said: "{text}"

Respond with ONLY this JSON:
{{
  "intent": "<intent>",
  "confidence": <0.0-1.0>,
  "text": "<content if create_note or update_note, else null>",
  "query": "<search term if query_notes/general_query/update_note, else null>",
  "workspace": "<workspace name if switch_workspace, else null>",
  "tags": ["tag1", "tag2"],
  "spoken_response": "<brief chill spoken response>",
  "pc_actions": []
}}

If intent is pc_command, pc_actions format:
[{{"action": "<action_name>", "params": {{"target": "...", "level": 50}}}}]"""


# ═══════════════════════════════════════
#  CLASSIFICATION
# ═══════════════════════════════════════

async def classify(text: str, context: dict = None) -> dict:
    if context is None:
        context = {"active_workspace": "General"}

    prompt = build_prompt(text, context)

    raw = await provider.ask(
        prompt,
        temperature=0.1,
        json_mode=True,
        timeout=settings.TIMEOUT_INTENT,
    )

    parsed = provider.parse_json(raw)

    if parsed:
        return _validate(parsed, text)
    else:
        return _fallback(text)


# ═══════════════════════════════════════
#  VALIDATION
# ═══════════════════════════════════════

def _validate(parsed: dict, original_text: str) -> dict:

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
    if intent in ("create_note", "update_note") and not text:
        text = original_text

    # Query
    query = parsed.get("query")
    if query is not None and not isinstance(query, str):
        query = str(query)
    if intent in ("query_notes", "general_query") and not query:
        query = original_text
    if intent == "update_note" and not query:
        query = original_text

    # Workspace
    workspace = parsed.get("workspace")
    if workspace is not None and not isinstance(workspace, str):
        workspace = str(workspace)

    # Tags
    tags = parsed.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    seen = set()
    clean_tags = []
    for t in tags:
        t_clean = str(t).strip().lower()
        if t_clean and t_clean not in seen and len(t_clean) > 1:
            seen.add(t_clean)
            clean_tags.append(t_clean)
    tags = clean_tags[:5]

    # Spoken response
    spoken = parsed.get("spoken_response", "")
    if not isinstance(spoken, str) or not spoken.strip():
        spoken = _default_spoken(intent)

    # PC actions
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

        if not pc_actions:
            intent = "create_note"
            text = original_text
            spoken = "Wasn't sure what command you meant, saved it as a note."

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
    return {
        "intent": "create_note",
        "confidence": 0.3,
        "text": text,
        "query": None,
        "workspace": None,
        "tags": [],
        "spoken_response": "Saved that as a note just in case.",
        "pc_actions": [],
    }


def _default_spoken(intent: str) -> str:
    defaults = {
        "create_note": "Got it, noted.",
        "update_note": "Updated.",
        "query_notes": "Let me check.",
        "general_query": "Hmm, let me think.",
        "delete_note": "Deleted.",
        "switch_workspace": "Switching.",
        "list_workspaces": "Here are your workspaces.",
        "list_notes": "Here's what you've got.",
        "start_meeting": "Meeting started. Recording.",
        "end_meeting": "Meeting ended.",
        "pc_command": "Done.",
        "greeting": "Hey! What's up?",
    }
    return defaults.get(intent, "Done.")