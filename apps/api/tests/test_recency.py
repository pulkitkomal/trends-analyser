from datetime import datetime, timedelta, timezone

from app.adapters.base import FetchedPost
from app.adapters.recency import by_recency, github_query, is_recent, keep_recent, unique_posts


def test_keep_recent_drops_old_posts():
    now = datetime.now(timezone.utc)
    fresh = FetchedPost(external_id="n", title="new", created_at=now - timedelta(days=2))
    stale = FetchedPost(external_id="o", title="old", created_at=now - timedelta(days=400))
    kept = keep_recent([stale, fresh], days=45)
    assert [p.external_id for p in kept] == ["n"]


def test_by_recency_newest_first():
    older = FetchedPost(external_id="a", title="a", created_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = FetchedPost(external_id="b", title="b", created_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert [p.external_id for p in by_recency([older, newer])] == ["b", "a"]


def test_github_query_adds_pushed_filter():
    q = github_query("unofficial game ports", days=45)
    assert "pushed:>" in q
    assert "unofficial game ports" in q


def test_unique_posts_drops_same_url():
    a = FetchedPost(external_id="1", title="A", url="https://example.com/x")
    b = FetchedPost(external_id="2", title="B", url="https://example.com/x?utm=1")
    assert len(unique_posts([a, b])) == 1


def test_naive_datetime_counts_as_recent():
    naive = datetime.now(timezone.utc).replace(tzinfo=None)
    assert is_recent(naive, days=1)
