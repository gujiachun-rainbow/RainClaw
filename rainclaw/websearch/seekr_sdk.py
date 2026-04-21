"""seekr_sdk — lightweight client for the RainClaw websearch microservice.

Designed to be COPY'd into sandbox containers as a single-file module.
Sandbox scripts and @tool functions can use:

    from seekr_sdk import web_search, web_crawl, web_crawl_many
"""

from __future__ import annotations

import os
from typing import Any

import httpx

_WEBSEARCH_URL = os.environ.get("WEBSEARCH_URL", "http://websearch:8068")
_API_KEY = os.environ.get("WEBSEARCH_API_KEY", "")
_TIMEOUT = 120


def _headers() -> dict[str, str]:
    h: dict[str, str] = {"Content-Type": "application/json"}
    if _API_KEY:
        h["apikey"] = _API_KEY
    return h


def _post(path: str, json: dict, *, timeout: int | None = None) -> dict:
    url = f"{_WEBSEARCH_URL}{path}"
    resp = httpx.post(url, json=json, headers=_headers(), timeout=timeout or _TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def web_search(query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Search the web via the websearch microservice.

    Returns a list of dicts with keys: ``title``, ``url``, ``content``.
    """
    data = _post("/web_search", {"query": query, "limit": limit})
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in data.get("results", [])
    ]


def web_crawl(url: str) -> str:
    """Crawl a single URL and return its extracted text content."""
    data = _post("/crawl_urls", {"urls": [url]})
    return data.get("results", {}).get(url, "")


def web_crawl_many(urls: list[str]) -> dict[str, str]:
    """Crawl multiple URLs and return a mapping of URL → text."""
    data = _post("/crawl_urls", {"urls": urls})
    results: dict[str, str] = data.get("results", {})
    for u in data.get("failed_urls", []):
        results.setdefault(u, "")
    return results
