"""Tests for helper/fetch_audio.py."""

import subprocess
import sys
from pathlib import Path

import pytest

from fetch_audio import download_audio, main


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


def test_main_prints_output_path(tmp_path, capsys, monkeypatch):
    output = tmp_path / "out"

    def fake_run(cmd, **kwargs):
        Path(str(output) + ".webm").write_bytes(b"x")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["fetch_audio.py", "https://youtu.be/aircAruvnKk", "-o", str(output)]
    )

    main()

    assert capsys.readouterr().out.strip() == str(Path(str(output) + ".webm").resolve())


def test_main_called_process_error_exits_cleanly(tmp_path, capsys, monkeypatch):
    def boom(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="yt-dlp: ERROR: Private video")

    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(
        sys, "argv", ["fetch_audio.py", "https://youtu.be/aircAruvnKk", "-o", str(tmp_path / "x.mp3")]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "Private video" in err


def test_main_invalid_url_exits_cleanly(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["fetch_audio.py", "not a url", "-o", str(tmp_path / "x.mp3")]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "Invalid YouTube URL" in err


def test_main_runtime_error_exits_cleanly(tmp_path, capsys, monkeypatch):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys, "argv", ["fetch_audio.py", "url", "-o", str(tmp_path / "nope.mp3")]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "Traceback" not in capsys.readouterr().err
