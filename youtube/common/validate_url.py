#!/usr/bin/env python3
"""Shared YouTube URL validation helpers."""

import re
from urllib.parse import urlparse

VIDEO_ID_PATTERNS = [
    r"(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})(?![a-zA-Z0-9_-])",
]

RAW_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def extract_video_id(url_or_id: str) -> str | None:
    """Return the 11-character video ID from a YouTube URL or raw ID, or None."""
    url_or_id = url_or_id.strip()
    if not url_or_id:
        return None
    if RAW_ID_PATTERN.fullmatch(url_or_id):
        return url_or_id
    parsed = urlparse(url_or_id if "://" in url_or_id else f"https://{url_or_id}")
    host = (parsed.hostname or "").lower()
    if host != "youtu.be" and not host.endswith("youtube.com"):
        return None
    for pattern in VIDEO_ID_PATTERNS:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def is_valid_youtube_url(url: str) -> bool:
    """Return True if the input is a YouTube URL or a raw 11-char video ID."""
    return extract_video_id(url) is not None
