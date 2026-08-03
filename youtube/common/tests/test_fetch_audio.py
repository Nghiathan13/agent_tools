"""Tests for common/fetch_audio.py."""

import subprocess
import sys
from pathlib import Path

import pytest

from fetch_audio import download_audio


def test_download_audio_constructs_ytdlp_command(tmp_path, monkeypatch):
    output = tmp_path / "out"
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        Path(str(output) + ".webm").write_bytes(b"x")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = download_audio("https://youtu.be/abc", str(output))

    assert result == Path(str(output) + ".webm")
    assert calls["cmd"][:3] == [sys.executable, "-m", "yt_dlp"]
    assert "-f" in calls["cmd"] and "bestaudio" in calls["cmd"]
    assert "--extract-audio" not in calls["cmd"]
    assert "--audio-format" not in calls["cmd"]
    assert calls["cmd"][-2:] == [f"{output}.%(ext)s", "https://youtu.be/abc"]
    assert calls["kwargs"]["check"] is True


def test_download_audio_raises_when_no_file_created(tmp_path, monkeypatch):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError):
        download_audio("url", str(tmp_path / "missing.mp3"))
