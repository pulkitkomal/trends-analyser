export const SOURCE_NAMES: Record<string, string> = {
  hn: "Hacker News",
  github: "GitHub",
  bluesky: "Bluesky",
  rss: "News feed",
  trends: "Google search",
  reddit: "Reddit",
  x: "X",
};

export function sourceName(id: string): string {
  return SOURCE_NAMES[id] || id;
}

export function timeAgo(value: string | null): string {
  if (!value) return "Not updated yet";
  const then = new Date(value).getTime();
  const mins = Math.round((Date.now() - then) / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}
