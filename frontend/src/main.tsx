import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { App } from "./App";
import { seedDemoIdeas } from "./store/seedIdeas";

// Populate the in-memory store with demo ideas on first load
seedDemoIdeas();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
