"""xcom-rs CLI adapter for X search in the last30days pipeline.

Shells out to ``xcom-rs`` via ``dotenvx`` in non-interactive JSON mode and
normalizes the response into the same item shape consumed by the ranking
pipeline (matching ``bird_x.parse_bird_response`` / ``xai_x.parse_x_response``
output format).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import log
from .relevance import token_overlap_relevance as _compute_relevance

# Depth configurations: number of results to request
DEPTH_CONFIG = {
    "quick": 12,
    "default": 30,
    "deep": 60,
}

# Default dotenvx env file path
_DOTENVX_ENV_FILE = os.path.expanduser("~/.env")


def _log(msg: str) -> None:
    log.source_log("xcom-rs", msg, tty_only=False)


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for X search."""
    from .query import extract_core_subject
    return extract_core_subject(topic, max_words=5, strip_suffixes=True)


# ---------------------------------------------------------------------------
# Prerequisite detection
# ---------------------------------------------------------------------------

def is_xcom_rs_installed() -> bool:
    """Return True when the ``xcom-rs`` CLI binary is in PATH."""
    return shutil.which("xcom-rs") is not None


def is_dotenvx_installed() -> bool:
    """Return True when ``dotenvx`` is in PATH."""
    return shutil.which("dotenvx") is not None


def has_prerequisites() -> bool:
    """Return True when both ``xcom-rs`` and ``dotenvx`` are available."""
    return is_xcom_rs_installed() and is_dotenvx_installed()


def check_auth_context() -> bool:
    """Return True when the required auth env file exists.

    The mini convention is that ``~/.env`` contains the bearer token
    used by ``dotenvx run -f ~/.env -- xcom-rs ...``.
    """
    return os.path.isfile(_DOTENVX_ENV_FILE)


def is_available() -> bool:
    """Return True when xcom-rs can be used as an X backend."""
    return has_prerequisites() and check_auth_context()


