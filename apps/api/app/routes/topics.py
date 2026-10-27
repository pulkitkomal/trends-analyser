import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Comment, Digest, InterestPoint, KeywordStat, LlmReport, Post, Surface, Topic, User, utcnow
from app.services.auth import current_user
from app.schemas import (
    CommentInsight,
    DigestOut,
    InterestOut,
    KeywordOut,
    PostOut,
    RelatedOut,
    SurfaceCreate,
    SurfaceOut,
    SurfacePatch,
    ThemeOut,
    TopicCreate,
    TopicDashboard,
    TopicOut,
)
from app.adapters.recency import by_recency
from app.services.analyze import comment_insights, recurring_trends
from app.services.discover import default_surfaces
from app.services.ingest import ingest_topic

router = APIRouter(prefix="/topics", tags=["topics"])


def owned_topic(topic_id: int, session: Session, user: User) -> Topic:
    topic = session.get(Topic, topic_id)
    if not topic or topic.user_id != user.id:
        raise HTTPException(404, "Topic not found")
    return topic


@router.get("", response_model=list[TopicOut])
def list_topics(session: Session = Depends(get_session), user: User = Depends(current_user)) -> list[Topic]:
    return list(
        session.exec(select(Topic).where(Topic.user_id == user.id).order_by(Topic.updated_at.desc())).all()
    )


@router.post("", response_model=TopicOut)
def create_topic(
    body: TopicCreate, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> Topic:
    topic = Topic(
        user_id=user.id,
        name=body.name.strip(),
        seed=body.seed.strip(),
        notes=body.notes.strip(),
    )
    session.add(topic)
    session.commit()
    session.refresh(topic)
    for surface in default_surfaces(topic.id, topic.seed):  # type: ignore[arg-type]
        session.add(surface)
    session.commit()
    session.refresh(topic)
    return topic


@router.get("/{topic_id}", response_model=TopicDashboard)
def get_dashboard(
    topic_id: int, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> TopicDashboard:
    topic = owned_topic(topic_id, session, user)
    surfaces = session.exec(select(Surface).where(Surface.topic_id == topic_id)).all()
    posts = by_recency(session.exec(select(Post).where(Post.topic_id == topic_id)).all())
    keywords = session.exec(
        select(KeywordStat).where(KeywordStat.topic_id == topic_id).order_by(KeywordStat.count.desc())
    ).all()
    interest = session.exec(select(InterestPoint).where(InterestPoint.topic_id == topic_id)).all()
    comments = session.exec(select(Comment).where(Comment.topic_id == topic_id)).all()
    digest = session.exec(
        select(Digest).where(Digest.topic_id == topic_id).order_by(Digest.created_at.desc())
    ).first()
    post_list = list(posts)
    comment_list = list(comments)
    insights = comment_insights(comment_list)
    kw_tuples = [(k.term, k.count, k.score) for k in keywords]
    report = session.exec(
        select(LlmReport).where(LlmReport.topic_id == topic_id).order_by(LlmReport.created_at.desc())
    ).first()
    briefing = ""
    themes: list[ThemeOut] = []
    related = RelatedOut()
    if report:
        briefing = report.briefing
        themes = [ThemeOut.model_validate(t) for t in json.loads(report.themes_json or "[]") if t.get("name")]
        related = RelatedOut.model_validate(json.loads(report.related_json or "{}"))
        llm_insights = json.loads(report.insights_json or "[]")
        if llm_insights:
            insights = [
                CommentInsight(
                    summary=str(i.get("summary") or ""),
                    score=0,
                    author=str(i.get("author") or ""),
                    post_id=0,
                    body=str(i.get("kind") or ""),
                )
                for i in llm_insights
                if i.get("summary")
            ]
    return TopicDashboard(
        topic=TopicOut.model_validate(topic),
        surfaces=[SurfaceOut.model_validate(s) for s in surfaces],
        posts=[PostOut.model_validate(p) for p in post_list],
        keywords=[KeywordOut(term=k.term, count=k.count, score=k.score) for k in keywords],
        interest=[InterestOut(term=i.term, date=i.date, value=i.value) for i in interest],
        comment_insights=insights,
        recurring=recurring_trends(post_list, comment_list, kw_tuples),
        briefing=briefing,
        themes=themes,
        related=related,
        digest=DigestOut(markdown=digest.markdown, created_at=digest.created_at) if digest else None,
    )


@router.post("/{topic_id}/refresh", response_model=TopicOut)
def refresh(
    topic_id: int, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> Topic:
    return ingest_topic(session, owned_topic(topic_id, session, user))


@router.get("/{topic_id}/surfaces", response_model=list[SurfaceOut])
def list_surfaces(
    topic_id: int, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> list[Surface]:
    owned_topic(topic_id, session, user)
    return list(session.exec(select(Surface).where(Surface.topic_id == topic_id)).all())


@router.post("/{topic_id}/surfaces", response_model=SurfaceOut)
def add_surface(
    topic_id: int,
    body: SurfaceCreate,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Surface:
    owned_topic(topic_id, session, user)
    surface = Surface(
        topic_id=topic_id,
        source=body.source,
        label=body.label.strip(),
        query=body.query.strip(),
        enabled=body.enabled,
    )
    session.add(surface)
    topic = session.get(Topic, topic_id)
    if topic:
        topic.updated_at = utcnow()
        session.add(topic)
    session.commit()
    session.refresh(surface)
    return surface


@router.patch("/surfaces/{surface_id}", response_model=SurfaceOut)
def patch_surface(
    surface_id: int,
    body: SurfacePatch,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Surface:
    surface = session.get(Surface, surface_id)
    if not surface:
        raise HTTPException(404, "Surface not found")
    owned_topic(surface.topic_id, session, user)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(surface, key, value)
    session.add(surface)
    session.commit()
    session.refresh(surface)
    return surface


@router.get("/{topic_id}/digest", response_model=DigestOut)
def get_digest(
    topic_id: int, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> DigestOut:
    owned_topic(topic_id, session, user)
    digest = session.exec(
        select(Digest).where(Digest.topic_id == topic_id).order_by(Digest.created_at.desc())
    ).first()
    if not digest:
        raise HTTPException(404, "No digest yet — refresh the topic first")
    return DigestOut(markdown=digest.markdown, created_at=digest.created_at)


@router.delete("/{topic_id}")
def delete_topic(
    topic_id: int, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> dict:
    topic = owned_topic(topic_id, session, user)
    for model in (LlmReport, Digest, InterestPoint, KeywordStat, Comment, Post, Surface):
        for row in session.exec(select(model).where(model.topic_id == topic_id)).all():  # type: ignore[attr-defined]
            session.delete(row)
    session.delete(topic)
    session.commit()
    return {"ok": True}
