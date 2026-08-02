#!/usr/bin/env python3
"""Download the best audio track of a YouTube video, keeping its native format."""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "common"))

from validate_url import extract_video_id  # noqa: E402


def download_audio(url: str, output: str) -> Path:
    """Download the best audio track via yt-dlp without re-encoding.

    The output path is used as a base: yt-dlp appends the real container
    extension (e.g. ``audio.webm``), which is returned.
    """
    subprocess.run(
        [
            sys.executable,
            "-m",
            "yt_dlp",
            "-f",
            "bestaudio",
            "-o",
            f"{output}.%(ext)s",
            url,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    matches = sorted(Path(output).parent.glob(f"{Path(output).name}.*"))
    if not matches:
        raise RuntimeError(f"yt-dlp finished but no audio file was created: {output}")
    return matches[0]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "-o",
        "--output",
        default="audio",
        help="Output audio base path, extension added automatically (default: audio)",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    video_id = extract_video_id(arguments.url)
    if video_id is None:
        print(f"Invalid YouTube URL: {arguments.url}", file=sys.stderr)
        raise SystemExit(1)
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        audio_path = download_audio(url, arguments.output)
    except subprocess.CalledProcessError as error:
        print((error.stderr or str(error)).strip(), file=sys.stderr)
        raise SystemExit(1)
    except (OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    print(audio_path.resolve())


if __name__ == "__main__":
    main()
