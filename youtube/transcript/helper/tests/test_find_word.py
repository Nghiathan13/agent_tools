"""Tests for helper/find_word.py."""

import numpy as np

import find_word as fw


def make_audio(duration_s: float, sr: int = 16000) -> np.ndarray:
    return np.zeros(int(duration_s * sr), dtype=np.float32)


def test_crop_audio():
    audio = np.arange(16000 * 5, dtype=np.float32)  # 5s, sample i == time_ms*16
    cropped = fw.crop_audio(audio, 1000, 3000)
    assert len(cropped) == 2000 * 16
    assert cropped[0] == 16000
    assert cropped[-1] == 16000 * 3 - 1  # 48000th sample, 0-indexed


def test_crop_audio_exact_ms():
    audio = make_audio(2)
    assert len(fw.crop_audio(audio, 0, 1000)) == 16000
    assert len(fw.crop_audio(audio, 500, 1500)) == 16000
    assert len(fw.crop_audio(audio, 1000, 2000)) == 16000


def test_normalize_word():
    assert fw.normalize_word("Justin!") == "justin"
    assert fw.normalize_word("  ♪HEY♪ ") == "hey"
    assert fw.normalize_word("you're") == "youre"


def test_find_word_in():
    words = [
        {"word": "Justin!", "start_ms": 220, "end_ms": 1461},
        {"word": "Show", "start_ms": 5122, "end_ms": 5362},
    ]
    match = fw.find_word_in(words, "justin")
    assert match is not None and match["start_ms"] == 220
    match = fw.find_word_in(words, "SHOW")
    assert match is not None and match["end_ms"] == 5362
    assert fw.find_word_in(words, "missing") is None


def test_align_sentence_extracts_words(monkeypatch):
    fake_result = {
        "segments": [
            {
                "words": [
                    {"word": "Justin!", "start": 0.22, "end": 1.461},
                    {"word": "Show", "start": 5.122, "end": 5.362},
                    {"word": "2014", "end": 8.0},  # missing start -> skipped
                ]
            }
        ]
    }
    captured = {}

    def fake_align(segments, model, metadata, audio, device):
        captured["segments"] = segments
        return fake_result

    monkeypatch.setattr(fw.whisperx, "align", fake_align)

    words = fw.align_sentence(
        object(), {"language": "en"}, make_audio(10), "Justin show you off", "cuda"
    )

    assert captured["segments"] == [
        {"start": 0.0, "end": 10.0, "text": "Justin show you off"}
    ]
    assert words == [
        {"word": "Justin!", "start_ms": 220, "end_ms": 1461},
        {"word": "Show", "start_ms": 5122, "end_ms": 5362},
    ]


def test_load_aligner_caches(monkeypatch):
    calls = []

    def fake_load(language_code, device, model_name=None):
        calls.append((language_code, device, model_name))
        return ("model", {"language": language_code})

    monkeypatch.setattr(fw.whisperx, "load_align_model", fake_load)

    fw.load_aligner("en", "cuda", None)
    fw.load_aligner("en", "cuda", None)
    fw.load_aligner("en", "cuda", "facebook/wav2vec2-large-960h")
    fw._ALIGNER_CACHE.clear()

    assert calls == [
        ("en", "cuda", None),
        ("en", "cuda", "facebook/wav2vec2-large-960h"),
    ]