def get_status() -> Dict[str, Any]:
    """Return a diagnostic status dict for xcom-rs prerequisites."""
    xcom_rs_ok = is_xcom_rs_installed()
    dotenvx_ok = is_dotenvx_installed()
    auth_ok = check_auth_context()
    available = xcom_rs_ok and dotenvx_ok and auth_ok

    missing: List[str] = []
    if not xcom_rs_ok:
        missing.append("xcom-rs not installed")
    if not dotenvx_ok:
        missing.append("dotenvx unavailable")
    if not auth_ok:
        missing.append("XCOM_RS_BEARER_TOKEN not available through ~/.env")

    return {
        "available": available,
        "xcom_rs_installed": xcom_rs_ok,
        "dotenvx_installed": dotenvx_ok,
        "auth_context": auth_ok,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# CLI execution
# ---------------------------------------------------------------------------

def _run_xcom_rs(query: str, limit: int, timeout: int) -> Dict[str, Any]:
    """Execute ``xcom-rs search recent`` via dotenvx and return parsed JSON.

    Returns a dict with ``"items"`` (list) and optionally ``"error"`` (str).
    """
    cmd = [
        "dotenvx", "run", "-f", _DOTENVX_ENV_FILE, "--",
        "xcom-rs", "search", "recent", query,
        "--limit", str(limit),
        "--output", "json",
        "--non-interactive",
    ]

    preexec = os.setsid if hasattr(os, "setsid") else None

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec,
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
            proc.wait(timeout=5)
            return {"error": f"xcom-rs timed out after {timeout}s", "items": []}

        if proc.returncode != 0:
            error = stderr.strip() if stderr else "xcom-rs search failed"
            return {"error": error, "items": []}

        output = (stdout or "").strip()
        if not output:
            return {"items": []}

        parsed = json.loads(output)
        if isinstance(parsed, list):
            return {"items": parsed}
        return parsed

    except json.JSONDecodeError as exc:
        return {"error": f"Invalid JSON from xcom-rs: {exc}", "items": []}
    except Exception as exc:
        return {"error": str(exc), "items": []}


# ---------------------------------------------------------------------------
# Search API
# ---------------------------------------------------------------------------

def search_x(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> Dict[str, Any]:
    """Search X via xcom-rs with automatic retry on 0 results.

    Mirrors the retry strategy of ``bird_x.search_x``.
    """
    limit = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    timeout = 30 if depth == "quick" else 45 if depth == "default" else 60

    core_topic = _extract_core_subject(topic)
    query = f"{core_topic} since:{from_date} until:{to_date}"

    _log(f"Searching: {query}")
    response = _run_xcom_rs(query, limit, timeout)

    items = parse_response(response, query=core_topic)

    # Retry with OR groups for multi-word queries
    core_words = core_topic.split()
    if not items and len(core_words) >= 2:
        from .query import extract_compound_terms
        compounds = extract_compound_terms(topic)
        if compounds:
            or_parts = " OR ".join(f'"{t}"' for t in compounds[:3])
            _log(f"0 results for '{core_topic}', retrying with OR groups: {or_parts}")
            query = f"({or_parts}) since:{from_date} until:{to_date}"
            response = _run_xcom_rs(query, limit, timeout)
            items = parse_response(response, query=core_topic)

    # Retry with fewer keywords
    if not items and len(core_words) > 2:
        shorter = " ".join(core_words[:2])
        _log(f"0 results for '{core_topic}', retrying with '{shorter}'")
        query = f"{shorter} since:{from_date} until:{to_date}"
        response = _run_xcom_rs(query, limit, timeout)
        items = parse_response(response, query=core_topic)

    # Last-chance retry: strongest remaining token
    if not items and core_words:
        low_signal = {
            "trendiest", "trending", "hottest", "hot", "popular", "viral",
            "best", "top", "latest", "new", "plugin", "plugins",
            "skill", "skills", "tool", "tools",
        }
        candidates = [w for w in core_words if w not in low_signal]
        if candidates:
            strongest = max(candidates, key=len)
            _log(f"0 results for '{core_topic}', retrying with strongest token '{strongest}'")
            query = f"{strongest} since:{from_date} until:{to_date}"
            response = _run_xcom_rs(query, limit, timeout)

    return response


def search_handles(
    handles: List[str],
    topic: Optional[str],
    from_date: str,
    count_per: int = 5,
) -> List[Dict[str, Any]]:
    """Search specific X handles via xcom-rs using ``from:<handle>`` queries.

    Mirrors ``bird_x.search_handles`` for supplemental Phase 2 search.
    """
    core_topic = _extract_core_subject(topic) if topic else None

    def _search_one(handle: str) -> List[Dict[str, Any]]:
        handle = handle.lstrip("@")
        if core_topic:
            q = f"from:{handle} {core_topic} since:{from_date}"
        else:
            q = f"from:{handle} since:{from_date}"

        result = _run_xcom_rs(q, count_per, timeout=15)
        return parse_response(result, query=core_topic)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_items: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(5, len(handles))) as executor:
        futures = {executor.submit(_search_one, h): h for h in handles}
        for future in as_completed(futures):
            all_items.extend(future.result())

    return all_items


# ---------------------------------------------------------------------------
# Response parsing / normalization
# ---------------------------------------------------------------------------

def parse_response(response: Dict[str, Any], query: str = "") -> List[Dict[str, Any]]:
    """Parse xcom-rs JSON output into the normalized item format.

    The output shape matches ``bird_x.parse_bird_response`` so downstream
    normalization/scoring can treat items identically.
    """
    items: List[Dict[str, Any]] = []

    if "error" in response and response["error"]:
        _log(f"xcom-rs error: {response['error']}")
        return items

    raw_items = (
        response if isinstance(response, list)
        else response.get("items", response.get("tweets", response.get("data", [])))
    )

    if not isinstance(raw_items, list):
        return items

    for i, tweet in enumerate(raw_items):
        if not isinstance(tweet, dict):
            continue

        url = tweet.get("permanent_url") or tweet.get("url", "")
        if not url and tweet.get("id"):
            author_info = tweet.get("author", {}) or tweet.get("user", {})
            screen_name = author_info.get("username") or author_info.get("screen_name", "")
            if screen_name:
                url = f"https://x.com/{screen_name}/status/{tweet['id']}"

        if not url:
            continue

        # Parse date
        date = None
        created_at = tweet.get("createdAt") or tweet.get("created_at", "")
        if created_at:
            try:
                if len(created_at) > 10 and created_at[10] == "T":
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                date = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        # Author handle
        author_info = tweet.get("author", {}) or tweet.get("user", {})
        author_handle = (
            author_info.get("username")
            or author_info.get("screen_name", "")
            or tweet.get("author_handle", "")
        )

        # Engagement
        engagement = {
            "likes": _first_of(tweet.get("likeCount"), tweet.get("like_count"), tweet.get("favorite_count")),
            "reposts": _first_of(tweet.get("retweetCount"), tweet.get("retweet_count")),
            "replies": _first_of(tweet.get("replyCount"), tweet.get("reply_count")),
            "quotes": _first_of(tweet.get("quoteCount"), tweet.get("quote_count")),
        }
        for key in engagement:
            if engagement[key] is not None:
                try:
                    engagement[key] = int(engagement[key])
                except (ValueError, TypeError):
                    engagement[key] = None

        item = {
            "id": f"X{i + 1}",
            "text": str(tweet.get("text", tweet.get("full_text", ""))).strip()[:500],
            "url": url,
            "author_handle": author_handle.lstrip("@"),
            "date": date,
            "engagement": engagement,
            "why_relevant": "",
            "relevance": _compute_relevance(query, str(tweet.get("text", ""))) if query else 0.7,
        }

        items.append(item)

    return items


def _first_of(*values: Any) -> Any:
    """Return first value that is not None."""
    for v in values:
        if v is not None:
            return v
    return None
