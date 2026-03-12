from datetime import datetime
from typing import Literal
import json

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai import provider
from config import settings

router = APIRouter()


class IdeaPayload(BaseModel):
    id: str
    title: str
    summary: str
    expanded_idea: str
    action_items: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    importance_score: int = 5
    raw_transcript: str = ""
    timestamp: str = ""


class ProcessRequest(BaseModel):
    text: str


class ExpandRequest(BaseModel):
    idea: IdeaPayload


class InsightRequest(BaseModel):
    ideas: list[IdeaPayload]


class ConnectionsRequest(BaseModel):
    ideas: list[IdeaPayload]


def _process_locally(text: str) -> dict:
    words = [w for w in text.strip().split() if w]
    if not words:
        return {
            "title": "Untitled Idea",
            "summary": "",
            "expanded_idea": "",
            "action_items": [],
            "tags": ["idea"],
            "importance_score": 1,
        }

    title_words = words[: min(6, len(words))]
    title = " ".join([w[:1].upper() + w[1:] for w in title_words])
    if len(words) > 6:
        title += "..."

    stop_words = {
        "i", "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "at",
        "is", "it", "we", "my", "me", "for", "that", "this", "with", "be", "have",
        "so", "if", "could", "would", "should", "can", "will", "are", "was", "were",
        "about", "just", "some", "what", "there", "when", "how", "need", "want",
    }
    tags = []
    for raw in words:
        cleaned = "".join(ch for ch in raw.lower() if ch.isalnum())
        if len(cleaned) > 3 and cleaned not in stop_words and cleaned not in tags:
            tags.append(cleaned)
        if len(tags) >= 4:
            break

    importance = min(10, max(1, round(len(words) / 8) + 3))

    return {
        "title": title,
        "summary": text[:117] + "..." if len(text) > 120 else text,
        "expanded_idea": (
            f"You captured this thought: \"{text}\". Consider refining this idea further by "
            "exploring its potential impact, required resources, and how it connects to existing goals."
        ),
        "action_items": [
            "Review and refine this idea within 24 hours",
            "Share with a trusted colleague for feedback",
            "Research existing solutions or prior art",
        ],
        "tags": tags if tags else ["idea", "thought", "capture"],
        "importance_score": importance,
    }


def _expand_locally(idea: IdeaPayload) -> dict:
    return {
        "problem": (
            f"The core problem addressed by '{idea.title}' is a gap in existing solutions that creates "
            "friction or inefficiency for users. Current approaches are often too complex, too slow, "
            "or fail to address this need holistically."
        ),
        "proposed_solution": (
            "The proposed solution involves building a streamlined system that directly addresses the "
            "identified problem. By focusing on simplicity and effectiveness, it can deliver value "
            "quickly and iterate based on real user feedback."
        ),
        "target_users": (
            "Primary users are individuals or teams who frequently encounter this problem. They value "
            "efficiency, ease of use, and practical workflows."
        ),
        "potential_impact": (
            "If successful, this could save significant time and reduce cognitive overhead for the "
            "target audience. Widespread adoption could reshape how people approach this problem area."
        ),
        "business_opportunity": (
            "There is a clear opportunity to offer this as a SaaS product with subscription pricing. "
            "The productivity and automation market continues to grow, creating a viable path to revenue."
        ),
        "next_steps": [
            "Validate the core assumption with 5 potential users",
            "Build a minimum viable prototype in 1 week",
            "Define success metrics before launch",
            "Identify 3 competitors and analyze their weaknesses",
        ],
    }


