"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"in" | "up">("in");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.me().then(() => router.replace("/")).catch(() => {});
  }, [router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "up") {
        await api.register({ name, email, password });
      } else {
        await api.login({ email, password });
      }
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn’t sign in");
      setBusy(false);
    }
  }

  return (
    <main className="gate">
      <div className="gate-copy">
        <p className="eyebrow">Heard</p>
        <h1>What people are saying</h1>
        <p>Sign in to listen to a topic — GitHub, Hacker News, news feeds, Bluesky, and search.</p>
      </div>
      <form className="form gate-form" onSubmit={onSubmit}>
        {mode === "up" ? (
          <div className="field">
            <label htmlFor="name">Name</label>
            <input id="name" required value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
          </div>
        ) : null}
        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            inputMode="email"
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "up" ? "new-password" : "current-password"}
          />
        </div>
        {error ? <p className="error">{error}</p> : null}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Working…" : mode === "up" ? "Create account" : "Sign in"}
        </button>
        <button
          className="btn btn-quiet"
          type="button"
          onClick={() => {
            setMode(mode === "up" ? "in" : "up");
            setError("");
          }}
        >
          {mode === "up" ? "I already have an account" : "Create an account"}
        </button>
      </form>
    </main>
  );
}
