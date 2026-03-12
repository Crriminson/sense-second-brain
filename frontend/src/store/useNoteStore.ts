import { create } from 'zustand';

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

  setActiveWorkspace: (id: string) => void;
  addWorkspace: (name: string) => void;
  deleteWorkspace: (id: string) => void;

  setActiveNote: (id: string) => void;
  addNote: (title?: string) => void;
  updateNote: (id: string, updates: Partial<Note>) => void;
  deleteNote: (id: string) => void;

  toggleSidebar: () => void;
}

const useNoteStore = create<NoteStoreState>((set, get) => ({
  // ── Workspaces ──
  workspaces: [
    { id: 'ws-1', name: 'Personal Notes', createdAt: new Date().toISOString() },
    { id: 'ws-2', name: 'Work', createdAt: new Date().toISOString() },
  ],
  activeWorkspaceId: 'ws-1',

  // ── Notes ──
  notes: [
    {
      id: 'note-1',
      workspaceId: 'ws-1',
      title: 'Welcome to the New Editor',
      content: '<h2>A new way to capture thoughts</h2><p>This editor supports rich text, <strong>bold</strong>, <em>italics</em>, and task lists!</p><ul data-type="taskList"><li data-type="taskItem" data-checked="true"><label><input type="checkbox" checked="checked"><span></span></label><div><p>Porting from VersionB</p></div></li><li data-type="taskItem" data-checked="false"><label><input type="checkbox"><span></span></label><div><p>Make it look like Notion</p></div></li></ul>',
      tags: ['welcome'],
      createdAt: new Date().toISOString(),
    },
  ],
  activeNoteId: 'note-1',

  isSidebarOpen: true,

  // ── Actions ──
  setActiveWorkspace: (id) =>
    set({ activeWorkspaceId: id, activeNoteId: null }),

  addWorkspace: (name) => {
    const ws: Workspace = {
      id: `ws-${Date.now()}`,
      name,
      createdAt: new Date().toISOString(),
    };
    set((s) => ({
      workspaces: [...s.workspaces, ws],
      activeWorkspaceId: ws.id,
      activeNoteId: null,
    }));
  },

  deleteWorkspace: (id) =>
    set((s) => ({
      workspaces: s.workspaces.filter((w) => w.id !== id),
      notes: s.notes.filter((n) => n.workspaceId !== id),
      activeWorkspaceId:
        s.activeWorkspaceId === id
          ? s.workspaces[0]?.id || null
          : s.activeWorkspaceId,
      activeNoteId: null,
    })),

  setActiveNote: (id) => set({ activeNoteId: id }),

  addNote: (title = 'Untitled') => {
    const { activeWorkspaceId } = get();
    if (!activeWorkspaceId) return;
    const note: Note = {
      id: `note-${Date.now()}`,
      workspaceId: activeWorkspaceId,
      title,
      content: '',
      tags: [],
      createdAt: new Date().toISOString(),
    };
    set((s) => ({
      notes: [note, ...s.notes],
      activeNoteId: note.id,
    }));
  },

  updateNote: (id, updates) =>
    set((s) => ({
      notes: s.notes.map((n) => (n.id === id ? { ...n, ...updates } : n)),
    })),

  deleteNote: (id) =>
    set((s) => ({
      notes: s.notes.filter((n) => n.id !== id),
      activeNoteId: s.activeNoteId === id ? null : s.activeNoteId,
    })),

  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
}));

export default useNoteStore;
