"use client";

import { useId, useMemo } from "react";

type Point = { date: string; value: number };
type Series = { term: string; points: Point[] };

const COLORS = ["var(--heat)", "var(--accent)", "#1d4ed8", "#0284c7", "#7c3aed"];

export function InterestChart({ series }: { series: Series[] }) {
  const gradId = useId().replace(/:/g, "");
  const { active, layout } = useMemo(() => {
    const next = series.filter((s) => s.points.length > 1).slice(0, 4);
    return { active: next, layout: buildLayout(next) };
  }, [series]);

  if (!active.length || !layout) {
    return <p className="empty">No search-interest history yet.</p>;
  }

  const { width, height, pad, paths, yMax, xLabels } = layout;

  return (
    <div className="interest-chart">
      <svg
        className="interest-svg"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={summarize(active)}
      >
        <defs>
          {active.map((_, i) => (
            <linearGradient key={i} id={`${gradId}-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity="0.28" />
              <stop offset="100%" stopColor={COLORS[i % COLORS.length]} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>
        {[0, 0.5, 1].map((t) => {
          const y = pad.top + (height - pad.top - pad.bottom) * (1 - t);
          return (
            <g key={t}>
              <line x1={pad.left} y1={y} x2={width - pad.right} y2={y} className="chart-grid" />
              <text x={pad.left - 8} y={y + 3} className="chart-tick" textAnchor="end">
                {Math.round(yMax * t)}
              </text>
            </g>
          );
        })}
        {paths.map((p, i) => (
          <g key={active[i].term}>
            <path d={p.area} fill={`url(#${gradId}-${i})`} />
            <polyline
              fill="none"
              stroke={COLORS[i % COLORS.length]}
              strokeWidth="2.25"
              strokeLinejoin="round"
              strokeLinecap="round"
              points={p.line}
            />
            {p.last ? (
              <>
                <circle cx={p.last.x} cy={p.last.y} r="3.5" fill={COLORS[i % COLORS.length]} />
                <text x={p.last.x - 6} y={p.last.y - 8} className="chart-end" textAnchor="end">
                  {Math.round(p.last.value)}
                </text>
              </>
            ) : null}
          </g>
        ))}
        {xLabels.map((lab) => (
          <text key={lab.x} x={lab.x} y={height - 6} className="chart-tick" textAnchor="middle">
            {lab.label}
          </text>
        ))}
      </svg>
      <ul className="chart-legend">
        {active.map((s, i) => (
          <li key={s.term}>
            <span className="legend-swatch" style={{ background: COLORS[i % COLORS.length] }} />
            {s.term}
          </li>
        ))}
      </ul>
    </div>
  );
}

function summarize(series: Series[]): string {
  return series
    .map((s) => {
      const last = s.points[s.points.length - 1];
      return `${s.term} ends at ${Math.round(last.value)}`;
    })
    .join("; ");
}

function buildLayout(series: Series[]) {
  if (!series.length) return null;
  const width = 720;
  const height = 180;
  const pad = { top: 16, right: 16, bottom: 28, left: 36 };
  const allDates = [...new Set(series.flatMap((s) => s.points.map((p) => p.date)))].sort();
  const yMax = Math.max(10, ...series.flatMap((s) => s.points.map((p) => p.value)));
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const xFor = (date: string) => {
    if (allDates.length === 1) return pad.left + plotW / 2;
    const i = allDates.indexOf(date);
    return pad.left + (i / (allDates.length - 1)) * plotW;
  };
  const yFor = (value: number) => pad.top + plotH * (1 - value / yMax);

  const paths = series.map((s) => {
    const pts = s.points
      .slice()
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((p) => ({ x: xFor(p.date), y: yFor(p.value), value: p.value }));
    const line = pts.map((p) => `${p.x},${p.y}`).join(" ");
    const first = pts[0];
    const last = pts[pts.length - 1];
    const area = pts.length
      ? `M${first.x},${pad.top + plotH} L${pts.map((p) => `${p.x},${p.y}`).join(" L")} L${last.x},${pad.top + plotH} Z`
      : "";
    return { line, area, last };
  });

  const labelIdx = [0, Math.floor((allDates.length - 1) / 2), allDates.length - 1].filter(
    (v, i, a) => a.indexOf(v) === i && allDates[v],
  );
  const xLabels = labelIdx.map((i) => ({
    x: xFor(allDates[i]),
    label: shortDate(allDates[i]),
  }));

  return { width, height, pad, paths, yMax, xLabels };
}

function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso.slice(5);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
}
