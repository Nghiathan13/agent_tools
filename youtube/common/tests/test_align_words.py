"""Tests for common/align_words.py."""

from youtube.common import align_words as wa


def word(text, start, end):
    return {"word": text, "start": start, "end": end}


def test_merges_per_sentence_subsegments(monkeypatch):
    # whisperx splits one input into per-sentence subsegments; align_words
    # must merge them back into one entry with absolute ms words.
    subsegments = [
        {
            "text": "One two three.",
            "start": 1.0,
            "end": 1.8,
            "words": [word("One", 1.0, 1.2), word("two", 1.3, 1.5), word("three.", 1.6, 1.8)],
        },
        {
            "text": "Four five six.",
            "start": 2.0,
            "end": 2.8,
            "words": [word("Four", 2.0, 2.2), word("five", 2.3, 2.5), word("six.", 2.6, 2.8)],
        },
    ]
    monkeypatch.setattr(wa.whisperx, "align", lambda *args: {"segments": subsegments})

    result = wa.align_words(
        [{"text": "One two three. Four five six.", "start": 1.0, "end": 4.0}],
        "model",
        "meta",
        None,
        "cpu",
    )

    assert result == [
        {
            "text": "One two three. Four five six.",
            "start": 1.0,
            "end": 4.0,
            "words": [
                {"word": "One", "start_ms": 1000, "end_ms": 1200},
                {"word": "two", "start_ms": 1300, "end_ms": 1500},
                {"word": "three.", "start_ms": 1600, "end_ms": 1800},
                {"word": "Four", "start_ms": 2000, "end_ms": 2200},
                {"word": "five", "start_ms": 2300, "end_ms": 2500},
                {"word": "six.", "start_ms": 2600, "end_ms": 2800},
            ],
        }
    ]


def test_multiple_inputs_order_preserved(monkeypatch):
    subsegments = [
        {"text": "One.", "start": 0.0, "end": 0.5, "words": [word("One", 0.0, 0.3)]},
        {"text": "Two.", "start": 3.0, "end": 3.5, "words": [word("Two", 3.0, 3.3)]},
    ]
    monkeypatch.setattr(wa.whisperx, "align", lambda *args: {"segments": subsegments})

    result = wa.align_words(
        [
            {"text": "One.", "start": 0.0, "end": 0.5},
            {"text": "Two.", "start": 3.0, "end": 3.5},
        ],
        "model",
        "meta",
        None,
        "cpu",
    )

    assert [entry["words"][0]["word"] for entry in result] == ["One", "Two"]


def test_divergence_yields_empty_words(monkeypatch):
    # Output text does not match the input — misalignment, discard.
    subsegments = [
        {"text": "Something else.", "start": 0.0, "end": 1.0, "words": [word("X", 0.0, 0.2)]}
    ]
    monkeypatch.setattr(wa.whisperx, "align", lambda *args: {"segments": subsegments})

    result = wa.align_words(
        [{"text": "One two three.", "start": 0.0, "end": 1.0}],
        "model",
        "meta",
        None,
        "cpu",
    )

    assert result[0]["words"] == []


def test_failed_alignment_yields_empty_words(monkeypatch):
    monkeypatch.setattr(wa.whisperx, "align", lambda *args: {"segments": []})

    result = wa.align_words(
        [{"text": "One two three.", "start": 0.0, "end": 1.0}],
        "model",
        "meta",
        None,
        "cpu",
    )

    assert result[0]["words"] == []


def test_words_without_times_filtered(monkeypatch):
    subsegments = [
        {
            "text": "One.",
            "start": 0.0,
            "end": 1.0,
            "words": [{"word": "One"}, word("two", 0.5, 0.8)],
        }
    ]
    monkeypatch.setattr(wa.whisperx, "align", lambda *args: {"segments": subsegments})

    result = wa.align_words(
        [{"text": "One.", "start": 0.0, "end": 1.0}],
        "model",
        "meta",
        None,
        "cpu",
    )

    assert result[0]["words"] == [{"word": "two", "start_ms": 500, "end_ms": 800}]


def test_find_words_returns_first_occurrence_per_target():
    entries = [
        {
            "text": "One two.",
            "start": 0.0,
            "end": 1.0,
            "words": [
                {"word": "One", "start_ms": 0, "end_ms": 100},
                {"word": "two", "start_ms": 100, "end_ms": 200},
            ],
        },
        {
            "text": "two again.",
            "start": 1.0,
            "end": 2.0,
            "words": [
                {"word": "two", "start_ms": 1000, "end_ms": 1100},
                {"word": "again.", "start_ms": 1100, "end_ms": 1300},
            ],
        },
    ]
    assert wa.find_words(entries, ["two", "again"]) == [
        {"word": "two", "start_ms": 100, "end_ms": 200},
        {"word": "again.", "start_ms": 1100, "end_ms": 1300},
    ]


def test_find_words_matches_case_and_punctuation_insensitively():
    entries = [
        {
            "text": "Later, polyglot.",
            "start": 0.0,
            "end": 1.0,
            "words": [
                {"word": "Later,", "start_ms": 0, "end_ms": 100},
                {"word": "polyglot.", "start_ms": 100, "end_ms": 300},
            ],
        }
    ]
    assert wa.find_words(entries, ["later", "POLYGLOT"]) == [
        {"word": "Later,", "start_ms": 0, "end_ms": 100},
        {"word": "polyglot.", "start_ms": 100, "end_ms": 300},
    ]


def test_find_words_omits_missing_targets():
    entries = [
        {
            "text": "One.",
            "start": 0.0,
            "end": 1.0,
            "words": [{"word": "One", "start_ms": 0, "end_ms": 100}],
        }
    ]
    assert wa.find_words(entries, ["One", "missing"]) == [
        {"word": "One", "start_ms": 0, "end_ms": 100}
    ]


def test_find_words_empty_inputs():
    assert wa.find_words([], ["anything"]) == []
    assert wa.find_words([], []) == []
