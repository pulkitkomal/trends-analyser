import json

from sqlmodel import Session, select

from app.adapters import bluesky, github, hn, rss, trends
from app.adapters.recency import RECENT_DAYS, keep_recent, unique_posts
from app.models import Comment, Digest, InterestPoint, KeywordStat, LlmReport, Post, SourceKind, Surface, Topic, utcnow
from app.services.analyze import build_digest, comment_insights, keyword_stats, recurring_trends
from app.services.llm import enrich


def ingest_topic(session: Session, topic: Topic) -> Topic:
    surfaces = session.exec(
        select(Surface).where(Surface.topic_id == topic.id, Surface.enabled == True)  # noqa: E712
    ).all()

    # Clear prior derived rows for a fresh snapshot
    for model in (Post, Comment, KeywordStat, InterestPoint, Digest, LlmReport):
        for row in session.exec(select(model).where(model.topic_id == topic.id)).all():  # type: ignore[attr-defined]
            session.delete(row)
    session.commit()

    all_posts: list[Post] = []
    all_comments: list[Comment] = []
    trend_terms: list[str] = []

    for surface in surfaces:
        if surface.source == SourceKind.trends:
            trend_terms.append(surface.query)
            continue
        fetched = unique_posts(_fetch(surface))
        fetched = keep_recent(fetched, days=RECENT_DAYS) or keep_recent(fetched, days=90) or fetched
        for fp in fetched:
            post = Post(
                topic_id=topic.id,
                source=surface.source,
                external_id=fp.external_id,
                title=fp.title,
                body=fp.body,
                url=fp.url,
                author=fp.author,
                score=fp.score,
                comment_count=fp.comment_count or len(fp.comments),
                created_at=fp.created_at,
                surface_id=surface.id,
            )
            session.add(post)
            session.flush()
            all_posts.append(post)
            for fc in fp.comments:
                c = Comment(
                    topic_id=topic.id,
                    post_id=post.id,  # type: ignore[arg-type]
                    source=surface.source,
                    external_id=fc.external_id,
                    body=fc.body,
                    author=fc.author,
                    score=fc.score,
                    created_at=fc.created_at,
                    parent_external_id=fc.parent_external_id,
                )
                session.add(c)
                all_comments.append(c)

    if trend_terms:
        for row in trends.fetch_interest(trend_terms):
            session.add(
                InterestPoint(
                    topic_id=topic.id,
                    term=row["term"],
                    date=row["date"],
                    value=row["value"],
                )
            )

    session.flush()
    kws = keyword_stats(all_posts, all_comments)
    for term, count, score in kws:
        session.add(KeywordStat(topic_id=topic.id, term=term, count=count, score=score))

    insights = comment_insights(all_comments)
    recurring = recurring_trends(all_posts, all_comments, kws)
    md = build_digest(topic.name, kws, all_posts, insights, recurring)
    llm = enrich(topic, all_posts, all_comments)
    if llm:
        if llm["digest"]:
            md = llm["digest"]
        session.add(
            LlmReport(
                topic_id=topic.id,
                briefing=llm["briefing"],
                themes_json=json.dumps(llm["themes"]),
                related_json=json.dumps(llm["related"]),
                insights_json=json.dumps(llm["comment_insights"]),
            )
        )
    session.add(Digest(topic_id=topic.id, markdown=md))

    topic.last_ingested_at = utcnow()
    topic.updated_at = utcnow()
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic


def _fetch(surface: Surface):
    if surface.source == SourceKind.hn:
        return hn.fetch_posts(surface.query)
    if surface.source == SourceKind.github:
        return github.fetch_posts(surface.query)
    if surface.source == SourceKind.rss:
        return rss.fetch_posts(surface.query)
    if surface.source == SourceKind.bluesky:
        return bluesky.fetch_posts(surface.query)
    return []
