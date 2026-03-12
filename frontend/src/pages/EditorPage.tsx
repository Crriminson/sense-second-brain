import { Link } from 'react-router-dom';
import NotesSidebar from '../components/editor/NotesSidebar';
import NoteEditor from '../components/editor/NoteEditor';
import { LayoutGrid, PanelLeftClose, PanelLeft, Mic } from 'lucide-react';
import useNoteStore from '../store/useNoteStore';

export default function EditorPage() {
  const isSidebarOpen = useNoteStore((s) => s.isSidebarOpen);
  const toggleSidebar = useNoteStore((s) => s.toggleSidebar);

  return (
    <div className="flex h-screen bg-[#f0faf9] text-slate-700 overflow-hidden font-sans">
      {/* Sidebar */}
      <div 
        className={`transition-all duration-300 ease-in-out shrink-0 overflow-hidden ${
          isSidebarOpen ? 'w-80 opacity-100' : 'w-0 opacity-0 pointer-events-none'
        }`}
      >
        <NotesSidebar />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative z-10">
        {/* Editor Top Bar */}
        <header className="absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-4 lg:px-6 bg-white/30 backdrop-blur-xl border-b border-slate-200/50 z-50">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleSidebar}
              className="p-2 -ml-2 rounded-xl text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition-colors group"
              title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
            >
              {isSidebarOpen ? (
                <PanelLeftClose size={20} className="group-hover:text-[#07beb8] transition-colors" />
              ) : (
                <PanelLeft size={20} className="group-hover:text-[#07beb8] transition-colors" />
              )}
            </button>
            <div className="h-6 w-px bg-slate-200" />
            <Link to="/dashboard" className="flex items-center gap-2 group text-slate-500 hover:text-slate-800 transition-colors">
              <LayoutGrid size={18} className="group-hover:text-[#07beb8] transition-colors" />
              <span className="text-sm font-bold uppercase tracking-wider hidden sm:inline">Dashboard</span>
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/capture"
              className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-bold uppercase tracking-widest text-[#07beb8] transition-all hover:bg-[#07beb8]/10 hover:border-[#07beb8]/30 shadow-sm"
            >
              <Mic size={14} />
              <span>Capture Idea</span>
            </Link>
          </div>
        </header>

        {/* Editor Wrapper */}
        <main className="flex-1 overflow-hidden flex flex-col relative pt-16">
          <NoteEditor />
        </main>
      </div>
    </div>
  );
}
