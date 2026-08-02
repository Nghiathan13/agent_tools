"""Tests for helper/fetch_transcript.py."""

from fetch_transcript import (
    fetch_segments,
    fetch_segments_and_metadata,
    metadata_from_details,
    to_ms_segments,
)


def test_metadata_from_details_extracts_title_author():
    details = {"title": "My Song", "author": "Artist", "lengthSeconds": "240"}
    assert metadata_from_details(details) == {
        "title": "My Song",
        "author": "Artist",
        "duration": 240,
    }
    assert metadata_from_details({}) == {"title": "", "author": "", "duration": 0}
    assert metadata_from_details({"lengthSeconds": "abc"})["duration"] == 0


def test_fetch_segments_and_metadata_shares_player_response(monkeypatch):
    class FakeSegment:
        text = "hi"
        start = 1.0
        duration = 2.0

    class FakeTranscript:
        def fetch(self):
            return [FakeSegment()]

    class FakeList:
        def find_transcript(self, languages):
            return FakeTranscript()

    class FakeFetcher:
        _http_client = object()

        def _fetch_video_html(self, video_id):
            return '<html>"INNERTUBE_API_KEY": "AIza-key"</html>'

        def _extract_innertube_api_key(self, html, video_id):
            return "AIza-key"

        def _fetch_innertube_data(self, video_id, api_key):
            return {
                "videoDetails": {"title": "My Song", "author": "Artist"},
                "captions": {"playerCaptionsTracklistRenderer": {"captionTracks": []}},
            }

        def _extract_captions_json(self, innertube_data, video_id):
            return innertube_data["captions"]["playerCaptionsTracklistRenderer"]

    class FakeApi:
        _fetcher = FakeFetcher()

    monkeypatch.setattr("fetch_transcript.YouTubeTranscriptApi", lambda: FakeApi())
    monkeypatch.setattr(
        "fetch_transcript.TranscriptList.build",
        lambda http_client, video_id, captions_json: FakeList(),
    )

    segments, metadata = fetch_segments_and_metadata("abc")

    assert segments == [{"text": "hi", "startMs": 1000, "endMs": 3000}]
    assert metadata == {"title": "My Song", "author": "Artist", "duration": 0}


def test_to_ms_segments_converts_start_duration():
    segments = [
        {"text": "♪ hi ♪", "start": 1.0, "duration": 2.0},
        {"text": "bye", "start": 46.057, "duration": 1.2},
    ]
    assert to_ms_segments(segments) == [
        {"text": "♪ hi ♪", "startMs": 1000, "endMs": 3000},
        {"text": "bye", "startMs": 46057, "endMs": 47257},
    ]


def test_fetch_segments_converts_to_ms(monkeypatch):
    class FakeResult:
        text = "hi"
        start = 1.0
        duration = 2.0

    class FakeApi:
        def fetch(self, video_id):
            return [FakeResult()]

    monkeypatch.setattr("fetch_transcript.YouTubeTranscriptApi", FakeApi)

    assert fetch_segments("abc") == [{"text": "hi", "startMs": 1000, "endMs": 3000}]
