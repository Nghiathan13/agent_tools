"""Merge caption segments into complete sentences; fill missing timestamps via alignment."""

import re

import numpy as np

from youtube.common.align_words import align_words, load_aligner, pick_device

SENTENCE_END = (".", "!", "?", "...")
# Single-char sentence endings (SENTENCE_END minus the "..." sequence).
SENTENCE_END_CHARS = frozenset(ch for ch in SENTENCE_END if len(ch) == 1)

# Periods ending abbreviations — never treated as sentence boundaries.
ABBREVIATION_PATTERN = re.compile(
    r"(?<!\w)(?:"
    r"Mr|Mrs|Ms|Dr|Prof|St|Sr|Jr|No|vs|etc|e\.g|i\.e|U\.S|U\.K|a\.m|p\.m|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
    r")\.",
    re.IGNORECASE,
)


def word_count(text: str) -> int:
    """Count whitespace-separated words."""
    return len(text.split())


def has_sentence_end(text: str) -> bool:
    """Return True when text ends with sentence-ending punctuation."""
    return text.rstrip().endswith(SENTENCE_END)


def _absorb(merged: list[dict], index: int) -> None:
    """Append merged[index + 1] into merged[index] (startMs kept, endMs from next) and drop it."""
    cur = merged[index]
    nxt = merged[index + 1]
    cur["text"] = f"{cur['text']} {nxt['text']}"
    if "endMs" in nxt:
        cur["endMs"] = nxt["endMs"]
    else:
        cur.pop("endMs", None)
    del merged[index + 1]


def split_sentences(text: str) -> list[str]:
    """Split text into sentences at SENTENCE_END runs (punctuation stays on the left)."""
    protected = [m.span() for m in ABBREVIATION_PATTERN.finditer(text)]
    pieces = []
    start = 0
    i = 0
    while i < len(text):
        if text[i] not in SENTENCE_END_CHARS:
            i += 1
            continue
        if any(s <= i < e for s, e in protected):
            i += 1
            continue
        j = i
        while j < len(text) and text[j] in SENTENCE_END_CHARS:
            j += 1
        k = j
        while k < len(text) and text[k].isspace():
            k += 1
        if k >= len(text) or text[k].isalnum():
            pieces.append(text[start:k].strip())
            start = k
        i = j
    tail = text[start:].strip()
    if tail:
        pieces.append(tail)
    return pieces


def _split_pieces(segment: dict) -> list[dict]:
    """Split a segment into sentences, keeping only the anchored startMs/endMs edges."""
    text = segment.get("text", "").strip()
    sentences = split_sentences(text)
    if len(sentences) <= 1:
        return [dict(segment)]
    pieces = [{"text": sentence} for sentence in sentences]
    if "startMs" in segment:
        pieces[0]["startMs"] = segment["startMs"]
    if "endMs" in segment:
        pieces[-1]["endMs"] = segment["endMs"]
    return pieces


def group_runs(segments: list[dict]) -> list[dict]:
    """Group consecutive segments missing startMs/endMs into fillable runs."""
    runs = []
    i = 0
    count = len(segments)
    while i < count:
        if "startMs" in segments[i] and "endMs" in segments[i]:
            i += 1
            continue
        j = i
        while j < count and (
            "startMs" not in segments[j] or "endMs" not in segments[j]
        ):
            j += 1
        # Window: own edge, falling back to the neighbor's edge.
        start = segments[i].get("startMs")
        if start is None and i > 0:
            start = segments[i - 1].get("endMs")
        end = segments[j - 1].get("endMs")
        if end is None and j < count:
            end = segments[j].get("startMs")
        if start is not None and end is not None:
            runs.append({"start": start, "end": end, "indices": list(range(i, j))})
        i = j
    return runs


def _fill_missing_timestamps(merged: list[dict], audio: np.ndarray, device: str) -> None:
    """Fill missing startMs/endMs of runs by aligning their texts against the audio."""
    runs = group_runs(merged)
    if not runs:
        return
    model, metadata = load_aligner("en", device)
    aligned = align_words(
        [
            {
                "start": run["start"] / 1000,
                "end": run["end"] / 1000,
                "text": " ".join(merged[index]["text"] for index in run["indices"]),
            }
            for run in runs
        ],
        model,
        metadata,
        audio,
        device,
    )
    for run, entry in zip(runs, aligned):
        words = entry["words"]
        expected = sum(word_count(merged[index]["text"]) for index in run["indices"])
        if len(words) != expected:
            continue  # word-count mismatch: alignment unreliable
        cursor = 0
        for index in run["indices"]:
            count = word_count(merged[index]["text"])
            piece_words = words[cursor : cursor + count]
            cursor += count
            if not piece_words:
                continue
            if "startMs" not in merged[index]:
                merged[index]["startMs"] = piece_words[0]["start_ms"]
            if "endMs" not in merged[index]:
                merged[index]["endMs"] = piece_words[-1]["end_ms"]


def merge_segments(
    segments: list[dict],
    max_words: int | None = None,
    audio: np.ndarray | None = None,
    device: str | None = None,
) -> list[dict]:
    """Join fragments into complete sentences; split/pack oversized ones, filling missing timestamps when audio is given."""
    merged = [dict(segment) for segment in segments]
    i = 0
    while i < len(merged):
        # 1) Complete the sentence at i.
        while i + 1 < len(merged) and not has_sentence_end(merged[i]["text"]):
            _absorb(merged, i)
        # 2) Split an oversized completed sentence, staying at the first piece.
        if max_words is not None and word_count(merged[i]["text"]) > max_words:
            merged[i : i + 1] = _split_pieces(merged[i])
        # 3) Pack the piece backward while under max_words.
        while (
            max_words is not None
            and i > 0
            and i < len(merged)
            and word_count(merged[i - 1]["text"]) + word_count(merged[i]["text"]) < max_words
        ):
            _absorb(merged, i - 1)
            # The surfaced segment may be an unfinished fragment: complete it.
            while i + 1 < len(merged) and not has_sentence_end(merged[i]["text"]):
                _absorb(merged, i)
        i += 1
    if audio is not None:
        _fill_missing_timestamps(merged, audio, device or pick_device())
    return merged
