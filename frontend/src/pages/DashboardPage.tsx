import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { ideaStore, Idea } from "../store/ideas";
import IdeaCard from "../components/IdeaCard";
import DailyInsightPanel from "../components/DailyInsightPanel";
import ConnectionsPanel from "../components/ConnectionsPanel";
import {
  Zap,
  Mic,
  Search,
  SlidersHorizontal,
  Inbox,
  TrendingUp,
  Tag,
  BarChart3,
  Brain,
  Sparkles,
  GitBranch,
  LayoutGrid,
  Star,
  Trash2,
} from "lucide-react";

type SortKey = "timestamp" | "importance_score";
type FilterTag = string | null;
type ActiveTab = "ideas" | "insights" | "connections";

// ─── Stats Bar ────────────────────────────────────────────────────────────────

function StatsBar({ ideas }: { ideas: Idea[] }) {
  const avg =
    ideas.length > 0
      ? (ideas.reduce((s, i) => s + i.importance_score, 0) / ideas.length).toFixed(1)
      : "—";
  const allTags = ideas.flatMap((i) => i.tags);
  const uniqueTags = new Set(allTags).size;
  const highPriority = ideas.filter((i) => i.importance_score >= 8).length;
  const expandedCount = ideas.filter((i) => i.is_expanded).length;
  const todayCount = ideas.filter(
    (i) => new Date(i.timestamp).toDateString() === new Date().toDateString()
  ).length;

  const stats = [
    { icon: <BarChart3 size={20} />, label: "Total Ideas", value: ideas.length },
    { icon: <TrendingUp size={20} />, label: "Avg Score", value: avg },
    { icon: <Tag size={20} />, label: "Unique Tags", value: uniqueTags },
    { icon: <Sparkles size={20} />, label: "Expanded", value: expandedCount },
    { icon: <Star size={20} />, label: "High Priority", value: highPriority },
    { icon: <Zap size={20} />, label: "Today", value: todayCount },
  ];

  return (
    <section className="flex overflow-x-auto gap-6 sm:gap-8 pb-10 no-scrollbar animate-[fadeIn_0.5s_ease-out_forwards]">
      {stats.map(({ icon, label, value }) => (
        <div
          key={label}
          className="glass-card min-w-[160px] flex-1 p-6 rounded-3xl flex flex-col gap-2 hover:border-[#07beb8]/40 transition-colors group"
        >
          <div className="text-[#07beb8] mb-2 opacity-80 group-hover:scale-110 group-hover:opacity-100 transition-all">{icon}</div>
          <div className="font-display text-4xl font-extrabold text-slate-900 leading-none tracking-tight">{value}</div>
          <div className="text-[11px] uppercase tracking-[0.15em] text-slate-500 font-bold mt-2">{label}</div>
        </div>
      ))}
    </section>
  );
}

// ─── Tab Bar ──────────────────────────────────────────────────────────────────

