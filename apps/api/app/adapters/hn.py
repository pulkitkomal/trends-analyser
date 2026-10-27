from datetime import datetime, timezone

import httpx

from app.adapters.base import FetchedComment, FetchedPost
from app.adapters.recency import RECENT_DAYS, by_recency, hn_since, keep_recent

SEARCH = "https://hn.algolia.com/api/v1/search_by_date"
ITEM = "https://hn.algolia.com/api/v1/items"


def fetch_posts(query: str, limit: int = 15) -> list[FetchedPost]:
    posts = _search(query, limit, days=RECENT_DAYS)
    if len(posts) < 3:
        wider = _search(query, limit, days=90)
        posts = keep_recent(posts + wider, days=90) or by_recency(wider, limit=limit)
    return posts[:limit]


def _search(query: str, limit: int, days: int | None) -> list[FetchedPost]:
    params: dict[str, str | int] = {"query": query, "tags": "story", "hitsPerPage": limit}
    if days:
        params["numericFilters"] = f"created_at_i>{hn_since(days)}"
    with httpx.Client(timeout=30) as client:
        r = client.get(SEARCH, params=params)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        posts: list[FetchedPost] = []
        for h in hits:
            object_id = str(h.get("objectID", ""))
            comments: list[FetchedComment] = []
            try:
                item = client.get(f"{ITEM}/{object_id}").json()
                comments = _walk_comments(item.get("children") or [], limit=20)
            except Exception:
                pass
            created = h.get("created_at")
            posts.append(
                FetchedPost(
                    external_id=f"hn:{object_id}",
                    title=h.get("title") or "(untitled)",
                    body=h.get("story_text") or "",
                    url=h.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
                    author=h.get("author") or "",
                    score=int(h.get("points") or 0),
                    comment_count=int(h.get("num_comments") or 0),
                    created_at=_parse(created),
                    comments=comments,
                )
            )
        return posts


def _walk_comments(nodes: list, limit: int, out: list[FetchedComment] | None = None) -> list[FetchedComment]:
    out = out if out is not None else []
    for n in nodes:
        if len(out) >= limit:
            break
        text = (n.get("text") or "").strip()
        if text:
            out.append(
                FetchedComment(
                    external_id=f"hn:{n.get('id')}",
                    body=_strip_html(text),
                    author=n.get("author") or "",
                    score=0,
                    created_at=_parse(n.get("created_at")),
                    parent_external_id=f"hn:{n.get('parent_id')}" if n.get("parent_id") else "",
                )
            )
        _walk_comments(n.get("children") or [], limit, out)
    return out


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _strip_html(text: str) -> str:
    # shortcut: HN returns light HTML; upgrade to bleach if we need entity safety
    return (
        text.replace("<p>", "\n")
        .replace("</p>", "")
        .replace("<i>", "")
        .replace("</i>", "")
        .replace("&quot;", '"')
        .replace("&#x27;", "'")
        .replace("&gt;", ">")
        .replace("&lt;", "<")
        .replace("&amp;", "&")
    )
