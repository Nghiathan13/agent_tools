"""Tests for speech/build_transcript.py."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from youtube.transcript.speech import build_transcript as bt


def seg(text, start_ms, end_ms):
    return {"text": text, "startMs": start_ms, "endMs": end_ms}


@pytest.fixture(autouse=True)
def mock_audio(monkeypatch):
    monkeypatch.setattr(
        bt, "download_audio", lambda url, output: Path(str(output) + ".webm")
    )
    monkeypatch.setattr(bt, "prepare_audio", lambda path: np.zeros(16000))


def test_build_transcript_orchestrates_fetch(monkeypatch):
    segments = [
        seg("Hello and\nwelcome", 5767, 10200),
        seg("to the show.", 10200, 15117),
    ]
    monkeypatch.setattr(
        bt,
        "fetch_segments_and_metadata",
        lambda video_id, languages: (
            segments,
            {"title": "T", "author": "A", "duration": 423},
        ),
    )

    result = bt.build_transcript("https://youtu.be/9ifQ3xRz4hM")

    # \n removed and fragments merged into one sentence
    assert result == {
        "video": {
            "url": "https://www.youtube.com/watch?v=9ifQ3xRz4hM",
            "videoId": "9ifQ3xRz4hM",
            "title": "T",
            "author": "A",
            "duration": 423,
        },
        "segments": [seg("Hello and welcome to the show.", 5767, 15117)],
    }


def test_build_transcript_passes_languages(monkeypatch):
    captured = {}

    def fake_fetch(video_id, languages):
        captured["languages"] = languages
        return [], {"title": "T", "author": "A", "duration": 0}

    monkeypatch.setattr(bt, "fetch_segments_and_metadata", fake_fetch)

    bt.build_transcript("9ifQ3xRz4hM", languages=("en-GB",))

    assert captured["languages"] == ("en-GB",)


def test_build_transcript_packs_with_max_words(monkeypatch):
    segments = [
        seg("One two three four.", 0, 1000),
        seg("Five six.", 1000, 2000),
    ]
    monkeypatch.setattr(
        bt,
        "fetch_segments_and_metadata",
        lambda video_id, languages: (
            segments,
            {"title": "T", "author": "A", "duration": 3},
        ),
    )

    result = bt.build_transcript("9ifQ3xRz4hM", max_words=10)

    assert result["segments"] == [seg("One two three four. Five six.", 0, 2000)]


def test_build_transcript_invalid_url(monkeypatch):
    with pytest.raises(ValueError):
        bt.build_transcript("not a url")


def test_build_transcript_fetches_audio_with_max_words(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        bt,
        "fetch_segments_and_metadata",
        lambda video_id, languages: (
            [seg("Hi there.", 0, 1000)],
            {"title": "T", "author": "A", "duration": 3},
        ),
    )

    def fake_download(url, output):
        calls["url"] = url
        calls["output"] = output
        return Path(str(output) + ".webm")

    monkeypatch.setattr(bt, "download_audio", fake_download)

    bt.build_transcript("9ifQ3xRz4hM", max_words=10)

    assert calls["url"] == "https://www.youtube.com/watch?v=9ifQ3xRz4hM"
    assert calls["output"].endswith("audio")


def test_build_transcript_skips_audio_without_max_words(monkeypatch):
    def should_not_be_called(*args, **kwargs):
        raise AssertionError("audio must not download without max_words")

    monkeypatch.setattr(bt, "download_audio", should_not_be_called)
    monkeypatch.setattr(bt, "prepare_audio", should_not_be_called)
    monkeypatch.setattr(
        bt,
        "fetch_segments_and_metadata",
        lambda video_id, languages: (
            [seg("Hi there.", 0, 1000)],
            {"title": "T", "author": "A", "duration": 3},
        ),
    )

    result = bt.build_transcript("9ifQ3xRz4hM")

    assert result["segments"] == [seg("Hi there.", 0, 1000)]


def test_build_transcript_passes_audio_to_merge(monkeypatch):
    captured = {}
    segments = [seg("One.", 0, None), seg("Two.", None, 2000)]  # split leftover
    monkeypatch.setattr(
        bt,
        "fetch_segments_and_metadata",
        lambda video_id, languages: (
            segments,
            {"title": "T", "author": "A", "duration": 3},
        ),
    )

    def fake_merge(segs, max_words, audio, device):
        captured["audio"] = audio
        captured["max_words"] = max_words
        return segs

    monkeypatch.setattr(bt, "merge_segments", fake_merge)

    bt.build_transcript("9ifQ3xRz4hM", max_words=15)

    assert captured["audio"] is not None
    assert captured["max_words"] == 15


def test_build_transcript_does_not_fetch_on_invalid_url(monkeypatch):
    def should_not_be_called(video_id, languages):
        raise AssertionError("fetch must not run for an invalid URL")

    monkeypatch.setattr(bt, "fetch_segments_and_metadata", should_not_be_called)

    with pytest.raises(ValueError):
        bt.build_transcript("not a url")


def test_main_writes_output_file(tmp_path, capsys, monkeypatch):
    segments = [seg("Hello\nworld", 0, 1000), seg("everyone.", 1000, 2000)]
    monkeypatch.setattr(
        bt,
        "fetch_segments_and_metadata",
        lambda video_id, languages: (
            segments,
            {"title": "T", "author": "A", "duration": 3},
        ),
    )
    monkeypatch.setattr(bt, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(sys, "argv", ["build_transcript.py", "9ifQ3xRz4hM"])

    bt.main()

    output_path = tmp_path / "9ifQ3xRz4hM.json"
    assert capsys.readouterr().out.strip() == str(output_path.resolve())
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["video"]["videoId"] == "9ifQ3xRz4hM"
    assert data["segments"] == [seg("Hello world everyone.", 0, 2000)]


def test_main_passes_max_words(tmp_path, capsys, monkeypatch):
    segments = [
        seg("One two three four.", 0, 1000),
        seg("Five six.", 1000, 2000),
    ]
    monkeypatch.setattr(
        bt,
        "fetch_segments_and_metadata",
        lambda video_id, languages: (
            segments,
            {"title": "T", "author": "A", "duration": 3},
        ),
    )
    monkeypatch.setattr(bt, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["build_transcript.py", "9ifQ3xRz4hM", "--max-words", "10"]
    )

    bt.main()

    data = json.loads((tmp_path / "9ifQ3xRz4hM.json").read_text(encoding="utf-8"))
    assert data["segments"] == [seg("One two three four. Five six.", 0, 2000)]


def test_main_invalid_url_exits_cleanly(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["build_transcript.py", "not a url"])

    with pytest.raises(SystemExit) as exc_info:
        bt.main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "Invalid YouTube URL" in err
