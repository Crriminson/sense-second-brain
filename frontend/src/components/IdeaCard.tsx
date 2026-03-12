import { useState, useCallback } from "react";
import { Idea } from "../store/ideas";
import { ideaStore } from "../store/ideas";
import { expandIdea } from "../api/process";
import {
  Lightbulb,
  CheckSquare,
  ChevronUp,
  Clock,
  Sparkles,
  Loader2,
  Users,
  Target,
  TrendingUp,
  Briefcase,
  AlertCircle,
  BadgeCheck,
} from "lucide-react";

// ─── Sub-components ────────────────────────────────────────────────────────────

function ImportanceBadge({ score }: { score: number }) {
  const level = score >= 8 ? "high" : score >= 5 ? "medium" : "low";
  const styles = {
    high: "bg-rose-50 text-rose-500 border-rose-200",
    medium: "bg-[#07beb8]/10 text-[#07beb8] border-[#07beb8]/20",
    low: "bg-slate-50 text-slate-400 border-slate-200",
  };
  const labels = { high: "High Priority", medium: "Medium", low: "Low" };

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] ${styles[level]}`}
    >
      <span className="relative flex h-1.5 w-1.5">
        <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${score >= 5 ? "bg-current" : "hidden"}`}></span>
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-current"></span>
      </span>
      {labels[level]}
    </div>
  );
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ─── Expansion panel ──────────────────────────────────────────────────────────

