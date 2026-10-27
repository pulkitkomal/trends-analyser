from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings
from app.models import Comment, Post, Topic
from app.adapters.recency import by_recency
from app.services.analyze import clean_text

SYSTEM = """You analyze public posts and comments for a trends dashboard.
Stay grounded in the provided text. Do not invent URLs.
Write about what is happening recently. Treat older posts as background, not current news.
If you infer a related search that is not in the text, put it in searches and keep it short.
Return JSON only with this shape:
{
  "briefing": "5-8 sentences on what is going on",
  "themes": [{"name": "short theme", "why": "one sentence"}],
  "comment_insights": [{"summary": "one sentence", "kind": "claim|watchout|name|link", "author": ""}],
  "related": {
    "searches": ["phrase"],
    "names": ["project or game"],
    "places": [{"source": "github|hn|bluesky|rss|trends", "label": "", "query": ""}],
    "topics": [{"name": "", "seed": ""}],
    "links": [{"title": "", "url": ""}]
  },
  "digest": "markdown summary with headings, credit original posts by title"
}"""


def enrich(topic: Topic, posts: list[Post], comments: list[Comment]) -> dict[str, Any] | None:
    if not settings.openai_api_key:
        return None
    payload = {
        "model": settings.openai_model,
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _bundle(topic, posts, comments)},
        ],
    }
    try:
        with httpx.Client(timeout=60) as client:
            r = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except Exception:
        return None
    return _normalize(data)


def _bundle(topic: Topic, posts: list[Post], comments: list[Comment]) -> str:
    post_bits = []
    for p in by_recency(posts, limit=12):
        post_bits.append(
            {
                "source": p.source.value,
                "title": clean_text(p.title)[:180],
                "url": p.url,
                "author": p.author,
                "posted": p.created_at.isoformat() if p.created_at else "",
                "body": clean_text(p.body)[:400],
            }
        )
    comment_bits = []
    for c in sorted(comments, key=lambda x: (x.score, len(x.body)), reverse=True)[:16]:
        body = clean_text(c.body)
        if len(body) < 40:
            continue
        comment_bits.append({"author": c.author, "body": body[:350]})
    return json.dumps(
        {"topic": topic.name, "seed": topic.seed, "posts": post_bits, "comments": comment_bits},
        ensure_ascii=False,
    )


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    related = data.get("related") if isinstance(data.get("related"), dict) else {}
    return {
        "briefing": str(data.get("briefing") or "").strip(),
        "themes": [t for t in data.get("themes") or [] if isinstance(t, dict) and t.get("name")][:8],
        "comment_insights": [
            i for i in data.get("comment_insights") or [] if isinstance(i, dict) and i.get("summary")
        ][:10],
        "related": {
            "searches": [str(x) for x in related.get("searches") or [] if x][:8],
            "names": [str(x) for x in related.get("names") or [] if x][:8],
            "places": [p for p in related.get("places") or [] if isinstance(p, dict) and p.get("query")][:8],
            "topics": [t for t in related.get("topics") or [] if isinstance(t, dict) and t.get("name")][:6],
            "links": [lk for lk in related.get("links") or [] if isinstance(lk, dict) and lk.get("url")][:6],
        },
        "digest": str(data.get("digest") or "").strip(),
    }
