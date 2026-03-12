import { FileText, Plus, Search, Trash2, FolderPen } from 'lucide-react';
import useNoteStore from '../../store/useNoteStore';
import { useState } from 'react';

export default function NotesSidebar() {
  const notes = useNoteStore((s) => s.notes);
  const activeWorkspaceId = useNoteStore((s) => s.activeWorkspaceId);
  const activeNoteId = useNoteStore((s) => s.activeNoteId);
  const setActiveNote = useNoteStore((s) => s.setActiveNote);
  const addNote = useNoteStore((s) => s.addNote);
  const deleteNote = useNoteStore((s) => s.deleteNote);
  
  const workspaces = useNoteStore((s) => s.workspaces);
  const setActiveWorkspace = useNoteStore((s) => s.setActiveWorkspace);

  const [search, setSearch] = useState('');
  const [isWorkspaceMenuOpen, setIsWorkspaceMenuOpen] = useState(false);

  const activeWorkspace = workspaces.find(ws => ws.id === activeWorkspaceId);

  const workspaceNotes = notes
    .filter((n) => n.workspaceId === activeWorkspaceId)
    .filter((n) => n.title.toLowerCase().includes(search.toLowerCase()) || n.content.toLowerCase().includes(search.toLowerCase()));

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 86400000) {
      return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getPreview = (html: string) => {
    const text = html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    return text.length > 50 ? text.slice(0, 50) + '…' : text;
  };

  return (
    <div className="w-80 bg-white border-r border-slate-200/60 flex flex-col h-full shrink-0 z-20">
      {/* Workspace Selector */}
      <div className="p-4 border-b border-slate-200/60">
        <div className="flex items-center gap-2 mb-4 relative">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#07beb8]/5 border border-slate-200 shrink-0">
            <FolderPen size={16} className="text-[#07beb8]" />
          </div>
          
          <div className="flex-1 relative">
            <button
              onClick={() => setIsWorkspaceMenuOpen(!isWorkspaceMenuOpen)}
              className="w-full h-8 flex items-center justify-between bg-[#07beb8]/5 border border-[#07beb8]/10 text-slate-900 font-display font-black text-[10px] px-3 rounded-lg outline-none cursor-pointer uppercase tracking-[0.2em] transition-all hover:bg-[#07beb8]/10 hover:border-[#07beb8]/20 group"
            >
              <span className="truncate pr-2">{activeWorkspace?.name || 'Select Workspace'}</span>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="12" 
                height="12" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="3" 
                strokeLinecap="round" 
                strokeLinejoin="round"
                className={`text-[#07beb8]/50 group-hover:text-[#07beb8] transition-transform duration-300 ${isWorkspaceMenuOpen ? 'rotate-180' : ''}`}
              >
                <path d="m6 9 6 6 6-6"/>
              </svg>
            </button>

            {/* Custom Dropdown Menu */}
            {isWorkspaceMenuOpen && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setIsWorkspaceMenuOpen(false)} 
                />
                <div className="absolute top-full left-0 right-0 mt-2 z-50 bg-white border border-slate-200/60 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.08)] overflow-hidden animate-[slideDown_0.2s_ease-out]">
                  <div className="p-1.5 space-y-0.5">
                    <div className="px-3 py-2 text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">Workspaces</div>
                    {workspaces.map(ws => (
                      <button
                        key={ws.id}
                        onClick={() => {
                          setActiveWorkspace(ws.id);
                          setIsWorkspaceMenuOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition-all ${
                          activeWorkspaceId === ws.id
                            ? 'bg-[#07beb8] text-white'
                            : 'text-slate-600 hover:bg-[#07beb8]/5 hover:text-[#07beb8]'
                        }`}
                      >
                        <span className="text-[10px] font-bold uppercase tracking-widest">{ws.name}</span>
                        {activeWorkspaceId === ws.id && (
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-[#07beb8] transition-colors" />
          <input
            type="text"
            placeholder="Search notes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2 pl-9 pr-4 text-sm text-slate-800 outline-none placeholder:text-slate-400 focus:border-[#07beb8]/30 focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
          Notes ({workspaceNotes.length})
        </span>
        <button
          onClick={() => addNote()}
          className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-[#07beb8] hover:text-[#3dccc7] hover:bg-[#07beb8]/10 px-2 py-1 rounded-md transition-all"
        >
          <Plus className="w-3 h-3" />
          New
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1 custom-scrollbar">
        {workspaceNotes.length === 0 ? (
          <div className="text-center py-12 px-4 rounded-2xl border border-dashed border-slate-200 mt-4 mx-2">
            <FileText className="w-8 h-8 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500 font-medium mb-1">No notes found</p>
            <p className="text-xs text-slate-400 font-light">
              Create a new note to start capturing
            </p>
          </div>
        ) : (
          workspaceNotes.map((note) => {
            const isActive = activeNoteId === note.id;
            return (
              <div
                key={note.id}
                onClick={() => setActiveNote(note.id)}
                className={`group p-3 rounded-xl cursor-pointer transition-all duration-300 ${
                  isActive
                    ? 'bg-[#07beb8]/5 border border-[#07beb8]/20 shadow-sm'
                    : 'border border-transparent hover:bg-slate-50 hover:border-slate-200'
                }`}
              >
                <div className="flex items-start justify-between mb-1">
                  <h3
                    className={`text-sm font-bold font-display truncate pr-2 ${
                      isActive ? 'text-[#07beb8]' : 'text-slate-800 group-hover:text-slate-900'
                    }`}
                  >
                    {note.title || 'Untitled Note'}
                  </h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteNote(note.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-500 transition-all p-1 -mr-1 rounded-md hover:bg-rose-50"
                    title="Delete note"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed font-light">
                  {getPreview(note.content) || 'No content...'}
                </p>

                <div className="flex items-center justify-between mt-3 text-[10px] uppercase tracking-wider font-bold text-slate-400">
                  <span className={isActive ? 'text-[#07beb8]/70' : ''}>
                    {formatDate(note.createdAt)}
                  </span>
                  {note.tags.length > 0 && (
                    <span className="bg-slate-100 px-2 py-0.5 rounded-sm">
                      {note.tags.length} tag{note.tags.length !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.06);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.12);
        }
      `}</style>
    </div>
  );
}
