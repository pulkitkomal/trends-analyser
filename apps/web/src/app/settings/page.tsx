"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/Shell";
import { api, type Topic, type User } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [name, setName] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.me(), api.listTopics()])
      .then(([me, list]) => {
        setUser(me);
        setName(me.name);
        setTopics(list);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  async function onSave(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const next = await api.updateMe({ name });
      setUser(next);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn’t save");
    }
  }

  async function onSignOut() {
    await api.logout();
    router.replace("/login");
  }

  async function onDelete() {
    if (!confirm("Delete this account and every topic it follows? This cannot be undone.")) return;
    await api.deleteMe();
    router.replace("/login");
  }

  return (
    <Shell topics={topics}>
      <header className="page-head">
        <div>
          <p className="eyebrow">Account</p>
          <h1>Settings</h1>
        </div>
      </header>
      <form className="form" onSubmit={onSave}>
        <div className="field">
          <label htmlFor="name">Name</label>
          <input id="name" required value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" value={user?.email || ""} readOnly />
        </div>
        {error ? <p className="error">{error}</p> : null}
        {saved ? <p className="meta">Saved.</p> : null}
        <button className="btn btn-primary" type="submit">
          Save name
        </button>
      </form>
      <div className="settings-actions">
        <button className="btn" type="button" onClick={onSignOut}>
          Sign out
        </button>
        <button className="btn btn-quiet danger-text" type="button" onClick={onDelete}>
          Delete account
        </button>
      </div>
    </Shell>
  );
}
