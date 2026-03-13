import { create } from 'zustand';
import { fetchAuthStatus, getGoogleLoginUrl } from '../api/auth';

export type AuthStatus = 'loading' | 'connected' | 'needs_refresh' | 'expired' | 'unconnected';

interface AuthState {
  status: AuthStatus;
  email: string | null;
  checkAuth: () => Promise<void>;
  login: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'loading',
  email: null,
  checkAuth: async () => {
    try {
      const res = await fetchAuthStatus();
      set({ status: res.status, email: res.email || null });
    } catch (e) {
      set({ status: 'unconnected', email: null });
    }
  },
  login: () => {
    window.location.href = getGoogleLoginUrl();
  }
}));
