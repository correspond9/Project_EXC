import { create } from 'zustand';

interface AuthState {
  isAuthenticated: boolean;
  userId: string | null;
  email: string | null;
  role: string | null;
  tradingMode: string | null;
  setAuth: (userId: string, email: string, role: string, tradingMode: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  userId: null,
  email: null,
  role: null,
  tradingMode: null,
  setAuth: (userId, email, role, tradingMode) =>
    set({ isAuthenticated: true, userId, email, role, tradingMode }),
  clearAuth: () =>
    set({ isAuthenticated: false, userId: null, email: null, role: null, tradingMode: null }),
}));
