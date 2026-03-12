import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import { useEffect } from 'react';
import {
  Bold, Italic, Strikethrough, Code, List, ListOrdered,
  Quote, CheckSquare, Heading1, Heading2, Minus, Type,
  Undo, Redo,
} from 'lucide-react';
import useNoteStore from '../../store/useNoteStore';

function ToolbarButton({ onClick, isActive, children, title }: any) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`p-2 rounded-xl transition-all duration-200 ${
        isActive
          ? 'bg-[#07beb8]/10 text-[#07beb8] shadow-sm'
          : 'text-slate-400 hover:bg-slate-100 hover:text-slate-700'
      }`}
    >
      {children}
    </button>
  );
}

function Divider() {
  return <div className="h-6 w-px bg-slate-200 mx-1" />;
}

export default function NoteEditor() {
  const notes = useNoteStore((s) => s.notes);
  const activeNoteId = useNoteStore((s) => s.activeNoteId);
  const updateNote = useNoteStore((s) => s.updateNote);

  const activeNote = notes.find((n) => n.id === activeNoteId);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: 'Start typing your thought...',
      }),
      TaskList,
      TaskItem.configure({ nested: true }),
    ],
    content: '',
    onUpdate: ({ editor }) => {
      if (activeNoteId) {
        updateNote(activeNoteId, { content: editor.getHTML() });
      }
    },
    editorProps: {
      attributes: {
        class: 'tiptap prose prose-slate max-w-none focus:outline-none min-h-[500px] pb-32 text-slate-600',
      },
    },
  });

  useEffect(() => {
    if (activeNote && editor) {
      const currentContent = editor.getHTML();
      if (activeNote.content !== currentContent && activeNote.content !== undefined) {
        editor.commands.setContent(activeNote.content || '');
      }
    }
  }, [activeNote?.id, activeNote?.content, editor]);

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (activeNoteId) {
      updateNote(activeNoteId, { title: e.target.value });
    }
  };

  if (!activeNote) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#f5fcfb] transition-colors duration-200 w-full h-full relative overflow-hidden">
        <div className="absolute top-0 right-0 -z-0 h-[600px] w-[600px] rounded-full bg-[#07beb8]/10 blur-[150px] pointer-events-none" />
        <div className="text-center relative z-10 p-12 glass-card rounded-3xl">
          <div className="w-20 h-20 bg-[#07beb8]/5 border border-slate-200 rounded-3xl flex items-center justify-center mx-auto mb-6">
            <Type className="w-10 h-10 text-[#07beb8]/50" />
          </div>
          <p className="text-slate-900 text-lg font-bold font-display">Select a note to start editing</p>
          <p className="text-slate-400 text-sm mt-2 font-light">Or create a new note from the sidebar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-[#f5fcfb] flex flex-col h-full overflow-hidden relative">
      <div className="absolute top-0 left-0 -z-0 h-[400px] w-[400px] rounded-full bg-[#07beb8]/10 blur-[120px] pointer-events-none" />

      {/* Toolbar */}
      <div className="glass-card m-4 md:m-8 rounded-2xl px-4 py-2 flex items-center gap-1 flex-wrap relative z-10 sticky top-4">
        <ToolbarButton onClick={() => editor?.chain().focus().undo().run()} title="Undo">
          <Undo className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().redo().run()} title="Redo">
          <Redo className="w-4 h-4" />
        </ToolbarButton>

        <Divider />

        <ToolbarButton onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()} isActive={editor?.isActive('heading', { level: 1 })} title="Heading 1">
          <Heading1 className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()} isActive={editor?.isActive('heading', { level: 2 })} title="Heading 2">
          <Heading2 className="w-4 h-4" />
        </ToolbarButton>

        <Divider />

        <ToolbarButton onClick={() => editor?.chain().focus().toggleBold().run()} isActive={editor?.isActive('bold')} title="Bold">
          <Bold className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().toggleItalic().run()} isActive={editor?.isActive('italic')} title="Italic">
          <Italic className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().toggleStrike().run()} isActive={editor?.isActive('strike')} title="Strikethrough">
          <Strikethrough className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().toggleCode().run()} isActive={editor?.isActive('code')} title="Inline Code">
          <Code className="w-4 h-4" />
        </ToolbarButton>

        <Divider />

        <ToolbarButton onClick={() => editor?.chain().focus().toggleBulletList().run()} isActive={editor?.isActive('bulletList')} title="Bullet List">
          <List className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().toggleOrderedList().run()} isActive={editor?.isActive('orderedList')} title="Numbered List">
          <ListOrdered className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().toggleTaskList().run()} isActive={editor?.isActive('taskList')} title="Task List">
          <CheckSquare className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().toggleBlockquote().run()} isActive={editor?.isActive('blockquote')} title="Quote">
          <Quote className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor?.chain().focus().setHorizontalRule().run()} title="Divider">
          <Minus className="w-4 h-4" />
        </ToolbarButton>

        <div className="ml-auto flex gap-2">
          {activeNote.tags.map((tag) => (
            <span key={tag} className="text-[10px] uppercase tracking-widest bg-[#07beb8]/10 border border-[#07beb8]/20 text-[#07beb8] px-3 py-1 rounded-full font-bold">
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto w-full max-w-4xl mx-auto px-8 md:px-16 pt-8 pb-32 relative z-10 custom-scrollbar">
        {/* Title Input */}
        <div className="mb-8">
          <input
            type="text"
            value={activeNote.title || ''}
            onChange={handleTitleChange}
            placeholder="Untitled Note"
            className="w-full text-5xl font-display font-extrabold bg-transparent text-slate-900 outline-none placeholder:text-slate-300 leading-tight tracking-tight focus:ring-0"
          />
          <div className="flex items-center gap-4 mt-4 text-xs font-bold tracking-widest uppercase text-slate-400">
            <span>
              {new Date(activeNote.createdAt).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </span>
            <div className="w-1 h-1 rounded-full bg-slate-300" />
            <span className="text-[#07beb8]/70">Thought Stream Active</span>
          </div>
        </div>

        {/* Editor Content */}
        <div className="editor-container">
          <EditorContent editor={editor} />
        </div>
      </div>
      
      <style>{`
        /* TipTap specific styles for light theme */
        .editor-container .ProseMirror p.is-editor-empty:first-child::before {
          color: #94a3b8;
          content: attr(data-placeholder);
          float: left;
          height: 0;
          pointer-events: none;
        }
        
        .editor-container .ProseMirror h1,
        .editor-container .ProseMirror h2,
        .editor-container .ProseMirror h3 {
          font-family: 'Manrope', 'Space Grotesk', system-ui, sans-serif;
          font-weight: 800;
          letter-spacing: -0.02em;
          color: #0f172a;
          margin-top: 1.5em;
          margin-bottom: 0.5em;
        }
        
        .editor-container .ProseMirror ul[data-type="taskList"] {
          list-style: none;
          padding: 0;
        }
        
        .editor-container .ProseMirror ul[data-type="taskList"] p {
          margin: 0;
        }
        
        .editor-container .ProseMirror ul[data-type="taskList"] li {
          display: flex;
          align-items: flex-start;
          margin-bottom: 0.5rem;
        }
        
        .editor-container .ProseMirror ul[data-type="taskList"] li > label {
          flex: 0 0 auto;
          margin-right: 0.75rem;
          user-select: none;
          margin-top: 0.25rem;
        }
        
        .editor-container .ProseMirror ul[data-type="taskList"] li > div {
          flex: 1 1 auto;
        }
        
        .editor-container .ProseMirror input[type="checkbox"] {
          appearance: none;
          background-color: white;
          margin: 0;
          font: inherit;
          color: currentColor;
          width: 1.15em;
          height: 1.15em;
          border: 1.5px solid #cbd5e1;
          border-radius: 0.25em;
          display: grid;
          place-content: center;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .editor-container .ProseMirror input[type="checkbox"]::before {
          content: "";
          width: 0.65em;
          height: 0.65em;
          transform: scale(0);
          transition: 120ms transform ease-in-out;
          box-shadow: inset 1em 1em white;
          background-color: white;
          transform-origin: center;
          clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
        }
        
        .editor-container .ProseMirror input[type="checkbox"]:checked {
          background-color: #07beb8;
          border-color: #07beb8;
        }
        
        .editor-container .ProseMirror input[type="checkbox"]:checked::before {
          transform: scale(1);
        }
        
        .editor-container .ProseMirror li[data-checked="true"] > div > p {
          color: #94a3b8;
          text-decoration: line-through;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.08);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.15);
        }

        .prose a {
          color: #07beb8;
          text-decoration: none;
          border-bottom: 1px solid rgba(7,190,184,0.3);
          transition: border-color 0.2s;
        }
        
        .prose a:hover {
          border-bottom-color: #07beb8;
        }
        
        .prose blockquote {
          border-left-color: #07beb8;
          background: linear-gradient(to right, rgba(7,190,184,0.08), transparent);
          padding: 1rem 1.5rem;
          border-radius: 0 0.5rem 0.5rem 0;
          font-style: normal;
          color: #475569;
        }
        
        .prose code {
          color: #07beb8;
          background: rgba(7,190,184,0.08);
          padding: 0.2em 0.4em;
          border-radius: 0.25rem;
          font-weight: 500;
        }
        
        .prose code::before,
        .prose code::after {
          display: none;
        }
      `}</style>
    </div>
  );
}
