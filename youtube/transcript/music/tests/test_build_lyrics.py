"""Tests for music/build_lyrics.py."""

import json
import sys

import pytest

from youtube.transcript.music import build_lyrics as bl


def lyric_seg(text, start_ms, end_ms):
    return {"text": text, "startMs": start_ms, "endMs": end_ms}


def test_build_lyrics_orchestrates_fetch_filter_merge(monkeypatch):
    segments = [
        lyric_seg("♪ Show off ♪", 50019, 52544),
        lyric_seg("♪ Tonight ♪", 52544, 55904),
        lyric_seg("- narration -", 1000, 2000),
    ]
    monkeypatch.setattr(
        bl, "fetch_segments_and_metadata",
        lambda video_id: (segments, {"title": "Test Song", "author": "Artist", "duration": 240}),
    )

    result = bl.build_lyrics("https://youtu.be/aircAruvnKk", min_words=3, max_words=10)

    # narration filtered out, markers stripped, both lyric segments merged
    assert result == {
        "video": {
            "url": "https://www.youtube.com/watch?v=aircAruvnKk",
            "videoId": "aircAruvnKk",
            "title": "Test Song",
            "author": "Artist",
            "duration": 240,
        },
        "segments": [lyric_seg("Show off. Tonight", 50019, 55904)],
    }


def test_build_lyrics_keep_markers(monkeypatch):
    segments = [lyric_seg("♪ Hey ♪", 0, 1000)]
    monkeypatch.setattr(
        bl, "fetch_segments_and_metadata",
        lambda video_id: (segments, {"title": "T", "author": "A", "duration": 5}),
    )

    result = bl.build_lyrics("aircAruvnKk", strip=False)

    assert result["segments"][0]["text"] == "♪ Hey ♪"


def test_build_lyrics_invalid_url(monkeypatch):
    with pytest.raises(ValueError):
        bl.build_lyrics("not a url")


def test_build_lyrics_does_not_fetch_on_invalid_url(monkeypatch):
    def should_not_be_called(video_id):
        raise AssertionError("fetch must not run for an invalid URL")

    monkeypatch.setattr(bl, "fetch_segments_and_metadata", should_not_be_called)

    with pytest.raises(ValueError):
        bl.build_lyrics("not a url")


def test_main_writes_output_file(tmp_path, capsys, monkeypatch):
    segments = [
        lyric_seg("♪ a ♪", 0, 1000),
        lyric_seg("♪ b ♪", 1000, 2000),
    ]
    monkeypatch.setattr(
        bl, "fetch_segments_and_metadata",
        lambda video_id: (segments, {"title": "T", "author": "A", "duration": 3}),
    )
    monkeypatch.setattr(bl, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_lyrics.py",
            "https://youtu.be/aircAruvnKk",
            "--min-words",
            "2",
            "--max-words",
            "10",
        ],
    )

    bl.main()

    output_path = tmp_path / "aircAruvnKk.json"
    assert capsys.readouterr().out.strip() == str(output_path.resolve())
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["video"]["videoId"] == "aircAruvnKk"
    assert data["segments"] == [lyric_seg("a. b", 0, 2000)]


def test_main_invalid_url_exits_cleanly(capsys, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["build_lyrics.py", "not a url"]
    )

    with pytest.raises(SystemExit) as exc_info:
        bl.main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "Traceback" not in err and "Invalid YouTube URL" in err
