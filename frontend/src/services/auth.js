import api from "./api";

/**
 * Auth is entirely cookie-based (HttpOnly, set by the backend) - there is
 * no token to store or attach manually here. `api`'s withCredentials: true
 * is what makes the browser send/receive those cookies automatically.
 */

export async function register({ email, password, fullName }) {
  const { data } = await api.post("/auth/register", { email, password, full_name: fullName || undefined });
  return data;
}

export async function login({ email, password }) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export async function logout() {
  await api.post("/auth/logout");
}

export async function getMe() {
  const { data } = await api.get("/auth/me");
  return data;
}
