from datetime import datetime, timezone

import httpx

from app.adapters.base import FetchedComment, FetchedPost
from app.adapters.recency import RECENT_DAYS, keep_recent
from app.config import settings

PUBLIC = "https://public.api.bsky.app"


def fetch_posts(query: str, limit: int = 15) -> list[FetchedPost]:
    # shortcut: public search; upgrade to authenticated app password session if rate-limited
    with httpx.Client(timeout=30) as client:
        r = client.get(
            f"{PUBLIC}/xrpc/app.bsky.feed.searchPosts",
            params={"q": query, "limit": limit, "sort": "latest"},
        )
        if r.status_code >= 400:
            return []
        posts: list[FetchedPost] = []
        for item in r.json().get("posts", []):
            record = item.get("record") or {}
            author = (item.get("author") or {}).get("handle") or ""
            uri = item.get("uri") or ""
            text = record.get("text") or ""
            like = int((item.get("likeCount") or 0))
            reply_count = int((item.get("replyCount") or 0))
            comments: list[FetchedComment] = []
            if reply_count and uri:
                comments = _thread(client, uri, limit=8)
            posts.append(
                FetchedPost(
                    external_id=f"bsky:{uri}",
                    title=(text[:120] + "…") if len(text) > 120 else text or "(post)",
                    body=text,
                    url=_web_url(uri, author),
                    author=author,
                    score=like,
                    comment_count=reply_count,
                    created_at=_parse(record.get("createdAt")),
                    comments=comments,
                )
            )
        recent = keep_recent(posts, days=RECENT_DAYS) or keep_recent(posts, days=90)
        return (recent or posts)[:limit]


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _thread(client: httpx.Client, uri: str, limit: int) -> list[FetchedComment]:
    r = client.get(f"{PUBLIC}/xrpc/app.bsky.feed.getPostThread", params={"uri": uri, "depth": 2})
    if r.status_code >= 400:
        return []
    thread = (r.json().get("thread") or {}).get("replies") or []
    out: list[FetchedComment] = []
    for node in thread:
        if len(out) >= limit:
            break
        post = node.get("post") or {}
        record = post.get("record") or {}
        text = record.get("text") or ""
        if not text:
            continue
        out.append(
            FetchedComment(
                external_id=f"bsky:{post.get('uri')}",
                body=text,
                author=(post.get("author") or {}).get("handle") or "",
                score=int(post.get("likeCount") or 0),
            )
        )
    return out


def _web_url(uri: str, handle: str) -> str:
    # at://did:plc:.../app.bsky.feed.post/rkey
    parts = uri.split("/")
    rkey = parts[-1] if parts else ""
    if handle and rkey:
        return f"https://bsky.app/profile/{handle}/post/{rkey}"
    return ""


def _unused_auth_note() -> None:
    # credentials reserved for later session auth
    _ = (settings.bluesky_handle, settings.bluesky_app_password)
