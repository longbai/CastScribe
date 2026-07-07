"""Input source collection and URL resolution."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import urlencode, unquote, urlparse
from urllib.request import urlopen


def collect_sources(urls: Sequence[str], input_file: Path | None) -> list[str]:
    sources = [url.strip() for url in urls if url.strip()]
    if input_file is None:
        return sources

    for line in input_file.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("#"):
            sources.append(cleaned)
    return sources


def local_source_path(source: str) -> Path | None:
    parsed = urlparse(source)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).expanduser()
    if parsed.scheme:
        return None

    path = Path(source).expanduser()
    if path.exists():
        return path
    return None


def resolve_remote_source(source: str, url_opener: Callable[[str], bytes] | None = None) -> str:
    feed_url = apple_podcasts_feed_url(source, url_opener)
    return feed_url or source


def apple_podcasts_feed_url(source: str, url_opener: Callable[[str], bytes] | None = None) -> str | None:
    parsed = urlparse(source)
    if parsed.netloc not in {"podcasts.apple.com", "itunes.apple.com"}:
        return None
    match = re.search(r"/id(\d+)", parsed.path)
    if not match:
        return None

    podcast_id = match.group(1)
    query = urlencode({"id": podcast_id, "entity": "podcast"})
    lookup_url = f"https://itunes.apple.com/lookup?{query}"
    opener = url_opener or default_url_opener
    payload = json.loads(opener(lookup_url).decode("utf-8"))
    for result in payload.get("results", []):
        feed_url = result.get("feedUrl")
        if feed_url:
            return feed_url
    return None


def default_url_opener(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        return response.read()
