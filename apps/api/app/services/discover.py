from urllib.parse import quote

from sqlmodel import Session, select

from app.models import SourceKind, Surface


def news_feed_url(seed: str) -> str:
    return f"https://news.google.com/rss/search?q={quote(seed.strip())}&hl=en-US&gl=US&ceid=US:en"


def default_surfaces(topic_id: int, seed: str) -> list[Surface]:
    """Bootstrap editable discovery map from the topic seed."""
    seed = seed.strip()
    return [
        Surface(
            topic_id=topic_id,
            source=SourceKind.rss,
            label=f"News: {seed}",
            query=news_feed_url(seed),
            enabled=True,
        ),
        Surface(
            topic_id=topic_id,
            source=SourceKind.hn,
            label=f"HN: {seed}",
            query=seed,
            enabled=True,
        ),
        Surface(
            topic_id=topic_id,
            source=SourceKind.bluesky,
            label=f"Bluesky: {seed}",
            query=seed,
            enabled=True,
        ),
        Surface(
            topic_id=topic_id,
            source=SourceKind.github,
            label=f"GitHub: {seed}",
            query=seed,
            enabled=True,
        ),
        Surface(
            topic_id=topic_id,
            source=SourceKind.trends,
            label=f"Trends: {seed}",
            query=seed,
            enabled=True,
        ),
    ]


def ensure_default_surfaces(session: Session, topic_id: int, seed: str) -> None:
    """Add missing high-signal defaults (esp. Google News) to older topics."""
    existing = list(session.exec(select(Surface).where(Surface.topic_id == topic_id)).all())
    have_news = any(
        s.source == SourceKind.rss and "news.google.com/rss/search" in (s.query or "") for s in existing
    )
    if have_news:
        return
    seed = seed.strip()
    session.add(
        Surface(
            topic_id=topic_id,
            source=SourceKind.rss,
            label=f"News: {seed}",
            query=news_feed_url(seed),
            enabled=True,
        )
    )
    session.commit()
