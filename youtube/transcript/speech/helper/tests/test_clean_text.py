"""Tests for speech/helper/clean_text.py."""

from youtube.transcript.speech.helper.clean_text import clean_text


def test_newline_replaced_with_space():
    assert clean_text("6 Minute\nEnglish") == "6 Minute English"


def test_multiple_newlines():
    assert clean_text("one\ntwo\nthree") == "one two three"


def test_no_newline_unchanged():
    assert clean_text("Hello, Hannah. Hi, Neil.") == "Hello, Hannah. Hi, Neil."


def test_empty_string():
    assert clean_text("") == ""