def _insight_locally(ideas: list[IdeaPayload]) -> dict:
    if not ideas:
        return {
            "thinking_themes": ["reflection", "planning", "capture"],
            "most_promising_idea": "No ideas captured yet today.",
            "key_insight": "Start by capturing one concrete thought to unlock pattern detection and daily insight generation.",
            "suggested_next_steps": [
                "Capture your first idea of the day",
                "Tag it with the main topic",
                "Generate daily insight again",
            ],
        }

    tag_counts: dict[str, int] = {}
    for idea in ideas:
        for tag in idea.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    top_tags = [k for k, _ in sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)[:3]]
    best = max(ideas, key=lambda i: i.importance_score)

    return {
        "thinking_themes": top_tags if top_tags else ["productivity", "innovation", "problem-solving"],
        "most_promising_idea": f"\"{best.title}\" stands out with a score of {best.importance_score}/10. {best.summary}",
        "key_insight": (
            f"Today you captured {len(ideas)} idea{'s' if len(ideas) != 1 else ''}, showing strong momentum "
            f"in your thinking. Your focus gravitates toward {top_tags[0] if top_tags else 'creative problem-solving'} "
            "so a focused deep-work block could compound this quickly."
        ),
        "suggested_next_steps": [
            f"Deep-dive into '{best.title}' since it has the highest potential",
            "Block 30 minutes tomorrow to work on top action items",
            "Review older ideas to find cross-connections",
        ],
    }


def _connections_locally(ideas: list[IdeaPayload]) -> list[dict]:
    connections: list[dict] = []
    for i in range(len(ideas)):
        for j in range(i + 1, len(ideas)):
            idea_a = ideas[i]
            idea_b = ideas[j]

            shared_tags = [t for t in idea_a.tags if t in idea_b.tags]

            a_words = {
                w for w in (f"{idea_a.title} {idea_a.summary}").lower().split()
                if len(w) > 4
            }
            b_words = [
                w for w in (f"{idea_b.title} {idea_b.summary}").lower().split()
                if len(w) > 4
            ]
            shared_words = [w for w in b_words if w in a_words]
            score = len(shared_tags) * 2 + len(shared_words)

            if score >= 2:
                strength: Literal["strong", "moderate", "weak"]
                if score >= 5:
                    strength = "strong"
                elif score >= 3:
                    strength = "moderate"
                else:
                    strength = "weak"

                connector = (
                    f"shared themes of {' and '.join(shared_tags[:2])}"
                    if shared_tags
                    else "overlapping concepts"
                )
                connections.append(
                    {
                        "idea_a_id": idea_a.id,
                        "idea_b_id": idea_b.id,
                        "idea_a_title": idea_a.title,
                        "idea_b_title": idea_b.title,
                        "explanation": (
                            f"'{idea_a.title}' and '{idea_b.title}' are connected through {connector}, "
                            "suggesting they can be developed together."
                        ),
                        "strength": strength,
                    }
                )

    strength_order = {"strong": 0, "moderate": 1, "weak": 2}
    connections.sort(key=lambda item: strength_order[item["strength"]])
    return connections[:6]


@router.post("/process")
async def process_transcript(req: ProcessRequest):
    text = req.text.strip()
    if not text:
        return _process_locally("")

        prompt = """You are an expert at converting raw spoken thoughts into structured knowledge.
Given a raw transcript of a spoken idea, extract and return ONLY valid JSON with exactly these fields:
{{
    "title": "concise title (max 8 words)",
    "summary": "one-sentence summary (max 25 words)",
    "expanded_idea": "2-3 sentence elaboration",
    "action_items": ["specific actionable next step", "another next step"],
    "tags": ["relevant", "topic", "tags"],
    "importance_score": <integer 1-10>
}}

Raw transcript: "{text}""".format(text=text)

    raw = await provider.ask(
        prompt,
        temperature=0.4,
        json_mode=True,
        timeout=settings.TIMEOUT_SUMMARIZE,
    )
    parsed = provider.parse_json(raw)
    return parsed if parsed else _process_locally(text)


