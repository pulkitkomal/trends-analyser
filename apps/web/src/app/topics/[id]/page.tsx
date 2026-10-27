"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Shell } from "@/components/Shell";
import { api, type Dashboard, type Topic } from "@/lib/api";
import { sourceName, timeAgo } from "@/lib/format";

export default function TopicPage() {
  const params = useParams();
  const id = Number(params.id);
  const router = useRouter();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [source, setSource] = useState("rss");
  const [label, setLabel] = useState("");
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    try {
      const [t, d] = await Promise.all([api.listTopics(), api.dashboard(id)]);
      setTopics(t);
      setDash(d);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn’t load this topic");
    }
  }, [id]);

  useEffect(() => {
    if (!Number.isFinite(id)) return;
    load();
  }, [id, load]);

  const interestLatest = useMemo(() => {
    if (!dash) return [];
    const byTerm = new Map<string, { date: string; value: number }>();
    for (const row of dash.interest) {
      const prev = byTerm.get(row.term);
      if (!prev || row.date > prev.date) byTerm.set(row.term, { date: row.date, value: row.value });
    }
    return [...byTerm.entries()].map(([term, v]) => ({ term, ...v }));
  }, [dash]);

  const liveInterest = interestLatest.filter((row) => row.value > 0);
  const [lead, rest] = splitLead(dash?.briefing || "");

  async function refresh() {
    setBusy(true);
    try {
      await api.refresh(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  async function toggleSurface(surfaceId: number, enabled: boolean) {
    await api.patchSurface(surfaceId, { enabled });
    await load();
  }

  async function addSurface(e: FormEvent) {
    e.preventDefault();
    await api.addSurface(id, { source, label, query, enabled: true });
    setLabel("");
    setQuery("");
    await load();
  }

  async function removeTopic() {
    if (!confirm("Stop following this topic?")) return;
    await api.deleteTopic(id);
    router.push("/");
    router.refresh();
  }

  function copyDigest() {
    if (!dash?.digest) return;
    navigator.clipboard.writeText(dash.digest.markdown);
  }

  const themes = dash?.themes?.length ? dash.themes : (dash?.recurring || []).map((r) => ({ name: r.term, why: r.why }));
  const liveSources = dash?.surfaces.filter((s) => s.enabled).length ?? 0;

  return (
    <Shell topics={topics}>
      {!dash && !error ? <p className="empty">Loading…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {dash ? (
        <>
          <header className="page-head">
            <div>
              <p className="eyebrow">Topic</p>
              <h1>{dash.topic.name}</h1>
              <p className="pulse">
                <span>
                  <b>{dash.posts.length}</b> posts
                </span>
                <span>
                  <b>{liveSources}</b> sources
                </span>
                <span>
                  <b>{themes.length}</b> themes
                </span>
                <span>{timeAgo(dash.topic.last_ingested_at)}</span>
              </p>
            </div>
            <div className="actions">
              <button className="btn btn-primary" onClick={refresh} disabled={busy}>
                {busy ? "Updating…" : "Update now"}
              </button>
              <button className="btn" onClick={copyDigest} disabled={!dash.digest || busy}>
                Copy summary
              </button>
            </div>
          </header>

          {busy ? (
            <div className="update-progress" role="status" aria-live="polite" aria-busy="true">
              <div className="update-track">
                <div className="update-fill" />
              </div>
              <p>Updating this topic — checking sources and writing a new summary.</p>
            </div>
          ) : null}

          {dash.briefing ? (
            <section className="lede">
              <p className="lede-kicker">Written summary</p>
              <p className="lede-first">{lead}</p>
              {rest ? <p className="lede-rest">{rest}</p> : null}
            </section>
          ) : (
            <section className="lede">
              <p className="empty">Update this topic to write the first summary.</p>
            </section>
          )}

          <div className="dash">
            <section className="block span-5">
              <h2>Coming up again</h2>
              <p className="block-muted">Themes that show up in more than one place.</p>
              {themes.length ? (
                <ul className="theme-list">
                  {themes.map((t) => (
                    <li key={t.name}>
                      <strong className={dash.themes?.length ? undefined : "title-case"}>{t.name}</strong>
                      <div className="meta">{t.why}</div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty">Update this topic to see repeating themes.</p>
              )}
            </section>

            <section className="block span-7">
              <h2>Words people use</h2>
              <p className="block-muted">Phrases that keep appearing in posts and replies.</p>
              <div className="chip-row">
                {dash.keywords.slice(0, 14).map((k) => (
                  <span className="chip" key={k.term}>
                    {k.term}
                  </span>
                ))}
                {!dash.keywords.length ? <p className="empty">Update to see the language people use.</p> : null}
              </div>
              {liveInterest.length ? (
                <div className="interest-bars" aria-label="Search interest">
                  {liveInterest.map((row) => (
                    <div className="bar" key={row.term}>
                      <span>{row.term}</span>
                      <span>{Math.round(row.value)}</span>
                      <div className="bar-track">
                        <div className="bar-fill" style={{ width: `${Math.min(100, row.value)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </section>

            <section className="block span-7">
              <h2>The wire</h2>
              {dash.posts.length ? (
                <ol className="wire">
                  {dash.posts.slice(0, 20).map((p) => (
                    <li key={p.id}>
                      <div className="wire-meta">
                        <time>{p.created_at ? timeAgo(p.created_at) : "—"}</time>
                        <span className="stamp">{sourceName(p.source)}</span>
                      </div>
                      <a href={p.url || undefined} target="_blank" rel="noreferrer">
                        {p.title}
                      </a>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="empty">No posts yet — tap Update now.</p>
              )}
            </section>

            <section className="block span-5">
              <h2>From the comments</h2>
              <p className="block-muted">Useful bits buried in replies.</p>
              <ul className="quote-list">
                {dash.comment_insights.map((c, i) => (
                  <li key={`${c.post_id}-${i}`}>
                    <q>{c.summary}</q>
                    <div className="meta">{c.author || "Someone"}</div>
                  </li>
                ))}
                {!dash.comment_insights.length ? <li className="empty">No standout comments yet.</li> : null}
              </ul>
            </section>

            <RelatedPanel related={dash.related} topicId={id} onChanged={load} />

            {dash.digest ? (
              <details className="fold span-12">
                <summary>Shareable summary</summary>
                <p className="block-muted">A short write-up you can paste into a community post.</p>
                <DigestView markdown={dash.digest.markdown} />
              </details>
            ) : null}

            <details className="fold span-12">
              <summary>Where we look</summary>
              <p className="block-muted">Turn a source off if it’s noisy. Changes apply the next time you update.</p>
              {dash.surfaces.map((s) => (
                <label className="surface-row" key={s.id}>
                  <input
                    type="checkbox"
                    checked={s.enabled}
                    onChange={(e) => toggleSurface(s.id, e.target.checked)}
                  />
                  <div>
                    <strong>{friendlySurface(s.label, s.source)}</strong>
                    <div className="meta">{sourceName(s.source)}</div>
                  </div>
                </label>
              ))}
              <button className="btn btn-quiet" type="button" onClick={() => setShowSources((v) => !v)}>
                {showSources ? "Hide extra sources" : "Add another source"}
              </button>
              {showSources ? (
                <form className="form" style={{ marginTop: 16 }} onSubmit={addSurface}>
                  <div className="field">
                    <label htmlFor="source">Place</label>
                    <select id="source" value={source} onChange={(e) => setSource(e.target.value)}>
                      <option value="rss">News feed</option>
                      <option value="hn">Hacker News</option>
                      <option value="github">GitHub</option>
                      <option value="bluesky">Bluesky</option>
                      <option value="trends">Google search</option>
                    </select>
                  </div>
                  <div className="field">
                    <label htmlFor="label">Name</label>
                    <input id="label" required value={label} onChange={(e) => setLabel(e.target.value)} />
                  </div>
                  <div className="field">
                    <label htmlFor="query">Search or feed address</label>
                    <input id="query" required value={query} onChange={(e) => setQuery(e.target.value)} />
                  </div>
                  <button className="btn" type="submit">
                    Add
                  </button>
                </form>
              ) : null}
              <div>
                <button className="btn btn-quiet danger-text" type="button" onClick={removeTopic}>
                  Stop following
                </button>
              </div>
            </details>
          </div>
        </>
      ) : null}
    </Shell>
  );
}

function RelatedPanel({
  related,
  topicId,
  onChanged,
}: {
  related: Dashboard["related"] | undefined;
  topicId: number;
  onChanged: () => Promise<void>;
}) {
  const r = related || { searches: [], names: [], places: [], topics: [], links: [] };
  const empty =
    !r.searches.length && !r.names.length && !r.places.length && !r.topics.length && !r.links.length;
  const [busy, setBusy] = useState("");

  async function follow(name: string, seed: string) {
    setBusy(name);
    try {
      await api.createTopic({ name, seed: seed || name });
      await onChanged();
    } finally {
      setBusy("");
    }
  }

  async function addPlace(place: { source: string; label: string; query: string }) {
    setBusy(place.query);
    try {
      await api.addSurface(topicId, {
        source: place.source || "hn",
        label: place.label || place.query,
        query: place.query,
        enabled: true,
      });
      await onChanged();
    } finally {
      setBusy("");
    }
  }

  if (empty) return null;

  return (
    <section className="block span-12">
      <h2>Related</h2>
      <p className="block-muted">Things that showed up nearby — add the ones you want to follow.</p>
      {r.names.length ? (
        <div className="chip-row" style={{ marginBottom: 12 }}>
          {r.names.map((n) => (
            <span className="chip" key={n}>
              {n}
            </span>
          ))}
        </div>
      ) : null}
      {r.searches.length ? (
        <p className="meta" style={{ marginBottom: 12 }}>
          Also search: {r.searches.join(" · ")}
        </p>
      ) : null}
      {r.topics.length || r.places.length ? (
        <ul className="related-list">
          {r.topics.map((t) => (
            <li key={t.name}>
              <div>
                <strong>{t.name}</strong>
                <div className="meta">Nearby topic</div>
              </div>
              <button className="btn btn-quiet" disabled={busy === t.name} onClick={() => follow(t.name, t.seed)}>
                {busy === t.name ? "Adding…" : "Follow"}
              </button>
            </li>
          ))}
          {r.places.map((p) => (
            <li key={`${p.source}-${p.query}`}>
              <div>
                <strong>{p.label || p.query}</strong>
                <div className="meta">
                  {sourceName(p.source)} · {p.query}
                </div>
              </div>
              <button className="btn btn-quiet" disabled={busy === p.query} onClick={() => addPlace(p)}>
                {busy === p.query ? "Adding…" : "Watch this"}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {r.links.length ? (
        <ul className="theme-list">
          {r.links.map((l) => (
            <li key={l.url}>
              <a href={l.url} target="_blank" rel="noreferrer">
                {l.title || l.url}
              </a>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function splitLead(text: string): [string, string] {
  const match = text.match(/^(.+?[.!?])\s+([\s\S]+)$/);
  return match ? [match[1], match[2]] : [text, ""];
}

function friendlySurface(label: string, source: string): string {
  return label.replace(/^(HN|GitHub|Bluesky|Trends):\s*/i, "").trim() || sourceName(source);
}

function DigestView({ markdown }: { markdown: string }) {
  return (
    <div className="digest-read">
      {markdown.split("\n").map((line, i) => {
        if (line.startsWith("# ")) return <h3 key={i}>{line.slice(2)}</h3>;
        if (line.startsWith("## ")) return <h4 key={i}>{line.slice(3)}</h4>;
        if (line.startsWith("- ")) return <p key={i}>{line.slice(2).replace(/\*\*/g, "")}</p>;
        if (!line.trim()) return null;
        return (
          <p key={i} className="block-muted">
            {line}
          </p>
        );
      })}
    </div>
  );
}
