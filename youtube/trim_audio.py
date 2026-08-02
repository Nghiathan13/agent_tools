#!/usr/bin/env python3
"""Trim an audio file to a time range without re-encoding."""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "common"))

import fetch_audio  # noqa: E402
from validate_url import extract_video_id  # noqa: E402


def trim_audio(audio: str, start_ms: int, end_ms: int, output: str) -> Path:
    """Trim audio to [start_ms, end_ms) using ffmpeg stream copy."""
    if end_ms <= start_ms:
        raise ValueError(
            f"end_ms ({end_ms}) must be greater than start_ms ({start_ms})"
        )
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-ss",
            f"{start_ms / 1000:.3f}",
            "-i",
            audio,
            "-t",
            f"{(end_ms - start_ms) / 1000:.3f}",
            "-c",
            "copy",
            "-y",
            output,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    output_path = Path(output)
    if not output_path.exists():
        raise RuntimeError(
            f"ffmpeg finished but no output file was created: {output}"
        )
    return output_path


def default_output(audio: str) -> str:
    """Return ``<name>_trimmed<ext>`` next to the input audio file."""
    path = Path(audio)
    return str(path.with_name(f"{path.stem}_trimmed{path.suffix}"))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", nargs="?", help="Input audio file path")
    parser.add_argument(
        "--url", help="YouTube URL: download the audio first, then trim"
    )
    parser.add_argument(
        "--start", type=int, required=True, help="Start time in milliseconds"
    )
    parser.add_argument(
        "--end", type=int, required=True, help="End time in milliseconds"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: <name>_trimmed<ext>)",
    )
    arguments = parser.parse_args()
    if bool(arguments.audio) == bool(arguments.url):
        parser.error("provide either an audio file path or --url, not both")
    return arguments


def main() -> None:
    arguments = parse_arguments()
    temp_base: str | None = None
    result: Path | None = None
    try:
        if arguments.url:
            video_id = extract_video_id(arguments.url)
            if video_id is None:
                print(f"Invalid YouTube URL: {arguments.url}", file=sys.stderr)
                raise SystemExit(1)
            temp_base = tempfile.mktemp(prefix="trim_audio_")
            audio = fetch_audio.download_audio(
                f"https://www.youtube.com/watch?v={video_id}", temp_base
            )
        else:
            audio = Path(arguments.audio)
        output = arguments.output or default_output(str(audio))
        result = trim_audio(str(audio), arguments.start, arguments.end, output)
    except subprocess.CalledProcessError as error:
        print((error.stderr or str(error)).strip(), file=sys.stderr)
        raise SystemExit(1)
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    finally:
        if temp_base is not None:
            for leftover in Path(temp_base).parent.glob(f"{Path(temp_base).name}.*"):
                try:
                    leftover.unlink()
                except OSError:
                    pass
    assert result is not None
    print(result.resolve())


if __name__ == "__main__":
    main()
