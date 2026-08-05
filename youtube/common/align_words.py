"""Align text windows against audio with wav2vec2 and find word timestamps."""

from typing import Any

import numpy as np
import torch
import whisperx

_ALIGNER_CACHE: dict[tuple[Any, ...], tuple[Any, dict]] = {}


def _norm(text: str) -> str:
    """Collapse whitespace for text comparison."""
    return " ".join(text.split())


def prepare_audio(path: str) -> np.ndarray:
    """Load an audio file as a 16 kHz mono float32 waveform."""
    return whisperx.load_audio(path)


def load_aligner(language: str, device: str, model_name: str | None = None):
    """Load (and cache) the wav2vec2 alignment model for a language."""
    key = (language, device, model_name)
    if key not in _ALIGNER_CACHE:
        _ALIGNER_CACHE[key] = whisperx.load_align_model(
            language_code=language, device=device, model_name=model_name
        )
    return _ALIGNER_CACHE[key]


def pick_device() -> str:
    """Return 'cuda' when available, otherwise 'cpu'."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def normalize_word(word: str) -> str:
    """Lowercase and strip punctuation and lyric markers for matching."""
    return "".join(ch for ch in word.lower() if ch.isalnum() or ch.isspace()).strip()


def align_words(
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


def find_words(entries: list[dict], targets: list[str]) -> list[dict]:
    """Return the first occurrence's timestamp for each target word.

    Matched case-insensitively with punctuation stripped (e.g. "Later" vs
    "later", "polyglot," vs "polyglot"), in target order. Targets without a
    match are omitted.
    """
    pool = [word for entry in entries for word in entry["words"]]
    results = []
    for target in targets:
        normalized = normalize_word(target)
        for word in pool:
            if normalize_word(word["word"]) == normalized:
                results.append(word)
                break
    return results