function ExpansionPanel({ idea }: { idea: Idea }) {
  const exp = idea.expansion!;

  const sections = [
    {
      icon: <AlertCircle size={16} className="text-[#07beb8]" />,
      label: "Problem Identified",
      color: "border-slate-100 bg-slate-50/50",
      text: exp.problem,
    },
    {
      icon: <Lightbulb size={16} className="text-[#07beb8]" />,
      label: "Proposed Architecture",
      color: "border-[#07beb8]/20 bg-[#07beb8]/[0.03]",
      text: exp.proposed_solution,
    },
    {
      icon: <Users size={16} className="text-[#07beb8]" />,
      label: "Target Persona",
      color: "border-slate-100 bg-slate-50/50",
      text: exp.target_users,
    },
    {
      icon: <Target size={16} className="text-[#07beb8]" />,
      label: "Impact Vector",
      color: "border-slate-100 bg-slate-50/50",
      text: exp.potential_impact,
    },
    {
      icon: <Briefcase size={16} className="text-[#07beb8]" />,
      label: "Business Mechanics",
      color: "border-[#07beb8]/20 bg-[#07beb8]/[0.03]",
      text: exp.business_opportunity,
    },
  ];

  return (
    <div className="px-8 pb-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pt-6 border-t border-slate-100">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#07beb8]/10 border border-[#07beb8]/20">
          <Sparkles size={16} className="text-[#07beb8]" />
        </div>
        <h4 className="text-xs font-black uppercase tracking-[0.2em] text-[#07beb8]">
          Deep Knowledge Graph
        </h4>
        <BadgeCheck size={18} className="text-[#07beb8]/40 ml-auto" />
      </div>

      {/* Grid of sections */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {sections.map(({ icon, label, color, text }) => (
          <div
            key={label}
            className={`rounded-2xl border p-5 transition-colors hover:border-[#07beb8]/40 ${color}`}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="rounded-lg bg-[#07beb8]/5 p-1.5">{icon}</div>
              <span className="text-[11px] font-bold uppercase tracking-widest text-slate-600">{label}</span>
            </div>
            <p className="text-sm font-light text-slate-500 leading-relaxed">{text}</p>
          </div>
        ))}
      </div>

      {/* Next Steps */}
      {exp.next_steps.length > 0 && (
        <div className="rounded-2xl border border-[#07beb8]/30 bg-[#07beb8]/[0.03] p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="rounded-lg bg-[#07beb8]/10 p-1.5">
              <TrendingUp size={16} className="text-[#07beb8]" />
            </div>
            <span className="text-[11px] font-bold uppercase tracking-widest text-[#07beb8]">Execution Vector</span>
          </div>
          <ol className="space-y-3">
            {exp.next_steps.map((step, i) => (
              <li key={i} className="flex items-start gap-4 text-sm font-light text-slate-600 bg-white p-4 rounded-xl border border-slate-100">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#07beb8]/20 text-[#07beb8] font-black text-xs border border-[#07beb8]/30">
                  {i + 1}
                </span>
                <span className="pt-0.5 leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

// ─── Main IdeaCard ─────────────────────────────────────────────────────────────

interface Props {
  idea: Idea;
}

export default function IdeaCard({ idea }: Props) {
  const [showExpansion, setShowExpansion] = useState(!!idea.expansion);
  const [expanding, setExpanding] = useState(false);
  const [expandError, setExpandError] = useState("");

  const handleExpandIdea = useCallback(async () => {
    if (idea.expansion) {
      setShowExpansion((v) => !v);
      return;
    }
    setExpanding(true);
    setExpandError("");
    try {
      const expansion = await expandIdea(idea);
      ideaStore.update(idea.id, { expansion, is_expanded: true });
      setShowExpansion(true);
    } catch (err) {
      console.error(err);
      setExpandError("Failed to expand signal. Neural link lost.");
    } finally {
      setExpanding(false);
    }
  }, [idea]);

  return (
    <article className="idea-card-premium flex flex-col h-full z-10">
      {/* Dynamic top gradient line */}
      <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[#07beb8]/50 to-transparent opacity-0 transition-opacity duration-500 hover-trigger" />

      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4 p-8 pb-4">
        <ImportanceBadge score={idea.importance_score} />
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-400 bg-slate-50 px-3 py-1 rounded-full border border-slate-100">
          <Clock size={12} />
          {formatTimestamp(idea.timestamp)}
        </div>
      </div>
      
      {/* ── Title & Summary ── */}
      <div className="px-8 pb-6">
        <h3 className="font-display text-2xl font-bold text-slate-900 leading-tight mb-4 tracking-tight">
          {idea.title}
        </h3>
        {idea.is_expanded && (
           <span className="inline-flex items-center gap-2 rounded-md bg-[#07beb8]/10 border border-[#07beb8]/20 px-2 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-[#07beb8] mb-5">
             <Sparkles size={12} className="animate-pulse" />
             AI Enriched
           </span>
         )}
        <p className="text-base font-light text-slate-500 leading-relaxed mb-6">
          {idea.summary}
        </p>
        
        {idea.tags.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 mt-6">
            {idea.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-slate-50 border border-slate-200 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-slate-500 transition-colors hover:bg-[#07beb8]/10 hover:text-[#07beb8] hover:border-[#07beb8]/30 cursor-pointer"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ── Core Details (Always Expanded) ── */}
      <div className="border-t border-slate-100 mx-8 my-2" />

      <div className="px-8 pt-6 pb-6">
        <h4 className="mb-3 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
          Raw Concept Data
        </h4>
        <div className="bg-slate-50 border border-slate-100 rounded-2xl p-5">
          <p className="text-sm font-light text-slate-600 leading-relaxed whitespace-pre-wrap">{idea.expanded_idea}</p>
        </div>
      </div>

      {/* Action items */}
      {idea.action_items.length > 0 && (
        <div className="px-8 pb-8">
          <h4 className="mb-4 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
            <CheckSquare size={14} className="text-slate-400" />
            Actionable Logic
          </h4>
          <ul className="space-y-3">
            {idea.action_items.map((item, i) => (
              <li key={i} className="flex items-start gap-4 transition-colors hover:bg-slate-50 p-2 rounded-lg -mx-2">
                <span className="mt-1 h-3 w-3 shrink-0 rounded-sm border-2 border-[#07beb8] bg-transparent" />
                <span className="text-sm font-light text-slate-600">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── AI Deep Expansion panel ── */}
      {idea.expansion && showExpansion && (
        <div className="mt-auto bg-slate-50/50 rounded-b-3xl">
          <div className="border-t border-slate-100" />
          <ExpansionPanel idea={idea} />
        </div>
      )}

      {/* ── Expand error ── */}
      {expandError && (
        <div className="mx-8 mb-6 rounded-2xl border border-rose-300 bg-rose-50 px-5 py-4 text-sm font-medium text-rose-500 flex items-center gap-3">
          <AlertCircle size={18} />
          {expandError}
        </div>
      )}

      {/* Spacer to push footer to bottom */}
      <div className="flex-grow"></div>

      {/* ── Footer / CTA ── */}
      <div className="border-t border-slate-100 px-8 py-6 mt-4">
        <button
          onClick={handleExpandIdea}
          disabled={expanding}
          className={`w-full flex justify-center items-center gap-3 rounded-full px-6 py-4 text-xs font-black uppercase tracking-[0.2em] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${
            idea.is_expanded && showExpansion
              ? "bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200"
              : idea.is_expanded
              ? "bg-[#07beb8]/10 text-[#07beb8] border border-[#07beb8]/20 hover:bg-[#07beb8] hover:text-white shadow-[0_0_20px_rgba(7,190,184,0.1)]"
              : "bg-[#07beb8] text-white shadow-[0_0_30px_rgba(7,190,184,0.3)] hover:scale-[1.02]"
          }`}
        >
          {expanding ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Processing Signal...
            </>
          ) : idea.is_expanded && showExpansion ? (
            <>
              <ChevronUp size={16} />
              Collapse Node
            </>
          ) : idea.is_expanded ? (
            <>
              <Sparkles size={16} />
              Re-open Deep Expansion
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Initiate Deep Expansion
            </>
          )}
        </button>
      </div>
    </article>
  );
}
