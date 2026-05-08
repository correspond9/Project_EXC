/**
 * Axios instance — automatically attaches JWT access token from in-memory store.
 * Base URL comes from the NEXT_PUBLIC_API_BASE_URL environment variable.
 */
import axios from "axios";
import { useAuthStore } from "@/store/authStore";

const fallbackBaseUrl =
  typeof window !== "undefined" ? window.location.origin : "http://localhost";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || fallbackBaseUrl,
  withCredentials: true, // send HttpOnly refresh cookie on auth endpoints
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
