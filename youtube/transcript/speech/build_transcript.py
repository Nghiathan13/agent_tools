#!/usr/bin/env python3
"""Build a transcript JSON from a YouTube URL: validate -> fetch -> clean -> merge."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError

from youtube_transcript_api import YouTubeTranscriptApiException

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
# Make the helper modules importable when running this file directly.
sys.path.insert(0, str(ROOT / "helper"))  # speech/helper: clean_text, merge_segments
sys.path.insert(0, str(ROOT.parent / "helper"))  # helper: fetch_transcript, find_word
sys.path.insert(0, str(ROOT.parents[1] / "common"))  # common: validate_url, fetch_audio, align_text

from clean_text import clean_text  # noqa: E402
from fetch_audio import download_audio  # noqa: E402
from fetch_transcript import fetch_segments_and_metadata  # noqa: E402
from find_word import pick_device, prepare_audio  # noqa: E402
from merge_segments import merge_segments  # noqa: E402
from validate_url import extract_video_id  # noqa: E402


def build_transcript(
    url: str,
    languages: tuple[str, ...] = ("en-GB", "en"),
    max_words: int | None = None,
) -> dict:
    """Fetch a spoken-content video's transcript and return {video, segments}."""
    video_id = extract_video_id(url)
    if video_id is None:
        raise ValueError(f"Invalid YouTube URL: {url}")
    segments, metadata = fetch_segments_and_metadata(video_id, languages)
    segments = [
        {**segment, "text": clean_text(segment["text"])} for segment in segments
    ]
    audio = None
    if max_words is not None:
        # Splits may leave pieces without timestamps; fetch audio to fill them.
        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = download_audio(
                f"https://www.youtube.com/watch?v={video_id}",
                str(Path(tmp_dir) / "audio"),
            )
            audio = prepare_audio(str(audio_path))
    segments = merge_segments(segments, max_words, audio, pick_device())
    return {
        "video": {
            "url": url,
            "videoId": video_id,
            "title": metadata["title"],
            "author": metadata["author"],
            "duration": metadata["duration"],
        },
        "segments": segments,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube URL or 11-character video ID")
    parser.add_argument(
        "--max-words",
        type=int,
        default=None,
        help="Pack merged sentences into chunks below this word count",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    try:
        result = build_transcript(arguments.url, max_words=arguments.max_words)
    except (
        HTTPError,
        URLError,
        YouTubeTranscriptApiException,
        OSError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
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
