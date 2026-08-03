#!/usr/bin/env python3
"""Build merged lyric lines from a YouTube URL: fetch transcript -> filter -> merge."""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

from youtube_transcript_api import YouTubeTranscriptApiException

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
# Make the helper modules importable when running this file directly.
sys.path.insert(0, str(ROOT / "helper"))  # music/helper: filter_lyrics, merge_lyrics
sys.path.insert(0, str(ROOT.parent / "helper"))  # helper: fetch_transcript
sys.path.insert(0, str(ROOT.parents[1] / "common"))  # common: validate_url

from fetch_transcript import fetch_segments_and_metadata  # noqa: E402
from filter_lyrics import filter_lyrics, strip_markers  # noqa: E402
from merge_lyrics import merge_lyrics  # noqa: E402
from validate_url import extract_video_id  # noqa: E402


def build_lyrics(
    url: str,
    min_words: int | None = None,
    max_words: int | None = None,
    strip: bool = True,
) -> dict:
    """Fetch a transcript, keep ♪ lyric segments and merge them into lines.

    Returns {"video": {url, videoId, title, author, duration}, "segments": [...]}.
    """
    video_id = extract_video_id(url)
    if video_id is None:
        raise ValueError(f"Invalid YouTube URL: {url}")
    url = f"https://www.youtube.com/watch?v={video_id}"
    segments, metadata = fetch_segments_and_metadata(video_id)
    lyrics = filter_lyrics(segments)
    if strip:
        lyrics = [
            {**segment, "text": strip_markers(segment["text"])}
            for segment in lyrics
        ]
    return {
        "video": {
            "url": url,
            "videoId": video_id,
            "title": metadata["title"],
            "author": metadata["author"],
            "duration": metadata["duration"],
        },
        "segments": merge_lyrics(lyrics, min_words, max_words),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube URL or 11-character video ID")
    parser.add_argument(
        "--min-words",
        type=int,
        default=None,
        help="Merge segments below this word count",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=None,
        help="Keep merged segments below this word count",
    )
    parser.add_argument(
        "--keep-markers",
        action="store_true",
        help="Keep the ♪ markers instead of stripping them (default: strip)",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    try:
        result = build_lyrics(
            arguments.url,
            arguments.min_words,
            arguments.max_words,
            strip=not arguments.keep_markers,
        )
    except (HTTPError, URLError, YouTubeTranscriptApiException, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    video_id = result["video"]["videoId"]
    output_path = OUTPUT_DIR / f"{video_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output_path.resolve())


if __name__ == "__main__":
    main()
