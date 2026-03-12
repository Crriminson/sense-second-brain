/// <reference types="vite/client" />
import { Idea, IdeaExpansion, IdeaConnection, DailyInsight } from "../store/ideas";

const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const API_PREFIX = "/api";

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20000);

  try {
    const res = await fetch(`${BACKEND_URL}${API_PREFIX}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      throw new Error(`Request failed: ${res.status}`);
    }
    return (await res.json()) as T;
  } finally {
    window.clearTimeout(timeout);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. PROCESS TRANSCRIPT → Structured Idea
// ─────────────────────────────────────────────────────────────────────────────

function processLocally(
  text: string
): Omit<Idea, "id" | "raw_transcript" | "timestamp"> {
  const words = text.trim().split(/\s+/);
  const titleWords = words.slice(0, Math.min(6, words.length));
  const title =
    titleWords.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ") +
    (words.length > 6 ? "…" : "");

  const stopWords = new Set([
    "i", "the", "a", "an", "and", "or", "but", "to", "of", "in", "on", "at",
    "is", "it", "we", "my", "me", "for", "that", "this", "with", "be", "have",
    "so", "if", "could", "would", "should", "can", "will", "are", "was", "were",
    "about", "just", "some", "what", "there", "when", "how", "need", "want",
  ]);
  const tagCandidates = words
    .map((w) => w.toLowerCase().replace(/[^a-z0-9]/g, ""))
    .filter((w) => w.length > 3 && !stopWords.has(w));
  const uniqueTags = [...new Set(tagCandidates)].slice(0, 4);
  const importance = Math.min(10, Math.max(1, Math.round(words.length / 8) + 3));

  return {
    title,
    summary: text.length > 120 ? text.slice(0, 117) + "…" : text,
    expanded_idea: `You captured this thought: "${text}". Consider refining this idea further by exploring its potential impact, required resources, and how it connects to your existing goals.`,
    action_items: [
      "Review and refine this idea within 24 hours",
      "Share with a trusted colleague for feedback",
      "Research existing solutions or prior art",
    ],
    tags: uniqueTags.length > 0 ? uniqueTags : ["idea", "thought", "capture"],
    importance_score: importance,
  };
}

export async function processTranscript(
  text: string
): Promise<Omit<Idea, "id" | "raw_transcript" | "timestamp">> {
  try {
    return await postJSON<Omit<Idea, "id" | "raw_transcript" | "timestamp">>("/process", { text });
  } catch (err) {
    console.warn("Backend processing failed, falling back to local:", err);
  }
  return processLocally(text);
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. EXPAND IDEA → Deep structured breakdown
// ─────────────────────────────────────────────────────────────────────────────

function expandLocally(idea: Idea): IdeaExpansion {
  return {
    problem: `The core problem addressed by "${idea.title}" is a gap in existing solutions that creates friction or inefficiency for users. Current approaches are either too complex, too slow, or fail to address this need holistically.`,
    proposed_solution: `The proposed solution involves building a streamlined system that directly addresses the identified problem. By focusing on simplicity and effectiveness, it can deliver value quickly and iterate based on real user feedback.`,
    target_users: `Primary users are individuals or teams who frequently encounter the problem described in this idea. They value efficiency, ease-of-use, and solutions that integrate into their existing workflows.`,
    potential_impact: `If successful, this could save significant time and reduce cognitive overhead for the target audience. Widespread adoption could shift how people approach this category of problem entirely.`,
    business_opportunity: `There is a clear opportunity to offer this as a SaaS product with subscription pricing. The market for productivity and automation tools continues to grow, offering a viable path to revenue.`,
    next_steps: [
      "Validate the core assumption with 5 potential users",
      "Build a minimum viable prototype in 1 week",
      "Define success metrics before launch",
      "Identify 3 competitors and analyze their weaknesses",
    ],
  };
}

export async function expandIdea(idea: Idea): Promise<IdeaExpansion> {
  try {
    return await postJSON<IdeaExpansion>("/expand", { idea });
  } catch (err) {
    console.warn("Backend expansion failed, falling back to local:", err);
  }
  return expandLocally(idea);
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. DAILY INSIGHT GENERATOR
// ─────────────────────────────────────────────────────────────────────────────

function generateInsightLocally(
  ideas: Idea[]
): Omit<DailyInsight, "date" | "generated_at"> {
  const allTags = ideas.flatMap((i) => i.tags);
  const tagCounts: Record<string, number> = {};
  allTags.forEach((t) => {
    tagCounts[t] = (tagCounts[t] ?? 0) + 1;
  });
  const topTags = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([t]) => t);

  const best = ideas.reduce((a, b) =>
    b.importance_score > a.importance_score ? b : a
  );

  return {
    thinking_themes: topTags.length > 0 ? topTags : ["productivity", "innovation", "problem-solving"],
    most_promising_idea: `"${best.title}" stands out with a score of ${best.importance_score}/10. ${best.summary}`,
    key_insight: `Today you captured ${ideas.length} idea${ideas.length !== 1 ? "s" : ""}, showing strong momentum in your thinking. Your focus gravitates toward ${topTags[0] ?? "creative problem-solving"} — consider dedicating dedicated time to develop these further.`,
    suggested_next_steps: [
      `Deep-dive into "${best.title}" — it has the highest potential`,
      "Block 30 minutes tomorrow to work on your top action items",
      "Review yesterday's ideas to find cross-connections",
    ],
  };
}

export async function generateDailyInsight(ideas: Idea[]): Promise<DailyInsight> {
  try {
    return await postJSON<DailyInsight>("/insight", { ideas });
  } catch (err) {
    console.warn("Backend insight failed, falling back:", err);
    return {
      ...generateInsightLocally(ideas),
      date: new Date().toDateString(),
      generated_at: new Date().toISOString(),
    };
  }
}

export async function analyzeConnections(ideas: Idea[]): Promise<IdeaConnection[]> {
  if (ideas.length < 2) return [];
  return await postJSON<IdeaConnection[]>("/connections", { ideas });
}
