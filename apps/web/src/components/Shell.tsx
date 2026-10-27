"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Topic, type User } from "@/lib/api";

export function Shell({
  topics,
  children,
}: {
  topics: Topic[];
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => router.replace("/login"));
  }, [router]);

  const onTopics = pathname === "/" || pathname.startsWith("/topics") || pathname === "/new";

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar" aria-label="Topics">
        <Link href="/" className="brand">
          <em>Heard</em>
          <strong>What people are saying</strong>
        </Link>
        <nav>
          <ul className="nav-list">
            <li className="nav-item">
              <Link href="/" aria-current={pathname === "/" ? "page" : undefined}>
                Listening
              </Link>
            </li>
            {topics.map((t) => {
              const href = `/topics/${t.id}`;
              return (
                <li key={t.id} className="nav-item">
                  <Link href={href} aria-current={pathname === href ? "page" : undefined}>
                    {t.name}
                  </Link>
                </li>
              );
            })}
            <li className="nav-item nav-action">
              <Link href="/new">Follow a topic</Link>
            </li>
          </ul>
        </nav>
        <div className="sidebar-foot">
          <Link href="/settings" className="user-chip">
            {user?.name || "Account"}
          </Link>
        </div>
      </aside>
      <main id="main" className="main">
        {children}
      </main>
      <nav className="tab-bar" aria-label="App">
        <Link href="/" aria-current={onTopics ? "page" : undefined}>
          Listening
        </Link>
        <Link href="/settings" aria-current={pathname.startsWith("/settings") ? "page" : undefined}>
          Account
        </Link>
      </nav>
    </div>
  );
}
