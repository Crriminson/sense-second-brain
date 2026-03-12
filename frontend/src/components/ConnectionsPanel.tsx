import { useState, useCallback, useEffect, useMemo } from "react";
import { Idea, IdeaConnection } from "../store/ideas";
import { ideaStore } from "../store/ideas";
import { analyzeConnections } from "../api/process";
import {
  GitBranch,
  Loader2,
  RefreshCw,
  Zap,
  ChevronDown,
  ChevronUp,
  Link2,
  AlertCircle,
} from "lucide-react";

interface Props {
  ideas: Idea[];
}

const strengthConfig = {
  strong: {
    label: "Strong",
    dot: "bg-emerald-500",
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
    line: "border-emerald-200 bg-emerald-50/50",
  },
  moderate: {
    label: "Moderate",
    dot: "bg-sky-500",
    badge: "border-sky-200 bg-sky-50 text-sky-700",
    line: "border-sky-200 bg-sky-50/50",
  },
  weak: {
    label: "Weak",
    dot: "bg-slate-400",
    badge: "border-slate-200 bg-slate-50 text-slate-600",
    line: "border-slate-200 bg-slate-50/50",
  },
};

function ConnectionCard({ conn }: { conn: IdeaConnection }) {
  const cfg = strengthConfig[conn.strength];
  return (
    <div className={`rounded-xl border p-4 ${cfg.line} transition-all duration-200`}>
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div className="flex items-center gap-1.5 min-w-0">
            <span className="truncate text-xs font-semibold text-slate-700 rounded-md bg-white border border-slate-200 px-2 py-1">
              {conn.idea_a_title}
            </span>
            <Link2 size={13} className="shrink-0 text-slate-400" />
            <span className="truncate text-xs font-semibold text-slate-700 rounded-md bg-white border border-slate-200 px-2 py-1">
              {conn.idea_b_title}
            </span>
          </div>
        </div>
        <span
          className={`shrink-0 inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${cfg.badge}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
          {cfg.label}
        </span>
      </div>
      <p className="text-xs text-slate-600 leading-relaxed">{conn.explanation}</p>
    </div>
  );
}

export default function ConnectionsPanel({ ideas }: Props) {
  const [connections, setConnections] = useState<IdeaConnection[]>(
    ideaStore.getConnections()
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [collapsed, setCollapsed] = useState(false);

  const visibleConnections = useMemo(() => {
    const ids = new Set(ideas.map((i) => i.id));
    return connections.filter((c) => ids.has(c.idea_a_id) && ids.has(c.idea_b_id));
  }, [connections, ideas]);

  useEffect(() => {
    const unsub = ideaStore.subscribe(() => {
      setConnections(ideaStore.getConnections());
    });
    return unsub;
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (ideas.length < 2) return;
    setLoading(true);
    setError("");
    try {
      const result = await analyzeConnections(ideas);
      ideaStore.setConnections(result);
      setConnections(result);
      setCollapsed(false);
    } catch (err) {
      console.error(err);
      setError("Failed to analyze connections. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [ideas]);

  const strong = visibleConnections.filter((c) => c.strength === "strong").length;
  const moderate = visibleConnections.filter((c) => c.strength === "moderate").length;

  return (
    <div className="rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-50 to-indigo-50 shadow-sm mb-6 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-100 shadow-inner">
            <GitBranch size={18} className="text-sky-600" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-sky-900">Idea Connections</h2>
            <p className="text-xs text-sky-600">
              {visibleConnections.length > 0
                ? `${visibleConnections.length} connection${visibleConnections.length !== 1 ? "s" : ""} found · ${strong} strong · ${moderate} moderate`
                : `${ideas.length} ideas ready to analyze`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {visibleConnections.length > 0 && (
            <button
              onClick={() => setCollapsed((v) => !v)}
              className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-sky-700 hover:bg-sky-100 transition-colors"
            >
              {collapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
              {collapsed ? "Show" : "Hide"}
            </button>
          )}
          <button
            onClick={handleAnalyze}
            disabled={loading || ideas.length < 2}
            className="flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-2 text-xs font-semibold text-white shadow-sm shadow-sky-200 transition hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
          >
            {loading ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                Analyzing…
              </>
            ) : visibleConnections.length > 0 ? (
              <>
                <RefreshCw size={13} />
                Re-analyze
              </>
            ) : (
              <>
                <Zap size={13} />
                Analyze Connections
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600 flex items-center gap-2">
          <AlertCircle size={12} />
          {error}
        </div>
      )}

      {/* Not enough ideas */}
      {ideas.length < 2 && (
        <div className="px-5 pb-5">
          <p className="text-xs text-sky-600 text-center py-3 rounded-xl border border-sky-200 border-dashed bg-sky-50">
            Capture at least 2 ideas to analyze connections between them.
          </p>
        </div>
      )}

      {/* No connections found */}
      {!loading && visibleConnections.length === 0 && ideas.length >= 2 && (
        <div className="px-5 pb-5">
          <p className="text-xs text-sky-500 text-center py-3 rounded-xl border border-sky-200 border-dashed bg-sky-50/50">
            No saved connections yet. Click "Analyze Connections" to fetch current relationships from the backend.
          </p>
        </div>
      )}

      {/* Connections list */}
      {visibleConnections.length > 0 && !collapsed && (
        <div className="px-5 pb-5 space-y-2.5">
          <div className="h-px bg-sky-200" />

          {/* Legend */}
          <div className="flex items-center gap-4 py-1">
            {(["strong", "moderate", "weak"] as const).map((s) => (
              <div key={s} className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${strengthConfig[s].dot}`} />
                <span className="text-xs text-slate-500 capitalize">{s}</span>
              </div>
            ))}
          </div>

          {visibleConnections.map((conn, i) => (
            <ConnectionCard key={`${conn.idea_a_id}-${conn.idea_b_id}-${i}`} conn={conn} />
          ))}
        </div>
      )}
    </div>
  );
}
