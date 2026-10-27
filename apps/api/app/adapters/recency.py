from datetime import datetime, timedelta, timezone
from typing import Iterable, TypeVar

RECENT_DAYS = 45

T = TypeVar("T")


def cutoff(days: int = RECENT_DAYS) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_recent(value: datetime | None, days: int = RECENT_DAYS) -> bool:
    dt = as_utc(value)
    return bool(dt and dt >= cutoff(days))


def by_recency(items: Iterable[T], *, limit: int | None = None) -> list[T]:
    ranked = sorted(
        items,
        key=lambda item: as_utc(getattr(item, "created_at", None))
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return ranked[:limit] if limit else ranked


def unique_posts(items: Iterable[T]) -> list[T]:
    seen: set[str] = set()
    out: list[T] = []
    for item in items:
        url = (getattr(item, "url", "") or "").split("?")[0].rstrip("/")
        key = url or getattr(item, "external_id", "") or getattr(item, "title", "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def keep_recent(items: Iterable[T], days: int = RECENT_DAYS) -> list[T]:
    recent = [item for item in items if is_recent(getattr(item, "created_at", None), days)]
    return by_recency(recent)


def github_query(query: str, days: int = RECENT_DAYS) -> str:
    if "pushed:" in query or "updated:" in query:
        return query
    return f"{query} pushed:>{cutoff(days).date().isoformat()}"


def hn_since(days: int = RECENT_DAYS) -> int:
    return int(cutoff(days).timestamp())
