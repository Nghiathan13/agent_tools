"""Tests for helper/trim_audio.py."""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from trim_audio import default_output, main, trim_audio


def test_trim_audio_constructs_ffmpeg_command(tmp_path, monkeypatch):
    input_file = tmp_path / "in.webm"
    input_file.write_bytes(b"x")
    output = tmp_path / "out.webm"
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        output.write_bytes(b"x")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = trim_audio(str(input_file), 45000, 75000, str(output))

    assert result == output
    assert calls["cmd"][0] == "ffmpeg"
    assert "-ss" in calls["cmd"] and "45.000" in calls["cmd"]
    assert "-i" in calls["cmd"] and str(input_file) in calls["cmd"]
    assert "-t" in calls["cmd"] and "30.000" in calls["cmd"]
    assert "-c" in calls["cmd"] and "copy" in calls["cmd"]
    assert calls["kwargs"]["check"] is True


def test_trim_audio_rejects_invalid_range(tmp_path, monkeypatch):
    audio = str(tmp_path / "in.webm")
    with pytest.raises(ValueError):
        trim_audio(audio, 1000, 1000, str(tmp_path / "o.webm"))
    with pytest.raises(ValueError):
        trim_audio(audio, 2000, 1000, str(tmp_path / "o.webm"))


def test_trim_audio_raises_when_no_output(tmp_path, monkeypatch):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError):
        trim_audio(str(tmp_path / "in.webm"), 0, 1000, str(tmp_path / "missing.webm"))


def test_default_output():
    assert default_output("/x/y/in.webm") == "/x/y/in_trimmed.webm"


def test_main_prints_output(tmp_path, capsys, monkeypatch):
    input_file = tmp_path / "in.webm"
    input_file.write_bytes(b"x")

    def fake_run(cmd, **kwargs):
        Path(str(tmp_path / "in_trimmed.webm")).write_bytes(b"x")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["trim_audio.py", str(input_file), "--start", "45000", "--end", "75000"],
    )

    main()

    assert capsys.readouterr().out.strip() == str(
        (tmp_path / "in_trimmed.webm").resolve()
    )


def test_main_ffmpeg_error_exits_cleanly(tmp_path, capsys, monkeypatch):
    def boom(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="ffmpeg: Invalid data found")

    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(
        sys,
        "argv",
        ["trim_audio.py", str(tmp_path / "in.webm"), "--start", "0", "--end", "1000"],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "Invalid data found" in err


def test_main_url_composes_fetch_audio(tmp_path, capsys, monkeypatch):
    output = tmp_path / "out.webm"
    monkeypatch.setattr(
        "trim_audio.tempfile.mktemp", lambda prefix="": str(tmp_path / "tmp_src")
    )

    def fake_download(url, output_base):
        Path(output_base + ".webm").write_bytes(b"x")
        return Path(output_base + ".webm")

    def fake_run(cmd, **kwargs):
        output.write_bytes(b"x")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("fetch_audio.download_audio", fake_download)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "trim_audio.py",
            "--url",
            "https://youtu.be/aircAruvnKk",
            "--start",
            "45000",
            "--end",
            "75000",
            "-o",
            str(output),
        ],
    )

    main()

    assert capsys.readouterr().out.strip() == str(output.resolve())
    assert not (tmp_path / "tmp_src.webm").exists()


def test_main_requires_exactly_one_source(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["trim_audio.py", "--start", "0", "--end", "1000"]
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "trim_audio.py",
            str(tmp_path / "in.webm"),
            "--url",
            "https://youtu.be/aircAruvnKk",
            "--start",
            "0",
            "--end",
            "1000",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2


def test_main_invalid_url_exits_cleanly(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["trim_audio.py", "--url", "not a url", "--start", "0", "--end", "1000"],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "Invalid YouTube URL" in err
