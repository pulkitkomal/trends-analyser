from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import mktime

import feedparser

from app.adapters.base import FetchedPost
from app.adapters.recency import RECENT_DAYS, by_recency, keep_recent


def fetch_posts(feed_url: str, limit: int = 20) -> list[FetchedPost]:
    parsed = feedparser.parse(feed_url)
    posts: list[FetchedPost] = []
    for entry in parsed.entries[: max(limit * 3, 20)]:
        link = getattr(entry, "link", "") or ""
        title = getattr(entry, "title", "") or link or "(untitled)"
        body = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        author = getattr(entry, "author", "") or ""
        created = _entry_date(entry)
        external = getattr(entry, "id", None) or link or title
        posts.append(
            FetchedPost(
                external_id=f"rss:{external}",
                title=title,
                body=_strip_tags(body)[:2000],
                url=link,
                author=author,
                created_at=created,
            )
        )
    recent = keep_recent(posts, days=RECENT_DAYS) or keep_recent(posts, days=90)
    return (recent or by_recency(posts))[:limit]


def _entry_date(entry) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
    if getattr(entry, "published", None):
        try:
            dt = parsedate_to_datetime(entry.published)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError, IndexError):
            return None
    return None


def _strip_tags(html: str) -> str:
    out: list[str] = []
    in_tag = False
    for ch in html:
        if ch == "<":
            in_tag = True
            continue
        if ch == ">":
            in_tag = False
            continue
        if not in_tag:
            out.append(ch)
    return "".join(out).strip()
