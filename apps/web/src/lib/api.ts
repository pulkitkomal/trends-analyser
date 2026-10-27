const BASE =
  typeof window === "undefined"
    ? process.env.API_URL || "http://127.0.0.1:8001"
    : "";

export type User = {
  id: number;
  email: string;
  name: string;
};

export type Topic = {
  id: number;
  name: string;
  seed: string;
  notes: string;
  created_at: string;
  updated_at: string;
  last_ingested_at: string | null;
};

export type Surface = {
  id: number;
  topic_id: number;
  source: string;
  label: string;
  query: string;
  enabled: boolean;
};

export type Dashboard = {
  topic: Topic;
  surfaces: Surface[];
  posts: {
    id: number;
    source: string;
    title: string;
    body: string;
    url: string;
    author: string;
    score: number;
    comment_count: number;
    created_at: string | null;
  }[];
  keywords: { term: string; count: number; score: number }[];
  interest: { term: string; date: string; value: number }[];
  comment_insights: {
    summary: string;
    score: number;
    author: string;
    post_id: number;
    body: string;
  }[];
  recurring: { term: string; count: number; sources: number; why: string }[];
  briefing: string;
  themes: { name: string; why: string }[];
  related: {
    searches: string[];
    names: string[];
    places: { source: string; label: string; query: string }[];
    topics: { name: string; seed: string }[];
    links: { title: string; url: string }[];
  };
  digest: { markdown: string; created_at: string } | null;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth/")) {
    window.location.href = "/login";
    throw new Error("Sign in to continue");
  }
  if (!res.ok) {
    const text = await res.text();
    let message = text || res.statusText;
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed.detail === "string") message = parsed.detail;
      else if (Array.isArray(parsed.detail) && parsed.detail[0]?.msg) message = parsed.detail[0].msg;
    } catch {
      /* keep text */
    }
    throw new Error(message);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  me: () => req<User>("/api/auth/me"),
  register: (body: { name: string; email: string; password: string }) =>
    req<User>("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    req<User>("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  logout: () => req<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
  updateMe: (body: { name: string }) =>
    req<User>("/api/auth/me", { method: "PATCH", body: JSON.stringify(body) }),
  deleteMe: () => req<{ ok: boolean }>("/api/auth/me", { method: "DELETE" }),
  listTopics: () => req<Topic[]>("/api/topics"),
  createTopic: (body: { name: string; seed: string; notes?: string }) =>
    req<Topic>("/api/topics", { method: "POST", body: JSON.stringify(body) }),
  dashboard: (id: number) => req<Dashboard>(`/api/topics/${id}`),
  refresh: (id: number) => req<Topic>(`/api/topics/${id}/refresh`, { method: "POST" }),
  patchSurface: (id: number, body: Partial<Surface>) =>
    req<Surface>(`/api/topics/surfaces/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  addSurface: (
    topicId: number,
    body: { source: string; label: string; query: string; enabled?: boolean },
  ) =>
    req<Surface>(`/api/topics/${topicId}/surfaces`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteTopic: (id: number) => req<{ ok: boolean }>(`/api/topics/${id}`, { method: "DELETE" }),
};
