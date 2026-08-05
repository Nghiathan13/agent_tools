"""Tests for helper/separate_vocals.py."""

import subprocess
import sys
from pathlib import Path

import pytest

from youtube.transcript.helper.separate_vocals import default_output, pick_device, separate_vocals


def test_pick_device(monkeypatch):
    monkeypatch.setattr("torch.cuda.is_available", lambda: True)
    assert pick_device() == "cuda"
    monkeypatch.setattr("torch.cuda.is_available", lambda: False)
    assert pick_device() == "cpu"


def test_default_output():
    assert default_output("/x/y/song.webm") == "/x/y/song_vocals.wav"


def test_separate_vocals_constructs_demucs_command(tmp_path, monkeypatch):
    audio = tmp_path / "song.webm"
    audio.write_bytes(b"x")
    output = tmp_path / "vocals.wav"
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        source = tmp_path / "demucs_work" / "htdemucs_ft" / "song" / "vocals.wav"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"x")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("youtube.transcript.helper.separate_vocals.tempfile.mkdtemp", lambda prefix="": str(tmp_path / "demucs_work"))
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = separate_vocals(str(audio), str(output), "htdemucs_ft", "cuda", 7)

    assert result == output
    assert calls["cmd"][:3] == [sys.executable, "-m", "demucs"]
    assert calls["cmd"][3:5] == ["-n", "htdemucs_ft"]
    assert "--two-stems=vocals" in calls["cmd"]
    assert calls["cmd"][6:8] == ["-d", "cuda"]
    assert "--segment" in calls["cmd"] and "7" in calls["cmd"]
    assert calls["kwargs"]["env"]["PYTORCH_NO_CUDA_MEMORY_CACHING"] == "1"
    assert calls["kwargs"]["check"] is True
    assert output.exists()


def test_separate_vocals_raises_when_audio_missing(tmp_path):
    with pytest.raises(OSError):
        separate_vocals(str(tmp_path / "missing.webm"), str(tmp_path / "o.wav"))


def test_separate_vocals_raises_when_no_vocals_output(tmp_path, monkeypatch):
    audio = tmp_path / "song.webm"
    audio.write_bytes(b"x")

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("youtube.transcript.helper.separate_vocals.tempfile.mkdtemp", lambda prefix="": str(tmp_path / "demucs_work"))
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError):
        separate_vocals(str(audio), str(tmp_path / "o.wav"), "htdemucs_ft", "cuda", 7)
