"""Tests for helper/validate_url.py."""

from youtube.common.validate_url import extract_video_id, is_valid_youtube_url


def test_extract_video_id_valid_formats():
    cases = {
        "https://www.youtube.com/watch?v=aircAruvnKk": "aircAruvnKk",
        "https://youtu.be/aircAruvnKk?t=30": "aircAruvnKk",
        "https://www.youtube.com/shorts/aircAruvnKk": "aircAruvnKk",
        "https://www.youtube.com/embed/aircAruvnKk": "aircAruvnKk",
        "https://www.youtube.com/live/aircAruvnKk": "aircAruvnKk",
        "https://m.youtube.com/watch?v=aircAruvnKk": "aircAruvnKk",
        "https://music.youtube.com/watch?v=aircAruvnKk": "aircAruvnKk",
        "aircAruvnKk": "aircAruvnKk",
        "  aircAruvnKk  ": "aircAruvnKk",
    }
    for url, expected in cases.items():
        assert extract_video_id(url) == expected, url


def test_extract_video_id_rejects_invalid():
    invalid = [
        "",
        "not a url",
        "https://example.com/watch?v=aircAruvnKk",
        "https://evil.com/youtu.be/aircAruvnKk",
        "https://youtube.com/watch?v=short",
        "https://www.youtube.com/watch?v=aircAruvnKkXYZ1234567890",
    ]
    for value in invalid:
        assert extract_video_id(value) is None, value


def test_is_valid_youtube_url():
    assert is_valid_youtube_url("https://www.youtube.com/watch?v=aircAruvnKk")
    assert is_valid_youtube_url("https://youtu.be/aircAruvnKk")
    assert is_valid_youtube_url("aircAruvnKk")
    assert not is_valid_youtube_url("")
    assert not is_valid_youtube_url("https://example.com/watch?v=aircAruvnKk")
