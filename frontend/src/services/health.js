import api from "./api";

/**
 * Confirms the frontend can reach the FastAPI backend. This is the only
 * live endpoint the backend exposes as of Day 1, so it's what today's
 * "API connection" verification is built against.
 */
export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}
