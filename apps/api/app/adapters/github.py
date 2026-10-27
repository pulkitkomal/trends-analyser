from datetime import datetime, timezone

import httpx

from app.adapters.base import FetchedComment, FetchedPost
from app.adapters.recency import RECENT_DAYS, by_recency, github_query, keep_recent
from app.config import settings

API = "https://api.github.com"


def fetch_posts(query: str, limit: int = 10) -> list[FetchedPost]:
    posts = _search(query, limit, days=RECENT_DAYS)
    if len(posts) < 3:
        wider = _search(query, limit, days=90)
        posts = keep_recent(posts + wider, days=90) or by_recency(wider, limit=limit)
    return _cap_authors(posts)[:limit]


def _cap_authors(posts: list[FetchedPost], per_author: int = 2) -> list[FetchedPost]:
    counts: dict[str, int] = {}
    out: list[FetchedPost] = []
    for post in posts:
        author = post.author or ""
        if author and counts.get(author, 0) >= per_author:
            continue
        if author:
            counts[author] = counts.get(author, 0) + 1
        out.append(post)
    return out


def _search(query: str, limit: int, days: int | None) -> list[FetchedPost]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "trends-analyser"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    q = query if " " in query or ":" in query else f"{query} in:name,description,readme"
    if days:
        q = github_query(q, days)
    with httpx.Client(timeout=30, headers=headers) as client:
        r = client.get(
            f"{API}/search/repositories",
            params={"q": q, "sort": "updated", "order": "desc", "per_page": limit},
        )
        if r.status_code == 403:
            return []
        r.raise_for_status()
        posts: list[FetchedPost] = []
        for repo in r.json().get("items", []):
            full_name = repo["full_name"]
            comments = _issues(client, full_name, limit=5)
            posts.append(
                FetchedPost(
                    external_id=f"gh:{repo['id']}",
                    title=full_name,
                    body=(repo.get("description") or "")[:2000],
                    url=repo.get("html_url") or "",
                    author=(repo.get("owner") or {}).get("login") or "",
                    score=int(repo.get("stargazers_count") or 0),
                    comment_count=len(comments),
                    created_at=_parse(repo.get("pushed_at") or repo.get("updated_at")),
                    comments=comments,
                )
            )
        return posts


def _issues(client: httpx.Client, full_name: str, limit: int) -> list[FetchedComment]:
    r = client.get(
        f"{API}/repos/{full_name}/issues",
        params={"state": "all", "sort": "updated", "per_page": limit},
    )
    if r.status_code >= 400:
        return []
    out: list[FetchedComment] = []
    for issue in r.json():
        if "pull_request" in issue:
            continue
        out.append(
            FetchedComment(
                external_id=f"gh-issue:{issue['id']}",
                body=f"{issue.get('title', '')}\n\n{(issue.get('body') or '')[:1500]}".strip(),
                author=(issue.get("user") or {}).get("login") or "",
                score=int(issue.get("comments") or 0),
                created_at=_parse(issue.get("updated_at") or issue.get("created_at")),
            )
        )
    return out


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None
