"""Find the timestamp of a word inside a sentence by aligning audio with wav2vec2."""

from typing import Any

import numpy as np
import torch
import whisperx

_ALIGNER_CACHE: dict[tuple[Any, ...], tuple[Any, dict]] = {}


def prepare_audio(path: str) -> np.ndarray:
    """Load an audio file as a 16 kHz mono float32 waveform."""
    return whisperx.load_audio(path)


def crop_audio(audio: np.ndarray, start_ms: int, end_ms: int) -> np.ndarray:
    """Return the [start_ms, end_ms) slice of a 16 kHz waveform (16 samples per ms)."""
    return audio[start_ms * 16 : end_ms * 16]


def load_aligner(language: str, device: str, model_name: str | None = None):
    """Load (and cache) the wav2vec2 alignment model for a language."""
    key = (language, device, model_name)
    if key not in _ALIGNER_CACHE:
        _ALIGNER_CACHE[key] = whisperx.load_align_model(
            language_code=language, device=device, model_name=model_name
        )
    return _ALIGNER_CACHE[key]


def normalize_word(word: str) -> str:
    """Lowercase and strip punctuation and lyric markers for matching."""
    return "".join(ch for ch in word.lower() if ch.isalnum() or ch.isspace()).strip()


def align_sentence(
    model_a: Any,
    metadata: dict,
    audio: np.ndarray,
    text: str,
    device: str,
) -> list[dict]:
    """Align text against audio, returning words with times relative to the audio start."""
    duration = len(audio) / 16000
    result = whisperx.align(
        [{"start": 0.0, "end": duration, "text": text}],
        model_a,
        metadata,
        audio,
        device,
    )
    words = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            if "start" not in word or "end" not in word:
                continue
            words.append(
                {
                    "word": word["word"].strip(),
                    "start_ms": int(round(word["start"] * 1000)),
                    "end_ms": int(round(word["end"] * 1000)),
                }
            )
    return words


def find_word_in(words: list[dict], target: str) -> dict | None:
    """Return the entry whose normalized word matches the normalized target."""
    normalized_target = normalize_word(target)
    for entry in words:
        if normalize_word(entry["word"]) == normalized_target:
            return entry
    return None


def pick_device() -> str:
    """Return 'cuda' when available, otherwise 'cpu'."""
    return "cuda" if torch.cuda.is_available() else "cpu"