function TabBar({
  active,
  onChange,
  ideas,
}: {
  active: ActiveTab;
  onChange: (t: ActiveTab) => void;
  ideas: Idea[];
}) {
  const connectionCount = ideaStore.getConnections().length;
  const insight = ideaStore.getDailyInsight();
  const hasInsightToday = insight?.date === new Date().toDateString();

  const tabs: { id: ActiveTab; icon: React.ReactNode; label: string; badge?: string }[] = [
    {
      id: "ideas",
      icon: <LayoutGrid size={18} />,
      label: "Recent Thoughts",
      badge: ideas.length > 0 ? String(ideas.length) : undefined,
    },
    {
      id: "insights",
      icon: <Brain size={18} />,
      label: "Daily Insight",
      badge: hasInsightToday ? "✓" : undefined,
    },
    {
      id: "connections",
      icon: <GitBranch size={18} />,
      label: "Connections",
      badge: connectionCount > 0 ? String(connectionCount) : undefined,
    },
  ];

  return (
    <div className="flex gap-2 rounded-2xl glass-card p-2 mb-10 mx-auto max-w-fit">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`group flex items-center justify-center gap-3 rounded-xl px-6 py-4 text-sm font-bold uppercase tracking-wider transition-all duration-300 ${active === tab.id
            ? "bg-[#07beb8] text-white shadow-[0_0_20px_rgba(7,190,184,0.2)]"
            : "text-slate-500 hover:text-slate-800 hover:bg-slate-100"
            }`}
        >
          <span className={`transition-transform duration-300 ${active === tab.id ? "scale-110" : "group-hover:scale-110"}`}>{tab.icon}</span>
          <span className="hidden sm:inline">{tab.label}</span>
          {tab.badge && (
            <span
              className={`rounded-full px-2.5 py-1 text-[10px] font-black leading-none ${active === tab.id
                ? "bg-white/20 text-white"
                : "bg-slate-200 text-slate-600 group-hover:bg-slate-300"
                }`}
            >
              {tab.badge}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [ideas, setIdeas] = useState<Idea[]>(ideaStore.getAll());
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("timestamp");
  const [filterTag, setFilterTag] = useState<FilterTag>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("ideas");

  useEffect(() => {
    const unsub = ideaStore.subscribe(() => {
      setIdeas(ideaStore.getAll());
    });
    return unsub;
  }, []);

  const allTags = [...new Set(ideas.flatMap((i) => i.tags))].slice(0, 12);

  const displayed = ideas
    .filter((idea) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        idea.title.toLowerCase().includes(q) ||
        idea.summary.toLowerCase().includes(q) ||
        idea.tags.some((t) => t.toLowerCase().includes(q));
      const matchTag = !filterTag || idea.tags.includes(filterTag);
      return matchSearch && matchTag;
    })
    .sort((a, b) => {
      if (sortKey === "importance_score") return b.importance_score - a.importance_score;
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });

  return (
    <div className="min-h-screen bg-adnia bg-dots text-slate-700 pb-32">
      {/* ── Top Nav ── */}
      <header className="fixed top-0 z-50 w-full bg-white/30 backdrop-blur-2xl border-b border-slate-200/50">
        <div className="mx-auto flex items-center justify-between gap-4 max-w-screen-2xl px-6 lg:px-12 py-5">
          <Link to="/" className="flex items-center gap-4 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#07beb8]/10 border border-[#07beb8]/20 transition-transform group-hover:scale-105">
              <span className="text-[#07beb8] font-display font-extrabold text-xl">TC</span>
            </div>
            <div>
              <h1 className="font-display font-bold text-xl leading-none text-slate-900 transition-colors group-hover:text-slate-700">ThoughtCapture</h1>
              <span className="mt-1 block text-[10px] uppercase tracking-[0.2em] text-[#07beb8] font-bold">Dashboard</span>
            </div>
          </Link>

          <div className="flex items-center gap-4">
            {ideas.length > 0 && (
              <button
                onClick={() => {
                  if (confirm("Clear all ideas? This cannot be undone.")) {
                    ideaStore.clear();
                  }
                }}
                className="group flex items-center justify-center h-12 w-12 rounded-full border border-slate-200 bg-white text-slate-400 transition-all hover:border-rose-400 hover:bg-rose-50 hover:text-rose-500 shadow-sm"
                title="Clear All Ideas"
              >
                <Trash2 size={20} className="transition-transform group-hover:scale-110" />
              </button>
            )}
            <Link
              to="/editor"
              className="flex items-center gap-2 rounded-full border border-[#07beb8]/20 bg-[#07beb8]/5 px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-[#07beb8] transition-all hover:bg-[#07beb8]/10 hover:border-[#07beb8]/40"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 Z"></path></svg>
              <span className="hidden sm:inline">Note Editor</span>
            </Link>
            <Link
              to="/capture"
              className="btn-primary"
            >
              <Mic size={18} />
              <span className="hidden sm:inline">New Capture</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-screen-2xl px-6 lg:px-12 pt-36 relative z-10">
        {/* Dynamic decorative blobs */}
        <div className="absolute top-0 right-0 -z-10 h-[600px] w-[600px] rounded-full bg-[#07beb8]/10 blur-[150px] pointer-events-none" />

        {/* Stats */}
        {ideas.length > 0 && <StatsBar ideas={ideas} />}

        {/* Tab navigation */}
        <TabBar active={activeTab} onChange={setActiveTab} ideas={ideas} />

        {/* ── IDEAS TAB ── */}
        {activeTab === "ideas" && (
          <div className="animate-[slideUp_0.5s_ease-out_forwards]">
            {/* Search & Sort */}
            <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-center">
              <div className="relative flex-1 group">
                <Search
                  size={20}
                  className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400 transition-colors group-focus-within:text-[#07beb8]"
                />
                <input
                  type="text"
                  placeholder="Search thoughts, insights, neural tags..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full rounded-full border border-slate-200 bg-white py-4 pl-14 pr-6 text-base text-slate-800 outline-none placeholder-slate-400 shadow-sm transition-all focus:border-[#07beb8]/50 focus:shadow-[0_0_20px_rgba(7,190,184,0.1)]"
                />
              </div>
              <div className="flex items-center gap-4 rounded-full border border-slate-200 bg-white p-2 shadow-sm">
                <div className="pl-4">
                  <SlidersHorizontal size={18} className="text-slate-400" />
                </div>
                <select
                  value={sortKey}
                  onChange={(e) => setSortKey(e.target.value as SortKey)}
                  className="bg-transparent pr-6 py-2 text-sm font-bold uppercase tracking-wider text-slate-600 outline-none appearance-none cursor-pointer hover:text-slate-900"
                >
                  <option value="timestamp">Chronological</option>
                  <option value="importance_score">Highest Priority</option>
                </select>
              </div>
            </div>

            {/* Tag filters */}
            {allTags.length > 0 && (
              <div className="mb-12 flex flex-wrap gap-3">
                <button
                  onClick={() => setFilterTag(null)}
                  className={`rounded-full px-5 py-2.5 text-xs font-bold uppercase tracking-widest transition-all ${filterTag === null
                    ? "bg-[#07beb8] text-white shadow-[0_0_20px_rgba(7,190,184,0.3)]"
                    : "bg-white border border-slate-200 text-slate-500 hover:border-[#07beb8]/40 hover:text-slate-800 shadow-sm"
                    }`}
                >
                  All Signals
                </button>
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setFilterTag(filterTag === tag ? null : tag)}
                    className={`rounded-full px-5 py-2.5 text-xs font-bold uppercase tracking-widest transition-all ${filterTag === tag
                      ? "bg-[#07beb8] text-white shadow-[0_0_20px_rgba(7,190,184,0.3)]"
                      : "bg-white border border-slate-200 text-slate-500 hover:border-[#07beb8]/40 hover:text-slate-800 hover:bg-[#07beb8]/5 shadow-sm"
                      }`}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            )}

            {/* Ideas grid */}
            {displayed.length === 0 ? (
              <EmptyState hasIdeas={ideas.length > 0} />
            ) : (
              <div className="flex flex-col gap-6 max-w-4xl mx-auto w-full pb-48">
                {displayed.map((idea, index) => (
                  <div
                    key={idea.id}
                    style={{
                      animationDelay: `${index * 0.1}s`,
                      top: `calc(140px + ${index * 24}px)`,
                      zIndex: index,
                    }}
                    className="opacity-0 animate-[slideUp_0.5s_ease-out_forwards] sticky transition-all duration-300"
                  >
                    <IdeaCard idea={idea} />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── INSIGHTS & CONNECTIONS PLACEHOLDERS ── */}
        {activeTab === "insights" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 glass-card p-8 rounded-3xl animate-[fadeIn_0.5s_ease-out_forwards]">
            <DailyInsightPanel ideas={ideas} />
          </div>
        )}

        {activeTab === "connections" && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 glass-card p-8 rounded-3xl animate-[fadeIn_0.5s_ease-out_forwards]">
            <ConnectionsPanel ideas={ideas} />
          </div>
        )}
      </main>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

// ─── Empty State ──────────────────────────────────────────────────────────────

function EmptyState({ hasIdeas }: { hasIdeas: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white/30 py-32 text-center px-6 shadow-sm">
      <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-2xl bg-[#07beb8]/5 shadow-inner border border-slate-200">
        {hasIdeas ? (
          <Search size={40} className="text-[#07beb8]/50" />
        ) : (
          <Inbox size={40} className="text-[#07beb8]/50" />
        )}
      </div>
      <h2 className="font-display text-4xl font-bold text-slate-900 mb-4">
        {hasIdeas ? "Signal Lost" : "The Core is Empty"}
      </h2>
      <p className="mt-2 max-w-md text-lg text-slate-500 font-light leading-relaxed">
        {hasIdeas
          ? "Adjust your filters or query to find the data stream."
          : "Initialize your second brain by capturing your first thought. The deep neural net is awaiting input."}
      </p>
      {!hasIdeas && (
        <div className="mt-12">
          <Link to="/capture" className="btn-primary">
            <Mic size={20} />
            Initialize Thought Stream
          </Link>
        </div>
      )}
    </div>
  );
}
