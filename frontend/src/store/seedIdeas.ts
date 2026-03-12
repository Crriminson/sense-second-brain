import { ideaStore, Idea } from "./ideas";

// Use a versioned key — bump version to re-seed after schema changes
const SEED_KEY = "thoughtcapture_seeded_v2";

const seedData: Idea[] = [
  {
    id: "seed-1",
    title: "AI-Powered Meeting Summarizer",
    summary: "Build a tool that auto-summarizes Zoom calls and extracts action items.",
    expanded_idea:
      "This tool would plug into meeting platforms like Zoom or Google Meet, transcribe audio in real time, and use a language model to generate a structured summary with decisions made, open questions, and assigned action items. It could integrate with Slack or email to distribute the notes automatically.",
    action_items: [
      "Research Zoom and Google Meet webhook APIs",
      "Design the action-item extraction prompt",
      "Build a Slack bot for distribution",
    ],
    tags: ["ai", "productivity", "meetings", "automation"],
    importance_score: 9,
    raw_transcript:
      "What if there was a tool that listened to all your meetings and just automatically wrote up the summary and sent it to everyone? That would save like an hour a day.",
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    is_expanded: false,
  },
  {
    id: "seed-2",
    title: "Offline-First Recipe App",
    summary: "A mobile recipe app that works fully offline with smart pantry tracking.",
    expanded_idea:
      "Users log what's in their pantry, and the app suggests recipes they can make right now without a grocery run. The app syncs recipes and pantry state via a lightweight CRDT layer, ensuring it works seamlessly even with no internet connection.",
    action_items: [
      "Prototype pantry tracking UI in Figma",
      "Evaluate CRDTs: Automerge vs Yjs",
      "Source a free recipe API for initial content",
    ],
    tags: ["mobile", "offline", "food", "ux"],
    importance_score: 6,
    raw_transcript:
      "I keep opening recipe apps when I'm in the kitchen and they don't load because the wifi is bad. Would be great if it just worked offline and also told me what I could cook with what's already in the fridge.",
    timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    is_expanded: false,
  },
  {
    id: "seed-3",
    title: "Spaced Repetition for Code Snippets",
    summary: "Anki-style flashcard system for developers to retain useful code patterns.",
    expanded_idea:
      "Developers often look up the same syntax patterns repeatedly. A spaced-repetition tool tailored for code would let engineers bookmark snippets, then quiz them with fill-in-the-blank exercises scheduled by a forgetting-curve algorithm. IDE plugins could surface forgotten snippets contextually.",
    action_items: [
      "Implement SM-2 spaced repetition algorithm",
      "Design the VS Code extension integration",
      "Create a snippet import flow from GitHub Gists",
    ],
    tags: ["developer-tools", "learning", "productivity"],
    importance_score: 8,
    raw_transcript:
      "I look up the same regex syntax or array method every single week. There should be something like Anki but for code snippets, with the spaced repetition thing.",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    is_expanded: false,
  },
];

export function seedDemoIdeas(): void {
  if (typeof window === "undefined") return;
  // Only seed once per browser (persisted in localStorage)
  if (localStorage.getItem(SEED_KEY)) return;
  // Add in reverse so newest appears first after sort
  [...seedData].reverse().forEach((idea) => ideaStore.add(idea));
  localStorage.setItem(SEED_KEY, "1");
}
