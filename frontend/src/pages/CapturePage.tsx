import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Mic,
  MicOff,
  Send,
  RotateCcw,
  LayoutDashboard,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Cloud,
} from "lucide-react";
import { processTranscript } from "../api/process";
import { ideaStore, Idea } from "../store/ideas";
import MetaBalls from "../components/MetaBalls";

type Status = "idle" | "recording" | "processing" | "success" | "error";

export default function CapturePage() {
  const [status, setStatus] = useState<Status>("idle");
  const [transcript, setTranscript] = useState("");
  const [interimText, setInterimText] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setSupported(false);
    }
  }, []);

  const stopRecognition = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  }, []);

  const startRecording = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    setTranscript("");
    setInterimText("");
    setErrorMessage("");
    setStatus("recording");

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalText = "";
      let currentInterim = "";
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript + " ";
        } else {
          currentInterim += result[0].transcript;
        }
      }
      if (finalText) setTranscript((prev) => prev + finalText);
      setInterimText(currentInterim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech recognition error:", event.error);
      setStatus("error");
      setErrorMessage(
        event.error === "not-allowed"
          ? "Microphone access denied. Please allow microphone permissions."
          : `Speech recognition error: ${event.error}`
      );
      recognitionRef.current = null;
    };

    recognition.onend = () => {
      setInterimText("");
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, []);

  const stopRecording = useCallback(() => {
    stopRecognition();
    setStatus("idle");
  }, [stopRecognition]);

  const handleSubmit = useCallback(async () => {
    const fullText = (transcript + interimText).trim();
    if (!fullText) return;

    stopRecognition();
    setInterimText("");
    setStatus("processing");
    setErrorMessage("");

    try {
      const structured = await processTranscript(fullText);
      const idea: Idea = {
        ...structured,
        id: crypto.randomUUID(),
        raw_transcript: fullText,
        timestamp: new Date().toISOString(),
      };
      ideaStore.add(idea);
      setStatus("success");
      setTimeout(() => navigate("/dashboard"), 1200);
    } catch (err) {
      console.error(err);
      setStatus("error");
      setErrorMessage("Failed to process your thought signal. Neural connection lost.");
    }
  }, [transcript, interimText, stopRecognition, navigate]);

  const reset = useCallback(() => {
    stopRecognition();
    setTranscript("");
    setInterimText("");
    setErrorMessage("");
    setStatus("idle");
  }, [stopRecognition]);

  const fullTranscript = transcript + (interimText ? interimText : "");
  const hasContent = fullTranscript.trim().length > 0;

  return (
    <div className="min-h-screen bg-adnia bg-dots flex flex-col items-center relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#07beb8]/10 blur-[150px] rounded-full pointer-events-none" />

      {/* Nav */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/30 backdrop-blur-2xl border-b border-slate-200/50">
        <div className="mx-auto flex h-24 max-w-screen-2xl items-center justify-between px-6 lg:px-12">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#07beb8]/10 border border-[#07beb8]/20 transition-transform group-hover:scale-105">
              <Cloud size={20} className="text-[#07beb8]" />
            </div>
            <div className="flex flex-col">
              <span className="font-display font-bold text-lg text-slate-900 leading-none group-hover:text-slate-700 transition-colors">ThoughtCapture</span>
              <span className="mt-1 text-[10px] font-black uppercase tracking-[0.2em] text-[#07beb8]">v2 - Input Node</span>
            </div>
          </Link>
          <Link
            to="/dashboard"
            className="flex items-center gap-2 rounded-full bg-white border border-slate-200 px-6 py-3 text-xs font-bold uppercase tracking-widest text-slate-600 transition-all hover:bg-slate-50 hover:text-slate-900 shadow-sm"
          >
            <LayoutDashboard size={14} />
            View Data Core
          </Link>
        </div>
      </header>

      {/* Main */}
      <main className="w-full max-w-2xl px-6 pt-32 pb-20 relative z-10 animate-[slideUp_0.5s_ease-out_forwards]">
        <div className="w-full space-y-12">
          {/* Title */}
          <div className="text-center space-y-3">
            <h1 className="font-display text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
              Awaiting Signal
            </h1>
            <p className="text-sm font-light text-slate-500">
              Transmit your thoughts. The neural engine will map the geometry of your idea.
            </p>
          </div>

          {/* Not supported warning */}
          {!supported && (
            <div className="rounded-2xl border border-amber-400/30 bg-amber-50 p-5 text-sm font-light text-amber-700 flex items-start gap-3">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span className="leading-relaxed">
                Local speech interface disconnected. Browser incompatibility detected.
                Manual text input is still fully functional below.
              </span>
            </div>
          )}

          {/* Record button */}
          <div className="flex flex-col items-center gap-6">
            <div className="relative group perspective" style={{ width: '144px', height: '144px' }}>
              {/* MetaBalls background layer */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[150vw] h-[150vh] z-[-1] pointer-events-none">
                <MetaBalls
                  color="#07beb8"
                  cursorBallColor="#3dccc7"
                  cursorBallSize={1}
                  ballCount={10}
                  animationSize={50}
                  enableMouseInteraction
                  enableTransparency={true}
                  hoverSmoothness={0.086}
                  clumpFactor={1}
                  speed={0.5}
                />
              </div>
              {status === "recording" && (
                <>
                  <span className="absolute inset-0 rounded-full animate-ping bg-[#07beb8]/40 duration-1000 z-[1]" />
                  <span className="absolute inset-[-12px] rounded-full animate-pulse bg-[#07beb8]/20 duration-700 z-[1]" />
                </>
              )}
              <button
                onClick={status === "recording" ? stopRecording : startRecording}
                disabled={!supported || status === "processing" || status === "success"}
                className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 flex h-36 w-36 items-center justify-center rounded-full transition-all duration-300 shadow-2xl disabled:opacity-30 disabled:cursor-not-allowed
                  ${status === "recording"
                    ? "bg-[#07beb8] scale-105 shadow-[0_0_50px_rgba(7,190,184,0.6)]"
                    : "bg-[#f0faf9] border border-[#07beb8]/30 hover:bg-[#e2f7f6] hover:border-[#07beb8]/60 hover:scale-105 shadow-[0_0_30px_rgba(7,190,184,0.15)]"
                  }`}
              >
                {status === "recording" ? (
                  <MicOff size={48} className="text-white" />
                ) : (
                  <Mic size={48} className="text-[#07beb8] drop-shadow-[0_0_10px_rgba(7,190,184,0.8)]" />
                )}
              </button>
            </div>

            <div className="h-6">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500 transition-all">
                {status === "idle" && "Initiate Voice Capture"}
                {status === "recording" && (
                  <span className="flex items-center gap-2 text-[#07beb8]">
                    <span className="h-2 w-2 rounded-full bg-[#07beb8] animate-pulse shadow-[0_0_8px_#07beb8]" />
                    Recording Signal... Tap to Terminate
                  </span>
                )}
                {status === "processing" && (
                  <span className="flex items-center gap-2 text-[#07beb8]/80">
                    <Loader2 size={14} className="animate-spin" />
                    AI Structuring in Progress...
                  </span>
                )}
                {status === "success" && (
                  <span className="flex items-center gap-2 text-[#07beb8]">
                    <CheckCircle2 size={14} />
                    Signal Locked. Routing to Core...
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Transcript area */}
          <div className="space-y-3">
            <label className="block text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
              Raw Input Stream
            </label>
            <div className="relative">
              <textarea
                value={fullTranscript}
                onChange={(e) => {
                  setTranscript(e.target.value);
                  setInterimText("");
                }}
                placeholder={
                  status === "recording"
                    ? "Listening for neural patterns..."
                    : "Type manually or use voice capture above to begin data ingestion..."
                }
                rows={6}
                className="w-full resize-none rounded-2xl border border-slate-200 bg-white px-6 py-5 text-sm font-light text-slate-800 placeholder-slate-400 outline-none transition-all focus:border-[#07beb8]/50 focus:shadow-[0_0_20px_rgba(7,190,184,0.1)] shadow-sm"
              />
              {interimText && (
                <div className="absolute bottom-4 left-6 right-6 pointer-events-none">
                  <span className="text-sm text-[#07beb8] italic font-light animate-pulse">{interimText}</span>
                </div>
              )}
            </div>
          </div>

          {/* Error */}
          {status === "error" && errorMessage && (
            <div className="rounded-2xl border border-rose-300 bg-rose-50 p-5 text-sm font-light text-rose-600 flex items-start gap-3">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span className="leading-relaxed">{errorMessage}</span>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-4 pt-4">
            <button
              onClick={reset}
              disabled={status === "processing" || status === "success" || (!hasContent && status === "idle")}
              className="flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-4 text-xs font-bold uppercase tracking-widest text-slate-500 transition-all hover:bg-slate-50 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
            >
              <RotateCcw size={16} />
              Reset
            </button>
            <button
              onClick={handleSubmit}
              disabled={!hasContent || status === "processing" || status === "success"}
              className="flex flex-1 items-center justify-center gap-3 rounded-full bg-[#07beb8] px-6 py-4 text-sm font-bold uppercase tracking-[0.1em] text-white transition-all hover:bg-[#3dccc7] hover:scale-[1.02] disabled:opacity-30 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(7,190,184,0.2)] disabled:hover:scale-100"
            >
              {status === "processing" ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Processing...
                </>
              ) : status === "success" ? (
                <>
                  <CheckCircle2 size={18} />
                  Captured
                </>
              ) : (
                <>
                  <Send size={18} />
                  Process & Restructure
                </>
              )}
            </button>
          </div>
        </div>
      </main>

      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
