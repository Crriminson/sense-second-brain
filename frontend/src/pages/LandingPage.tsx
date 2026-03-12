import { Link } from "react-router-dom";
import { Mic, Grid, ArrowRight } from "lucide-react";
import MetaBalls from "../components/MetaBalls";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-adnia bg-dots">
      {/* Dynamic light glows */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -right-[10%] w-[500px] h-[500px] rounded-full bg-[#07beb8]/15 blur-[120px]" />
        <div className="absolute top-[40%] -left-[10%] w-[600px] h-[600px] rounded-full bg-[#07beb8]/10 blur-[150px]" />
      </div>

      {/* MetaBalls background layer */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <MetaBalls
          color="#07beb8"
          cursorBallColor="#3dccc7"
          cursorBallSize={1.3}
          ballCount={30}
          animationSize={80}
          enableMouseInteraction
          enableTransparency={true}
          hoverSmoothness={0.0076}
          clumpFactor={8}
          speed={0.35}
        />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-slate-200/50 bg-white/30 backdrop-blur-2xl">
        <div className="mx-auto flex h-24 max-w-screen-2xl items-center justify-between px-6 lg:px-12">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#07beb8]/10 border border-[#07beb8]/20">
              <span className="text-[#07beb8] font-display font-extrabold text-xl">TC</span>
            </div>
            <div className="flex flex-col">
              <h1 className="font-display text-xl font-bold text-slate-900 leading-none">ThoughtCapture</h1>
              <span className="mt-1 text-[10px] font-bold uppercase tracking-[0.2em] text-[#07beb8]">Second Brain v2</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="group flex items-center justify-center h-12 w-12 rounded-full border border-slate-200 bg-white text-slate-500 transition-all hover:border-[#07beb8]/50 hover:bg-[#07beb8]/10 hover:text-[#07beb8] shadow-sm">
              <Grid size={20} className="transition-transform group-hover:scale-110" />
            </Link>
            <Link to="/capture" className="flex items-center justify-center h-12 w-12 rounded-full bg-[#07beb8] text-white shadow-[0_0_20px_rgba(7,190,184,0.3)] transition-transform hover:scale-110">
              <Mic size={20} />
            </Link>
          </div>
        </div>
      </header>

      <main className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 pt-32 pb-20">
        <section className="mx-auto w-full max-w-5xl text-center">
          <div className="mb-10 inline-flex items-center gap-3 rounded-full border border-[#07beb8]/20 bg-[#07beb8]/5 px-4 py-2 opacity-0 animate-[fadeIn_1s_ease-out_forwards]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#07beb8] opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#07beb8]"></span>
            </span>
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#07beb8]">Intelligence Reimagined</span>
          </div>

          <h1 className="font-display text-6xl font-extrabold leading-[1.05] tracking-tight sm:text-8xl lg:text-[100px] opacity-0 animate-[slideUp_1s_ease-out_0.2s_forwards]">
            <span className="text-slate-900">Think it.</span><br />
            <span className="text-[#07beb8]">Speak it.</span><br />
            <span className="text-slate-400">Know it.</span>
          </h1>



          <div className="mt-16 flex flex-col items-center justify-center gap-6 sm:flex-row opacity-0 animate-[slideUp_1s_ease-out_0.6s_forwards]">
            <Link to="/capture" className="btn-primary w-full sm:w-auto">
              Start Capturing
              <ArrowRight size={18} />
            </Link>
            <Link to="/dashboard" className="btn-secondary w-full sm:w-auto">
              Open Dashboard
            </Link>
          </div>
        </section>
      </main>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
