export const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export async function fetchAuthStatus() {
  const res = await fetch(`${BACKEND_URL}/auth/google/status`);
  if (!res.ok) throw new Error("Failed to fetch auth status");
  return res.json();
}

export function getGoogleLoginUrl() {
  return `${BACKEND_URL}/auth/google/login`;
}
