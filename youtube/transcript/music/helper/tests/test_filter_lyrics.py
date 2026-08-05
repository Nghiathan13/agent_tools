"""Tests for music/filter_lyrics.py."""

from youtube.transcript.music.helper.filter_lyrics import clean_text, filter_lyrics, is_lyrics, strip_markers


def test_is_lyrics_accepts_marked_lines():
    assert is_lyrics("♪ Show you off ♪")
    assert is_lyrics("  ♪ Hey hey ♪  ")
    assert is_lyrics("♪")


def test_is_lyrics_rejects_noise():
    assert not is_lyrics("You have no game.")
    assert not is_lyrics("(piano playing)")
    assert not is_lyrics("- [Nicki Minaj] Yeah!")
    assert not is_lyrics("♪ no closing marker")
    assert not is_lyrics("no opening marker ♪")
    assert not is_lyrics("")


def test_is_lyrics_whitespace_only_is_false():
    assert not is_lyrics("   ")
    assert not is_lyrics("\t\n ")


def test_filter_lyrics_empty_list():
    assert filter_lyrics([]) == []


def test_clean_text_normalizes_whitespace():
    assert clean_text("♪ line1\nline2 ♪") == "♪ line1 line2 ♪"
    assert clean_text("a\tb  c\n\nd") == "a b c d"
    assert clean_text("  ♪ spaced ♪  ") == "♪ spaced ♪"
    assert clean_text("") == ""


def test_filter_lyrics_keeps_only_marked_segments():
    segments = [
        {"text": "♪ Show you off ♪", "start": 50.0, "duration": 2.5},
        {"text": "plain talk", "start": 8.6, "duration": 1.8},
        {"text": "(piano playing)", "start": 10.5, "duration": 2.6},
        {"text": "  ♪ Hey hey ♪  ", "start": 55.9, "duration": 1.6},
    ]
    kept = filter_lyrics(segments)
    assert [s["text"] for s in kept] == ["♪ Show you off ♪", "♪ Hey hey ♪"]


def test_filter_lyrics_cleans_newlines_in_kept_segments():
    segments = [
        {"text": "♪ first line\nsecond line ♪", "start": 10.0, "duration": 3.0},
        {"text": "(noise)", "start": 1.0, "duration": 1.0},
    ]
    kept = filter_lyrics(segments)
    assert kept == [
        {"text": "♪ first line second line ♪", "start": 10.0, "duration": 3.0}
    ]


def test_filter_lyrics_skips_segments_without_text():
    segments = [
        {"start": 1.0, "duration": 2.0},
        {"text": 123, "start": 2.0, "duration": 1.0},
        {"text": "♪ ok ♪", "start": 3.0, "duration": 1.0},
    ]
    kept = filter_lyrics(segments)
    assert [s["text"] for s in kept] == ["♪ ok ♪"]


def test_strip_markers():
    assert strip_markers("♪ Show you off ♪") == "Show you off"
    assert strip_markers("  ♪ Hey hey ♪  ") == "Hey hey"
    assert strip_markers("♪") == ""
    assert strip_markers("♪ ♪") == ""
    assert strip_markers("plain") == "plain"
