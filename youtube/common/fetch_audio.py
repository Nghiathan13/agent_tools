"""Download the best audio track of a YouTube video, keeping its native format."""

import subprocess
import sys
from pathlib import Path


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
