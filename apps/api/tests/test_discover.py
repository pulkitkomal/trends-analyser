from app.models import SourceKind, Surface
from app.services.discover import default_surfaces, news_feed_url


def test_news_feed_url_encodes_seed():
    url = news_feed_url("forza horizon 2")
    assert url.startswith("https://news.google.com/rss/search?q=")
    assert "forza" in url


def test_default_surfaces_enable_news_first():
    surfaces = default_surfaces(1, "Large Language Models")
    assert surfaces[0].source == SourceKind.rss
    assert surfaces[0].enabled
    assert "news.google.com/rss/search" in surfaces[0].query
    kinds = [s.source for s in surfaces]
    assert SourceKind.hn in kinds
    assert SourceKind.github in kinds
    assert SourceKind.bluesky in kinds
    assert SourceKind.trends in kinds
    # Old HN frontpage stub is gone — news carries RSS.
    assert all(isinstance(s, Surface) for s in surfaces)