@router.post("/expand")
async def expand_idea(req: ExpandRequest):
    idea = req.idea
    prompt = """You are a senior product strategist and entrepreneur. Given a captured idea, expand it into a detailed structured analysis.
Return ONLY valid JSON with exactly these fields:
{{
    "problem": "2-3 sentences",
    "proposed_solution": "2-3 sentences",
    "target_users": "1-2 sentences",
    "potential_impact": "2 sentences",
    "business_opportunity": "2 sentences",
    "next_steps": ["Immediate first action", "Second step", "Third step", "Fourth step"]
}}

Idea Title: {title}
Summary: {summary}
Original Thought: {raw}
Expanded Idea: {expanded}
Tags: {tags}""".format(
        title=idea.title,
        summary=idea.summary,
        raw=idea.raw_transcript,
        expanded=idea.expanded_idea,
        tags=", ".join(idea.tags),
    )

    raw = await provider.ask(
        prompt,
        temperature=0.6,
        json_mode=True,
        timeout=settings.TIMEOUT_ANSWER,
    )
    parsed = provider.parse_json(raw)
    return parsed if parsed else _expand_locally(idea)


@router.post("/insight")
async def generate_insight(req: InsightRequest):
    ideas = req.ideas
    if not ideas:
        local = _insight_locally([])
    else:
        ideas_summary = []
        for idx, idea in enumerate(ideas, start=1):
            ideas_summary.append(
                f"{idx}. '{idea.title}' (score: {idea.importance_score}/10)\\n"
                f"   Summary: {idea.summary}\\n"
                f"   Tags: {', '.join(idea.tags)}"
            )
        prompt = """You are a thoughtful personal thinking coach and strategist. Analyze a collection of ideas captured today and generate a reflective daily insight.
Return ONLY valid JSON with exactly these fields:
{
  "thinking_themes": ["theme 1", "theme 2", "theme 3"],
  "most_promising_idea": "Name and brief reason why this idea stands out (2 sentences)",
  "key_insight": "A deep observation about the user's thinking patterns today (2-3 sentences)",
  "suggested_next_steps": ["Actionable step 1", "Actionable step 2", "Actionable step 3"]
}

Here are ideas captured today:
""" + "\n\n".join(ideas_summary)

        raw = await provider.ask(
            prompt,
            temperature=0.7,
            json_mode=True,
            timeout=settings.TIMEOUT_ANSWER,
        )
        parsed = provider.parse_json(raw)
        local = parsed if parsed else _insight_locally(ideas)

    local["date"] = datetime.now().strftime("%a %b %d %Y")
    local["generated_at"] = datetime.utcnow().isoformat() + "Z"
    return local


@router.post("/connections")
async def detect_connections(req: ConnectionsRequest):
    ideas = req.ideas
    if len(ideas) < 2:
        return []

    ideas_payload = [
        {
            "id": idea.id,
            "title": idea.title,
            "summary": idea.summary,
            "tags": idea.tags,
            "expanded_idea": idea.expanded_idea,
        }
        for idea in ideas
    ]

    prompt = """You are an expert knowledge graph analyst. Analyze a set of ideas and identify meaningful connections between them.
Return ONLY valid JSON with this exact shape:
{{
    "connections": [
        {{
            "idea_a_id": "id",
            "idea_b_id": "id",
            "idea_a_title": "title",
            "idea_b_title": "title",
            "explanation": "one sentence",
            "strength": "strong|moderate|weak"
        }}
    ]
}}

Only include genuinely meaningful links. Max 6.

Ideas:
{ideas}""".format(ideas=json.dumps(ideas_payload, ensure_ascii=True))

    raw = await provider.ask(
        prompt,
        temperature=0.5,
        json_mode=True,
        timeout=settings.TIMEOUT_ANSWER,
    )
    parsed = provider.parse_json(raw)

    if parsed and isinstance(parsed.get("connections"), list):
        return parsed["connections"]
    return _connections_locally(ideas)


@router.post("/message")
async def send_message(req: ProcessRequest):
    processed = await process_transcript(req)
    return {"response": processed}


@router.get("/status")
async def status():
    return {"status": "ok"}
