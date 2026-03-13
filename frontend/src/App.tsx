import { useEffect } from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import CapturePage from "./pages/CapturePage";
import DashboardPage from "./pages/DashboardPage";
import EditorPage from "./pages/EditorPage";
import LoginPage from "./pages/LoginPage";
import Lenis from "@studio-freight/lenis";
import useNoteStore from "./store/useNoteStore";
import { useAuthStore } from "./store/useAuthStore";
import { connectPhone, onMessage } from "./api/phoneConnection";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const status = useAuthStore((s) => s.status);
  
  if (status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center bg-[#f0faf9]">
        <div className="w-8 h-8 rounded-full border-4 border-[#07beb8]/30 border-t-[#07beb8] animate-spin"></div>
      </div>
    );
  }
  
  if (status === 'unconnected' || status === 'expired') {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

export function App() {
  useEffect(() => {
    // Check authentication
    useAuthStore.getState().checkAuth();

    // Load backend data
    useNoteStore.getState().loadInitialData();

    // Connect WebSocket
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Use localhost if in electron/dev, or host if remote
    const host = window.location.hostname === "localhost" ? "localhost:8000" : window.location.host;
    const wsUrl = import.meta.env.VITE_WS_URL || `${protocol}//${host}/api/phone`;
    
    connectPhone(wsUrl).catch(console.error);

    const unsubscribe = onMessage((msg) => {
      // Whenever backend processes a text input or finishes an action, refresh data
      if (msg.type === "speak" || msg.type === "update") {
        useNoteStore.getState().loadInitialData();
      }
    });

    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1,
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      unsubscribe();
      lenis.destroy();
    };
  }, []);

  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected Routes */}
        <Route path="/capture" element={
          <ProtectedRoute>
            <CapturePage />
          </ProtectedRoute>
        } />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        } />
        <Route path="/editor" element={
          <ProtectedRoute>
            <EditorPage />
          </ProtectedRoute>
        } />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
