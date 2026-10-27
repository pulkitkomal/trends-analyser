from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SourceKind(str, Enum):
    github = "github"
    hn = "hn"
    rss = "rss"
    bluesky = "bluesky"
    trends = "trends"
    reddit = "reddit"
    x = "x"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str = ""
    password_hash: str
    created_at: datetime = Field(default_factory=utcnow)


class AuthSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    token: str = Field(index=True, unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)


class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True, foreign_key="user.id")
    name: str = Field(index=True)
    seed: str
    notes: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    last_ingested_at: Optional[datetime] = None


class Surface(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(index=True, foreign_key="topic.id")
    source: SourceKind
    label: str
    query: str
    enabled: bool = True
    meta_json: str = "{}"


class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(index=True, foreign_key="topic.id")
    source: SourceKind
    external_id: str = Field(index=True)
    title: str
    body: str = ""
    url: str = ""
    author: str = ""
    score: int = 0
    comment_count: int = 0
    created_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=utcnow)
    surface_id: Optional[int] = Field(default=None, foreign_key="surface.id")


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(index=True, foreign_key="topic.id")
    post_id: int = Field(index=True, foreign_key="post.id")
    source: SourceKind
    external_id: str
    body: str
    author: str = ""
    score: int = 0
    created_at: Optional[datetime] = None
    parent_external_id: str = ""


class KeywordStat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(index=True, foreign_key="topic.id")
    term: str
    count: int
    score: float = 0.0


class InterestPoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(index=True, foreign_key="topic.id")
    term: str
    date: str
    value: float


class Digest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(index=True, foreign_key="topic.id")
    markdown: str
    created_at: datetime = Field(default_factory=utcnow)


class LlmReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(index=True, foreign_key="topic.id")
    briefing: str = ""
    themes_json: str = "[]"
    related_json: str = "{}"
    insights_json: str = "[]"
    created_at: datetime = Field(default_factory=utcnow)
