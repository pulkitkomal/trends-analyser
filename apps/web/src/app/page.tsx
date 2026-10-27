"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { api, type Topic } from "@/lib/api";
import { timeAgo } from "@/lib/format";

export default function HomePage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listTopics()
      .then(setTopics)
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load topics"));
  }, []);

  return (
    <Shell topics={topics}>
      <header className="page-head">
        <div>
          <p className="eyebrow">Listening</p>
          <h1>Your topics</h1>
          <p className="pulse">What’s being said right now — one channel per topic.</p>
        </div>
        <div className="actions">
          <Link className="btn btn-primary" href="/new">
            Follow a topic
          </Link>
        </div>
      </header>

      {error ? <p className="error">{error}</p> : null}

      {!topics.length && !error ? (
        <p className="empty">Nothing on the desk yet. Follow a topic to start listening.</p>
      ) : (
        <ul className="channels">
          {topics.map((t) => {
            const fresh = t.last_ingested_at && Date.now() - new Date(t.last_ingested_at).getTime() < 1000 * 60 * 60 * 24;
            return (
              <li key={t.id}>
                <Link className="channel" href={`/topics/${t.id}`}>
                  <span className={fresh ? "pip" : "pip off"} aria-hidden="true" />
                  <span>
                    <strong>{t.name}</strong>
                    <span className="meta">Heard {timeAgo(t.last_ingested_at).toLowerCase()}</span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </Shell>
  );
}
