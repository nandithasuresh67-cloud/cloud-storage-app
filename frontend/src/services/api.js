import axios from "axios";

// Base URL comes from Vite env var so it's swappable per environment
// (local dev vs. deployed backend) without code changes.
const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  withCredentials: true, // backend will set JWTs as HttpOnly cookies once auth lands
});

export default api;
