import { useState, useCallback } from "react";
import { Idea, DailyInsight } from "../store/ideas";
import { ideaStore } from "../store/ideas";
import { generateDailyInsight } from "../api/process";
import {
  Sparkles,
  Loader2,
  RefreshCw,
  Lightbulb,
  Hash,
  TrendingUp,
  Star,
  ChevronDown,
  ChevronUp,
  Calendar,
} from "lucide-react";

interface Props {
  ideas: Idea[];
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DailyInsightPanel({ ideas }: Props) {
  const [insight, setInsight] = useState<DailyInsight | null>(
    ideaStore.getDailyInsight
      ? (() => {
          const saved = ideaStore.getDailyInsight();
          // Only show if generated today
          if (saved && saved.date === new Date().toDateString()) return saved;
          return null;
        })()
      : null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [collapsed, setCollapsed] = useState(false);

  const todayIdeas = ideas.filter(
    (i) => new Date(i.timestamp).toDateString() === new Date().toDateString()
  );

  const handleGenerate = useCallback(async () => {
    if (todayIdeas.length === 0) return;
    setLoading(true);
    setError("");
    try {
      const result = await generateDailyInsight(todayIdeas);
      ideaStore.setDailyInsight(result);
      setInsight(result);
      setCollapsed(false);
    } catch (err) {
      console.error(err);
      setError("Failed to generate insight. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [todayIdeas]);

  return (
    <div className="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 shadow-sm mb-6 overflow-hidden">
      {/* Panel header */}
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-100 shadow-inner">
            <Sparkles size={18} className="text-amber-600" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-amber-900">Daily Insight</h2>
            <p className="text-xs text-amber-600">
              {todayIdeas.length} idea{todayIdeas.length !== 1 ? "s" : ""} captured today
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {insight && (
            <button
              onClick={() => setCollapsed((v) => !v)}
              className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100 transition-colors"
            >
              {collapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
              {collapsed ? "Show" : "Hide"}
            </button>
          )}
          <button
            onClick={handleGenerate}
            disabled={loading || todayIdeas.length === 0}
            className="flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2 text-xs font-semibold text-white shadow-sm shadow-amber-200 transition hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
          >
            {loading ? (
              <>
                <Loader2 size={13} className="animate-spin" />
                Generating…
              </>
            ) : insight ? (
              <>
                <RefreshCw size={13} />
                Regenerate
              </>
            ) : (
              <>
                <Sparkles size={13} />
                Generate Insight
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-5 mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">
          {error}
        </div>
      )}

      {/* No ideas today */}
      {!insight && !loading && todayIdeas.length === 0 && (
        <div className="px-5 pb-5">
          <p className="text-xs text-amber-600 text-center py-3 rounded-xl border border-amber-200 border-dashed bg-amber-50">
            Capture at least one idea today to generate your daily insight.
          </p>
        </div>
      )}

      {/* Insight content */}
      {insight && !collapsed && (
        <div className="px-5 pb-5 space-y-4">
          <div className="h-px bg-amber-200" />

          {/* Generated at */}
          <div className="flex items-center gap-1.5 text-xs text-amber-500">
            <Calendar size={11} />
            Generated at {formatTime(insight.generated_at)} · {insight.date}
          </div>

          {/* Thinking Themes */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Hash size={13} className="text-amber-600" />
              <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">
                Thinking Themes
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {insight.thinking_themes.map((theme) => (
                <span
                  key={theme}
                  className="rounded-full border border-amber-300 bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700"
                >
                  #{theme}
                </span>
              ))}
            </div>
          </div>

          {/* Most Promising Idea */}
          <div className="rounded-xl border border-amber-200 bg-white/70 px-4 py-3">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Star size={13} className="text-amber-500 fill-amber-400" />
              <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">
                Most Promising Idea
              </span>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">
              {insight.most_promising_idea}
            </p>
          </div>

          {/* Key Insight */}
          <div className="rounded-xl border border-orange-200 bg-white/70 px-4 py-3">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Lightbulb size={13} className="text-orange-500" />
              <span className="text-xs font-bold text-orange-700 uppercase tracking-wider">
                Key Insight
              </span>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">
              {insight.key_insight}
            </p>
          </div>

          {/* Suggested Next Steps */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp size={13} className="text-amber-600" />
              <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">
                Suggested Next Steps
              </span>
            </div>
            <ol className="space-y-2">
              {insight.suggested_next_steps.map((step, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 rounded-lg border border-amber-100 bg-white/60 px-3 py-2.5"
                >
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-200 text-amber-700 font-bold text-[11px]">
                    {i + 1}
                  </span>
                  <span className="text-sm text-slate-700">{step}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
