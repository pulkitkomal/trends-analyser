from app.models import Comment, Post, SourceKind
from app.services.analyze import build_digest, comment_insights, keyword_stats, recurring_trends


def test_keyword_phrases_and_no_html_junk():
    posts = [
        Post(
            topic_id=1,
            source=SourceKind.hn,
            external_id="1",
            title="Unofficial Switch ports surge",
            body="community fan port for steam deck. steam deck users love it.",
            score=10,
        ),
        Post(
            topic_id=1,
            source=SourceKind.github,
            external_id="2",
            title="steam deck fan port",
            body="&quot;x27&quot; href= github repo for steam deck",
            score=4,
        ),
    ]
    comments = [
        Comment(
            topic_id=1,
            post_id=1,
            source=SourceKind.hn,
            external_id="c1",
            body="Works great on Steam Deck after the latest fan port build from github.",
            score=5,
            author="alice",
        )
    ]
    kws = keyword_stats(posts, comments, limit=12)
    terms = [t for t, _, _ in kws]
    assert "steam deck" in terms or any("steam" in t for t in terms)
    assert "x27" not in terms
    assert "quot" not in terms
    rec = recurring_trends(posts, comments, kws)
    assert rec
    insights = comment_insights(comments)
    assert insights
    md = build_digest("Unofficial ports", kws, posts, insights, rec)
    assert "talking about" in md
    assert "alice" in md
