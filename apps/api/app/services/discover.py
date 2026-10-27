from app.models import SourceKind, Surface


def default_surfaces(topic_id: int, seed: str) -> list[Surface]:
    """Bootstrap editable discovery map from the topic seed."""
    seed = seed.strip()
    return [
        Surface(
            topic_id=topic_id,
            source=SourceKind.hn,
            label=f"HN: {seed}",
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
            source=SourceKind.bluesky,
            label=f"Bluesky: {seed}",
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
        Surface(
            topic_id=topic_id,
            source=SourceKind.rss,
            label="HN RSS (frontpage)",
            query="https://hnrss.org/frontpage",
            enabled=False,
        ),
    ]
