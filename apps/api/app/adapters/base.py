from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FetchedComment:
    external_id: str
    body: str
    author: str = ""
    score: int = 0
    created_at: Optional[datetime] = None
    parent_external_id: str = ""


@dataclass
class FetchedPost:
    external_id: str
    title: str
    body: str = ""
    url: str = ""
    author: str = ""
    score: int = 0
    comment_count: int = 0
    created_at: Optional[datetime] = None
    comments: list[FetchedComment] = field(default_factory=list)
