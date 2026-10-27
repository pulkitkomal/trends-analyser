from __future__ import annotations

import html
import re
from collections import Counter, defaultdict

from app.adapters.recency import by_recency
from app.models import Comment, Post
from app.schemas import CommentInsight, RecurringOut

STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "it",
    "this", "that", "with", "as", "be", "are", "was", "were", "by", "from",
    "at", "you", "your", "we", "they", "i", "not", "but", "if", "have", "has",
    "had", "will", "can", "just", "about", "into", "http", "https", "www",
    "com", "org", "net", "html", "href", "src", "like", "what", "when",
    "there", "their", "them", "then", "than", "also", "more", "some", "any",
    "all", "out", "our", "how", "why", "who", "which", "would", "could",
    "should", "been", "being", "does", "did", "dont", "it's", "its", "via",
    "new", "one", "two", "get", "got", "use", "using", "used", "still",
}

JUNK = {
    "quot", "amp", "nbsp", "x27", "apos", "lt", "gt", "txt", "log", "json",
    "xml", "png", "jpg", "jpeg", "svg", "gif", "css", "js", "md", "yml",
    "yaml", "toml", "pdf", "zip", "exe", "dll", "bin", "tmp", "null",
    "user", "users", "file", "files", "attachment", "attachments", "image",
    "images", "screenshot", "issue", "issues", "pull", "request", "http",
    "https", "www", "com", "html", "href",
}

TAG = re.compile(r"<[^>]+>")
TOKEN = re.compile(r"[a-z][a-z0-9]{2,}")
SIGNAL = re.compile(
    r"\b(works|broken|crash|crashes|port|ports|fork|github|release|android|"
    r"ios|switch|deck|steam|build|builds|legal|takedown|mirror|repo)\b",
    re.I,
)


def clean_text(text: str) -> str:
    return TAG.sub(" ", html.unescape(text or "")).strip()


def keyword_stats(posts: list[Post], comments: list[Comment], limit: int = 24) -> list[tuple[str, int, float]]:
    uni: Counter[str] = Counter()
    bi: Counter[str] = Counter()
    for text in _corpus(posts, comments):
        toks = _tokens(text)
        uni.update(toks)
        bi.update(f"{a} {b}" for a, b in zip(toks, toks[1:]))

    ranked: list[tuple[str, int, float]] = []
    seen: set[str] = set()
    for term, count in bi.most_common(limit):
        if count < 2:
            continue
        ranked.append((term, count, float(count) * 2.2))
        seen.add(term)
    for term, count in uni.most_common(limit * 3):
        if not _keep(term) or any(term in s for s in seen):
            continue
        ranked.append((term, count, float(count)))
        seen.add(term)
        if len(ranked) >= limit:
            break
    ranked.sort(key=lambda row: row[2], reverse=True)
    return ranked[:limit]


def recurring_trends(posts: list[Post], comments: list[Comment], keywords: list[tuple[str, int, float]]) -> list[RecurringOut]:
    buckets: dict[str, set[str]] = defaultdict(set)
    for p in posts:
        blob = clean_text(f"{p.title} {p.body}").lower()
        for term, _, _ in keywords:
            if term in blob:
                buckets[term].add(p.source.value)
    for c in comments:
        blob = clean_text(c.body).lower()
        for term, _, _ in keywords:
            if term in blob:
                buckets[term].add(c.source.value)

    out: list[RecurringOut] = []
    for term, count, _ in keywords:
        sources = buckets.get(term) or set()
        if len(sources) < 2 and count < 6:
            continue
        if len(sources) >= 2:
            why = f"Showing up across {len(sources)} sources"
        else:
            why = "Keeps coming up in the discussion"
        out.append(RecurringOut(term=term, count=count, sources=len(sources), why=why))
        if len(out) >= 8:
            break
    return out


def comment_insights(comments: list[Comment], limit: int = 10) -> list[CommentInsight]:
    scored: list[tuple[int, Comment, str]] = []
    for c in comments:
        body = clean_text(c.body)
        if len(body) < 50 or _noise_ratio(body) > 0.35:
            continue
        weight = c.score + (4 if SIGNAL.search(body) else 0) + min(len(body) // 80, 3)
        scored.append((weight, c, body))
    scored.sort(key=lambda row: row[0], reverse=True)
    out: list[CommentInsight] = []
    for weight, c, body in scored:
        out.append(
            CommentInsight(
                summary=_first_sentence(body),
                score=c.score,
                author=c.author,
                post_id=c.post_id,
                body=body[:500],
            )
        )
        if len(out) >= limit:
            break
    return out


def build_digest(
    topic_name: str,
    keywords: list[tuple[str, int, float]],
    posts: list[Post],
    insights: list[CommentInsight],
    recurring: list[RecurringOut] | None = None,
) -> str:
    lines = [f"# {topic_name}", "", "A short snapshot of what people are talking about.", ""]
    if recurring:
        lines += ["## What keeps coming up"]
        for r in recurring[:6]:
            lines.append(f"- **{r.term}** — {r.why.lower()}")
        lines.append("")
    lines += ["## Words people use"]
    for term, count, _ in keywords[:8]:
        lines.append(f"- {term} ({count})")
    lines += ["", "## Worth opening"]
    for p in by_recency(posts, limit=6):
        title = clean_text(p.title)
        link = f" ({p.url})" if p.url else ""
        lines.append(f"- {title}{link}")
    lines += ["", "## From the comments"]
    if not insights:
        lines.append("- Nothing standout yet.")
    for i in insights[:5]:
        who = f" — {i.author}" if i.author else ""
        lines.append(f"- {i.summary}{who}")
    return "\n".join(lines)


def _corpus(posts: list[Post], comments: list[Comment]) -> list[str]:
    texts = [f"{p.title} {p.body}" for p in posts]
    texts += [c.body for c in comments]
    return texts


def _tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN.finditer(clean_text(text)) if _keep(m.group(0).lower())]


def _keep(term: str) -> bool:
    if term in STOP or term in JUNK or term.isdigit() or len(term) < 3:
        return False
    if term[0].isdigit():
        return False
    return True


def _noise_ratio(text: str) -> float:
    if not text:
        return 1.0
    letters = sum(ch.isalpha() or ch.isspace() for ch in text)
    return 1 - letters / len(text)


def _first_sentence(text: str) -> str:
    chunk = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return chunk[:200]
