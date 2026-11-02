"use client";

import { sourceName } from "@/lib/format";

const SOURCE_COLOR: Record<string, string> = {
  rss: "#1d4ed8",
  hn: "#c2410c",
  bluesky: "#0284c7",
  github: "#334155",
  trends: "#7c3aed",
  reddit: "#b45309",
  x: "#0f172a",
};

export function SourceMix({ counts }: { counts: { source: string; count: number }[] }) {
  const rows = counts.filter((c) => c.count > 0).sort((a, b) => b.count - a.count);
  if (!rows.length) {
    return <p className="empty">No posts yet — tap Update now.</p>;
  }
  const max = Math.max(...rows.map((r) => r.count), 1);
  const total = rows.reduce((n, r) => n + r.count, 0);

  return (
    <div className="source-mix" aria-label="Posts by source">
      <ul className="source-bars">
        {rows.map((r) => {
          const pct = Math.round((r.count / total) * 100);
          const width = Math.max(4, Math.round((r.count / max) * 100));
          return (
            <li key={r.source}>
              <span className="source-label">{sourceName(r.source)}</span>
              <div className="source-track" aria-hidden="true">
                <div
                  className="source-fill"
                  style={{
                    width: `${width}%`,
                    background: SOURCE_COLOR[r.source] || "var(--accent)",
                  }}
                />
              </div>
              <span className="source-count">
                {r.count}
                <span className="source-pct">{pct}%</span>
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
