// ─── Types ────────────────────────────────────────────────────────────────────

export interface IdeaExpansion {
  problem: string;
  proposed_solution: string;
  target_users: string;
  potential_impact: string;
  business_opportunity: string;
  next_steps: string[];
}

export interface Idea {
  id: string;
  title: string;
  summary: string;
  expanded_idea: string;
  action_items: string[];
  tags: string[];
  importance_score: number;
  raw_transcript: string;
  timestamp: string;
  workspace_id?: string;
  workspace_name?: string;
  // V2 fields
  expansion?: IdeaExpansion;
  is_expanded?: boolean;
}

export interface IdeaConnection {
  idea_a_id: string;
  idea_b_id: string;
  idea_a_title: string;
  idea_b_title: string;
  explanation: string;
  strength: "strong" | "moderate" | "weak";
}

export interface DailyInsight {
  date: string;
  thinking_themes: string[];
  most_promising_idea: string;
  key_insight: string;
  suggested_next_steps: string[];
  generated_at: string;
}

// ─── Storage helpers ───────────────────────────────────────────────────────────

const STORAGE_KEY = "thoughtcapture_ideas_v2";
const INSIGHT_KEY = "thoughtcapture_daily_insight_v2";

function loadFromStorage(): Idea[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveToStorage(ideas: Idea[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ideas));
  } catch (e) {
    console.warn("Failed to persist ideas to localStorage:", e);
  }
}

function loadDailyInsight(): DailyInsight | null {
  try {
    const raw = localStorage.getItem(INSIGHT_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as DailyInsight;
  } catch {
    return null;
  }
}

function saveDailyInsight(insight: DailyInsight): void {
  try {
    localStorage.setItem(INSIGHT_KEY, JSON.stringify(insight));
  } catch {}
}

// ─── Store class ───────────────────────────────────────────────────────────────

class IdeaStore {
  private ideas: Idea[] = loadFromStorage();
  private connections: IdeaConnection[] = [];
  private listeners: Array<() => void> = [];

  // ── Ideas ──────────────────────────────────────────────────────────────────

  getAll(): Idea[] {
    return [...this.ideas].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }

  getById(id: string): Idea | undefined {
    return this.ideas.find((i) => i.id === id);
  }

  getTodayIdeas(): Idea[] {
    const today = new Date().toDateString();
    return this.ideas.filter(
      (i) => new Date(i.timestamp).toDateString() === today
    );
  }

  add(idea: Idea): void {
    // Avoid duplicates (e.g. seed re-runs)
    if (this.ideas.find((i) => i.id === idea.id)) return;
    this.ideas.unshift(idea);
    saveToStorage(this.ideas);
    this.notify();
  }

  update(id: string, patch: Partial<Idea>): void {
    const idx = this.ideas.findIndex((i) => i.id === id);
    if (idx === -1) return;
    this.ideas[idx] = { ...this.ideas[idx], ...patch };
    saveToStorage(this.ideas);
    this.notify();
  }

  remove(id: string): void {
    this.ideas = this.ideas.filter((i) => i.id !== id);
    saveToStorage(this.ideas);
    this.notify();
  }

  clear(): void {
    this.ideas = [];
    this.connections = [];
    saveToStorage([]);
    this.notify();
  }

  // ── Daily Insight ──────────────────────────────────────────────────────────

  getDailyInsight(): DailyInsight | null {
    return loadDailyInsight();
  }

  setDailyInsight(insight: DailyInsight): void {
    saveDailyInsight(insight);
    this.notify();
  }

  // ── Connections ────────────────────────────────────────────────────────────

  getConnections(): IdeaConnection[] {
    return [...this.connections];
  }

  setConnections(connections: IdeaConnection[]): void {
    this.connections = [...connections];
    this.notify();
  }

  // ── Pub/sub ────────────────────────────────────────────────────────────────

  subscribe(fn: () => void): () => void {
    this.listeners.push(fn);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== fn);
    };
  }

  private notify(): void {
    this.listeners.forEach((fn) => fn());
  }
}

export const ideaStore = new IdeaStore();
