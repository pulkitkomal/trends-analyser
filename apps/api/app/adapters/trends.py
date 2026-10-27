from __future__ import annotations

from typing import Any


def fetch_interest(terms: list[str]) -> list[dict[str, Any]]:
    """Return [{term, date, value}, ...] via Google Trends.

    shortcut: pytrends is unofficial and flaky; cache results and tolerate empty.
    """
    if not terms:
        return []
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return []

    try:
        pytrends = TrendReq(hl="en-US", tz=0)
        # Google Trends caps compared keywords
        chunk = terms[:5]
        pytrends.build_payload(chunk, timeframe="today 1-m")
        df = pytrends.interest_over_time()
    except Exception:
        return []

    if df is None or df.empty:
        return []

    rows: list[dict[str, Any]] = []
    for term in chunk:
        if term not in df.columns:
            continue
        for idx, value in df[term].items():
            rows.append({"term": term, "date": str(idx.date()), "value": float(value)})
    return rows
