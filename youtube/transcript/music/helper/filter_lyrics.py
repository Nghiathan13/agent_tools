"""Filter transcript segments to keep only lines starting and ending with ♪."""


def is_lyrics(text: str) -> bool:
    """Return True if the text starts and ends with the ♪ music marker."""
    text = text.strip()
    return text.startswith("♪") and text.endswith("♪")


def strip_markers(text: str) -> str:
    """Remove leading and trailing ♪ markers and surrounding whitespace."""
    return text.strip().removeprefix("♪").removesuffix("♪").strip()


def clean_text(text: str) -> str:
    """Replace newlines and collapse whitespace runs into single spaces."""
    return " ".join(text.split())


def filter_lyrics(segments: list[dict]) -> list[dict]:
    """Return only segments whose text starts and ends with ♪.

    Segments without a string text (missing key or wrong type) are skipped.
    Kept segments have their text whitespace-normalized (newlines become spaces).
    """
    return [
        {**segment, "text": clean_text(segment["text"])}
        for segment in segments
        if isinstance(segment.get("text"), str) and is_lyrics(segment["text"])
    ]
