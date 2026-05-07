"""
SerpAPI integration — synchronous `requests` client (real organic URLs).
"""

from __future__ import annotations

from typing import Any

import requests

API_KEY = "23840f4b6072e6d69b26f2119b347ef7ffde1179a53918dbb80acb0684d767dd"


def build_code_serp_query(code: str, max_lines: int = 8, max_words: int = 14) -> str:
    """Build a short web search query from the first meaningful lines of code."""
    lines = (code or "").replace("\r\n", "\n").split("\n")
    taken: list[str] = []
    for line in lines[:max_lines]:
        s = line.strip()
        if not s:
            continue
        if s.startswith("#") or s.startswith("//"):
            continue
        if s.startswith("/*") or s.startswith("*"):
            continue
        taken.append(s)
    blob = " ".join(taken)[:800]
    words = blob.split()[:max_words]
    q = " ".join(words).strip()
    return q or "programming code snippet"


def search_sources(text: str) -> list[dict[str, Any]]:
    """Return up to 3 organic results with title, url, snippet, and placeholder similarity."""
    query = " ".join((text or "").split()[:10]) or "plagiarism check"
    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "api_key": API_KEY,
        "engine": "google",
        "num": "10",
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
    except Exception:
        return []

    results: list[dict[str, Any]] = []
    if "organic_results" in data:
        for item in (data.get("organic_results") or [])[:3]:
            link = item.get("link") or item.get("url") or ""
            if not link:
                continue
            snippet = item.get("snippet") or ""
            if isinstance(snippet, list):
                snippet = " ".join(str(x) for x in snippet)
            results.append(
                {
                    "title": item.get("title") or "Untitled",
                    "url": link,
                    "snippet": str(snippet),
                    "similarity": 80,  # placeholder; app.py replaces with semantic scores
                }
            )
    return results
