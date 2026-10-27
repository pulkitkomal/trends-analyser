from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import SourceKind


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    seed: str = Field(min_length=1, max_length=500)
    notes: str = ""


class TopicOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    seed: str
    notes: str
    created_at: datetime
    updated_at: datetime
    last_ingested_at: Optional[datetime] = None


class SurfaceCreate(BaseModel):
    source: SourceKind
    label: str
    query: str
    enabled: bool = True


class SurfaceOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    topic_id: int
    source: SourceKind
    label: str
    query: str
    enabled: bool


class SurfacePatch(BaseModel):
    enabled: Optional[bool] = None
    label: Optional[str] = None
    query: Optional[str] = None


class PostOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    source: SourceKind
    title: str
    body: str
    url: str
    author: str
    score: int
    comment_count: int
    created_at: Optional[datetime] = None


class CommentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    post_id: int
    source: SourceKind
    body: str
    author: str
    score: int
    url_hint: str = ""


class KeywordOut(BaseModel):
    term: str
    count: int
    score: float


class InterestOut(BaseModel):
    term: str
    date: str
    value: float


class DigestOut(BaseModel):
    model_config = {"from_attributes": True}

    markdown: str
    created_at: datetime


class CommentInsight(BaseModel):
    summary: str
    score: int
    author: str
    post_id: int
    body: str


class RecurringOut(BaseModel):
    term: str
    count: int
    sources: int
    why: str


class ThemeOut(BaseModel):
    name: str
    why: str = ""


class RelatedPlace(BaseModel):
    source: str = ""
    label: str = ""
    query: str = ""


class RelatedTopic(BaseModel):
    name: str
    seed: str = ""


class RelatedLink(BaseModel):
    title: str = ""
    url: str


class RelatedOut(BaseModel):
    searches: list[str] = []
    names: list[str] = []
    places: list[RelatedPlace] = []
    topics: list[RelatedTopic] = []
    links: list[RelatedLink] = []


class TopicDashboard(BaseModel):
    topic: TopicOut
    surfaces: list[SurfaceOut]
    posts: list[PostOut]
    keywords: list[KeywordOut]
    interest: list[InterestOut]
    comment_insights: list[CommentInsight]
    recurring: list[RecurringOut] = []
    briefing: str = ""
    themes: list[ThemeOut] = []
    related: RelatedOut = RelatedOut()
    digest: Optional[DigestOut] = None
