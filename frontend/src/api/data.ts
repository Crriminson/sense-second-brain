import { Idea } from "../store/ideas";

const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const API_PREFIX = "/api";

export interface BackendWorkspace {
  id: string;
  name: string;
  is_active: number;
  created_at: string;
}

export interface BackendNote {
  id: string;
  workspace_id: string;
  workspace_name?: string;
  raw_text: string;
  summary: string | null;
  tags: string[];
  source: string;
  created_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export function mapNoteToIdea(note: BackendNote): Idea {
  const clean = (note.raw_text ?? "").trim();
  const fallbackTitle = clean.length > 0 ? clean.split(/\s+/).slice(0, 6).join(" ") : "Untitled";
  const title = (note.summary?.trim() || fallbackTitle).slice(0, 80);

  return {
    id: note.id,
    title,
    summary: note.summary?.trim() || (clean.length > 120 ? `${clean.slice(0, 117)}...` : clean),
    expanded_idea: clean,
    action_items: [],
    tags: Array.isArray(note.tags) ? note.tags : [],
    importance_score: 5,
    raw_transcript: clean,
    timestamp: note.created_at,
    is_expanded: false,
  };
}

export async function fetchNotes(workspaceId?: string): Promise<BackendNote[]> {
  const qs = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : "";
  return request<BackendNote[]>(`/notes${qs}`);
}

export async function createNote(input: {
  raw_text: string;
  summary?: string;
  tags?: string[];
  workspace_id?: string;
  source?: string;
}): Promise<BackendNote> {
  return request<BackendNote>("/notes", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function deleteAllNotes(workspaceId?: string): Promise<{ deleted: number }> {
  const qs = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : "";
  return request<{ deleted: number }>(`/notes${qs}`, { method: "DELETE" });
}

export async function fetchWorkspaces(): Promise<BackendWorkspace[]> {
  return request<BackendWorkspace[]>("/workspaces");
}

export async function fetchActiveWorkspace(): Promise<BackendWorkspace | null> {
  return request<BackendWorkspace | null>("/workspaces/active");
}
