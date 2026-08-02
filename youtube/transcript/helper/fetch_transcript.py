"""Fetch raw transcript data (JSON segments or raw XML) for a YouTube video URL."""

from youtube_transcript_api import TranscriptList, YouTubeTranscriptApi


def metadata_from_details(details: dict) -> dict:
    """Extract {title, author, duration} from the player response videoDetails dict."""
    try:
        duration = int(details.get("lengthSeconds", 0) or 0)
    except (TypeError, ValueError):
        duration = 0
    return {
        "title": details.get("title", ""),
        "author": details.get("author", ""),
        "duration": duration,
    }


def to_ms_segments(segments: list[dict]) -> list[dict]:
    """Convert raw segments {text, start, duration} (seconds) to {text, startMs, endMs} (ms)."""
    return [
        {
            "text": segment["text"],
            "startMs": int(round(segment["start"] * 1000)),
            "endMs": int(round((segment["start"] + segment["duration"]) * 1000)),
        }
        for segment in segments
    ]


def fetch_segments(video_id: str) -> list[dict]:
    """Return transcript segments as {text, startMs, endMs} dicts."""
    result = YouTubeTranscriptApi().fetch(video_id)
    raw = [
        {"text": segment.text, "start": segment.start, "duration": segment.duration}
        for segment in result
    ]
    return to_ms_segments(raw)


def fetch_segments_and_metadata(
    video_id: str, languages: tuple[str, ...] = ("en",)
) -> tuple[list[dict], dict]:
    """Fetch the innertube player response ONCE, returning (ms segments, {title, author}).

    Uses the raw player response (videoDetails + captionTracks) so metadata
    comes from the same request as the transcript, without an extra call.
    """
    api = YouTubeTranscriptApi()
    fetcher = api._fetcher
    html = fetcher._fetch_video_html(video_id)
    api_key = fetcher._extract_innertube_api_key(html, video_id)
    innertube_data = fetcher._fetch_innertube_data(video_id, api_key)
    captions_json = fetcher._extract_captions_json(innertube_data, video_id)
    transcript = TranscriptList.build(
        fetcher._http_client, video_id, captions_json
    ).find_transcript(languages)
    raw = transcript.fetch()
    segments = to_ms_segments(
        [
            {"text": segment.text, "start": segment.start, "duration": segment.duration}
            for segment in raw
        ]
    )
    metadata = metadata_from_details(innertube_data.get("videoDetails", {}))
    return segments, metadata


def fetch_xml(video_id: str) -> str:
    """Return the raw timedtext XML response from YouTube."""
    api = YouTubeTranscriptApi()
    captions = api._fetcher._fetch_captions_json(video_id)
    base_url = captions["captionTracks"][0]["baseUrl"].replace("&fmt=srv3", "")
    response = api._fetcher._http_client.get(base_url, timeout=15)
    return response.text
