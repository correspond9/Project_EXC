/**
 * Zustand store — auth state.
 * Access token is held in memory only (never written to localStorage).
 * HttpOnly refresh cookie is managed by the browser automatically.
 */
import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  userEmail: string | null;
  userRole: string | null;
  setAuth: (token: string, email: string, role: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  userEmail: null,
  userRole: null,
  setAuth: (token, email, role) => set({ accessToken: token, userEmail: email, userRole: role }),
  clearAuth: () => set({ accessToken: null, userEmail: null, userRole: null }),
}));
