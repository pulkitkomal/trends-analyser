from app.services.llm import _normalize


def test_normalize_fills_related():
    out = _normalize(
        {
            "briefing": "Ports are heating up.",
            "themes": [{"name": "Steam Deck", "why": "Lots of posts"}],
            "comment_insights": [{"summary": "Works on Deck", "kind": "claim", "author": "a"}],
            "related": {"searches": ["fan port"], "topics": [{"name": "Emulation"}]},
            "digest": "# Hi",
        }
    )
    assert out["briefing"].startswith("Ports")
    assert out["related"]["searches"] == ["fan port"]
    assert out["related"]["topics"][0]["name"] == "Emulation"
