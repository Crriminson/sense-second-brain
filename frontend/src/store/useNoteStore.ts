import { create } from 'zustand';
import { 
  fetchWorkspaces, 
  fetchNotes, 
  createNote, 
  updateNoteClient, 
  deleteNoteClient, 
  createWorkspaceClient, 
  switchWorkspaceClient,
  fetchActiveWorkspace,
  structureWorkspaceClient 
} from '../api/data';

export interface Workspace {
  id: string;
  name: string;
  createdAt: string;
}

export interface Note {
  id: string;
  workspaceId: string;
  title: string;
  content: string;
  tags: string[];
  createdAt: string;
}

interface NoteStoreState {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  notes: Note[];
  activeNoteId: string | null;
  isSidebarOpen: boolean;

  // Sync methods
  loadInitialData: () => Promise<void>;
  
  setActiveWorkspace: (id: string, name?: string) => Promise<void>;
  addWorkspace: (name: string) => Promise<void>;
  deleteWorkspace: (id: string) => void;

  setActiveNote: (id: string) => void;
  addNote: (title?: string) => Promise<void>;
  updateNote: (id: string, updates: Partial<Note>) => Promise<void>;
  deleteNote: (id: string) => Promise<void>;

  structureWorkspace: () => Promise<void>;

  toggleSidebar: () => void;
}

const useNoteStore = create<NoteStoreState>((set, get) => ({
  workspaces: [],
  activeWorkspaceId: null,

  // ── Notes ──
  notes: [],
  activeNoteId: null,

  isSidebarOpen: true,

  // ── Actions ──
  loadInitialData: async () => {
    try {
      const wss = await fetchWorkspaces();
      const activeWs = await fetchActiveWorkspace();
      const activeId = activeWs?.id || (wss[0]?.id ?? null);
      
      const convertedWss = wss.map(w => ({ id: w.id, name: w.name, createdAt: w.created_at }));
      set({ workspaces: convertedWss, activeWorkspaceId: activeId });
      
      if (activeId) {
        const backendNotes = await fetchNotes(activeId);
        const mappedNotes = backendNotes.map(n => ({
          id: n.id,
          workspaceId: n.workspace_id,
          title: n.summary || 'Untitled',
          content: n.raw_text,
          tags: n.tags || [],
          createdAt: n.created_at
        }));
        set((s) => {
          // Keep the currently active note if it still exists in the refreshed list
          const stillExists = mappedNotes.some(n => n.id === s.activeNoteId);
          // Only switch focus to mappedNotes[0] if the current note was deleted or we switched workspaces
          const nextActiveId = stillExists ? s.activeNoteId : (mappedNotes[0]?.id || null);
          return { notes: mappedNotes, activeNoteId: nextActiveId };
        });
      }
    } catch (e) {
      console.error("Failed to load initial data", e);
    }
  },

  setActiveWorkspace: async (id, name) => {
    set({ activeWorkspaceId: id, activeNoteId: null, notes: [] });
    try {
      if (name) await switchWorkspaceClient(name);
      
      const backendNotes = await fetchNotes(id);
      const mappedNotes = backendNotes.map(n => ({
        id: n.id,
        workspaceId: n.workspace_id,
        title: n.summary || 'Untitled',
        content: n.raw_text,
        tags: n.tags || [],
        createdAt: n.created_at
      }));
      set({ notes: mappedNotes, activeNoteId: mappedNotes[0]?.id || null });
    } catch (e) {
      console.error(e);
    }
  },

  addWorkspace: async (name) => {
    try {
      const ws = await createWorkspaceClient(name);
      set((s) => ({
        workspaces: [...s.workspaces, { id: ws.id, name: ws.name, createdAt: ws.created_at }],
      }));
      await get().setActiveWorkspace(ws.id, ws.name);
    } catch (e) {
      console.error(e);
    }
  },

  deleteWorkspace: (id) => {
    // Requires a backend endpoint, implementing optimistic update for now
    set((s) => ({
      workspaces: s.workspaces.filter((w) => w.id !== id),
      notes: s.notes.filter((n) => n.workspaceId !== id),
      activeWorkspaceId: s.activeWorkspaceId === id ? s.workspaces[0]?.id || null : s.activeWorkspaceId,
      activeNoteId: null,
    }));
  },

  setActiveNote: (id) => set({ activeNoteId: id }),

  addNote: async (title = 'Untitled') => {
    const { activeWorkspaceId } = get();
    if (!activeWorkspaceId) return;
    try {
      const backendNote = await createNote({ raw_text: '', summary: title, workspace_id: activeWorkspaceId });
      const note: Note = {
        id: backendNote.id,
        workspaceId: backendNote.workspace_id,
        title: backendNote.summary || title,
        content: backendNote.raw_text,
        tags: backendNote.tags,
        createdAt: backendNote.created_at
      };
      set((s) => ({
        notes: [note, ...s.notes],
        activeNoteId: note.id,
      }));
    } catch (e) {
      console.error(e);
    }
  },

  updateNote: async (id, updates) => {
    set((s) => ({
      notes: s.notes.map((n) => (n.id === id ? { ...n, ...updates } : n)),
    }));
    try {
      const patch: any = {};
      if (updates.content !== undefined) patch.raw_text = updates.content;
      if (updates.title !== undefined) patch.summary = updates.title;
      if (updates.tags !== undefined) patch.tags = updates.tags;
      await updateNoteClient(id, patch);
    } catch (e) {
      console.error(e);
    }
  },

  deleteNote: async (id) => {
    set((s) => ({
      notes: s.notes.filter((n) => n.id !== id),
      activeNoteId: s.activeNoteId === id ? null : s.activeNoteId,
    }));
    try {
      await deleteNoteClient(id);
    } catch (e) {
      console.error(e);
    }
  },

  structureWorkspace: async () => {
    const { activeWorkspaceId } = get();
    if (!activeWorkspaceId) return;

    try {
      // Create the structured document via backend
      const backendNote = await structureWorkspaceClient(activeWorkspaceId);
      
      const note: Note = {
        id: backendNote.id,
        workspaceId: backendNote.workspace_id,
        title: backendNote.summary || 'Structured Overview',
        content: backendNote.raw_text,
        tags: backendNote.tags,
        createdAt: backendNote.created_at
      };
      
      // Prepend to notes list and make it active
      set((s) => ({
        notes: [note, ...s.notes],
        activeNoteId: note.id,
      }));
    } catch (e) {
      console.error("Failed to structure workspace:", e);
    }
  },

  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
}));

export default useNoteStore;
