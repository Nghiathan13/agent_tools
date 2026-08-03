"""Align multiple text windows against audio with wav2vec2 in one forward pass."""

from typing import Any

import numpy as np
import whisperx


def _norm(text: str) -> str:
    """Collapse whitespace for text comparison."""
    return " ".join(text.split())


def _norm_word(word: str) -> str:
    """Lowercase and strip punctuation for word matching."""
    return "".join(ch for ch in word.lower() if ch.isalnum() or ch.isspace()).strip()


def find_words(entries: list[dict], targets: list[str]) -> list[dict]:
    """Return the first occurrence's timestamp for each target word.

    Matched case-insensitively with punctuation stripped (e.g. "Later" vs
    "later", "polyglot," vs "polyglot"), in target order. Targets without a
    match are omitted.
    """
    pool = [word for entry in entries for word in entry["words"]]
    results = []
    for target in targets:
        normalized = _norm_word(target)
        for word in pool:
            if _norm_word(word["word"]) == normalized:
                results.append(word)
                break
    return results


def align_texts(
    texts: list[dict],
    model: Any,
    metadata: dict,
    audio: np.ndarray,
    device: str,
) -> list[dict]:
    """Align each {text, start, end} window against audio in one whisperx call.

    Returns one entry per input window (order preserved), with words merged
    back from whisperx's per-sentence subsegments: {"text", "start", "end",
    "words": [{"word", "start_ms", "end_ms"}, ...]} using absolute times.
    A window whose output text diverges from its input (misalignment) or that
    fails to align yields an empty words list.
    """
    result = whisperx.align(
        [
            {"start": entry["start"], "end": entry["end"], "text": entry["text"]}
            for entry in texts
        ],
        model,
        metadata,
        audio,
        device,
    )
    output_segments = result.get("segments", [])
    outputs = []
    out_ptr = 0
    for entry in texts:
        expected_text = _norm(entry["text"])
        words, joined = [], ""
        while out_ptr < len(output_segments):
            sub = output_segments[out_ptr]
            joined = " ".join([joined, sub.get("text", "")]).strip()
            words.extend(sub.get("words", []))
            out_ptr += 1
            if _norm(joined) == expected_text:
                break
            if not expected_text.startswith(_norm(joined)):
                words = []  # divergence: misaligned, discard this window
                break
        outputs.append(
            {
                "text": entry["text"],
                "start": entry["start"],
                "end": entry["end"],
                "words": [
                    {
                        "word": word.get("word", ""),
                        "start_ms": int(round(word["start"] * 1000)),
                        "end_ms": int(round(word["end"] * 1000)),
                    }
                    for word in words
                    if "start" in word and "end" in word
                ],
            }
        )
    return outputs
