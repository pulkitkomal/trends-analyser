"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/Shell";
import { api, type Topic } from "@/lib/api";

export default function NewTopicPage() {
  const router = useRouter();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listTopics().then(setTopics).catch(() => setTopics([]));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const topic = await api.createTopic({ name, seed: name, notes });
      router.push(`/topics/${topic.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn’t create that topic");
      setBusy(false);
    }
  }

  return (
    <Shell topics={topics}>
      <header className="page-head">
        <div>
          <p className="eyebrow">New</p>
          <h1>Follow a topic</h1>
          <p className="pulse">Give it a name. We’ll look for conversations that match.</p>
        </div>
      </header>
      <form className="form" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="name">Topic</label>
          <input
            id="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Unofficial game ports"
          />
        </div>
        <div className="field">
          <label htmlFor="notes">Anything to remember? (optional)</label>
          <textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Adding…" : "Start following"}
        </button>
      </form>
    </Shell>
  );
}
