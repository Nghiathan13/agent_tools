"""Tests for speech/helper/merge_segments.py."""

import numpy as np

import merge_segments as ms
from merge_segments import has_sentence_end, merge_segments, split_sentences, word_count


def seg(text, start_ms=None, end_ms=None):
    s = {"text": text}
    if start_ms is not None:
        s["startMs"] = start_ms
    if end_ms is not None:
        s["endMs"] = end_ms
    return s


def word(text, start_ms, end_ms):
    return {"word": text, "start_ms": start_ms, "end_ms": end_ms}


def mock_align(monkeypatch, entries):
    """Patch load_aligner/pick_device and capture the align_texts call."""
    calls = {}

    def fake_align_texts(texts, model, metadata, audio, device):
        calls["texts"] = texts
        return entries

    monkeypatch.setattr(ms, "load_aligner", lambda language, device: ("model", "meta"))
    monkeypatch.setattr(ms, "pick_device", lambda: "cpu")
    monkeypatch.setattr(ms, "align_texts", fake_align_texts)
    return calls


def entry(text, words, start=1.0, end=4.0):
    return {"text": text, "start": start, "end": end, "words": words}


def test_segment_with_sentence_end_not_merged():
    segments = [
        seg("Hello and welcome.", 5767, 10200),
        seg("I'm Neil.", 10200, 15117),
    ]
    assert merge_segments(segments) == segments


def test_segment_without_sentence_end_merged_with_next():
    segments = [
        seg("have been investigating", 16883, 20000),
        seg("what it's like to learn multiple languages.", 20000, 22833),
    ]
    result = merge_segments(segments)
    assert result == [
        seg(
            "have been investigating what it's like to learn multiple languages.",
            16883,
            22833,
        )
    ]


def test_fragment_chain_merges_until_sentence_end():
    # Real BBC pattern: fragments keep merging until one ends with a full stop.
    segments = [
        seg("Hannah and the What in the World team", 16883, 20000),
        seg("have been investigating", 20000, 22833),
        seg("what it's like to learn multiple languages,", 22833, 24833),
        seg("and she's here to tell us more about it.", 24833, 26400),
        seg("Welcome to 6 Minute English.", 26400, 28033),
    ]
    result = merge_segments(segments)
    assert result == [
        seg(
            "Hannah and the What in the World team have been investigating "
            "what it's like to learn multiple languages, and she's here to "
            "tell us more about it.",
            16883,
            26400,
        ),
        seg("Welcome to 6 Minute English.", 26400, 28033),
    ]


def test_comma_is_not_a_sentence_end():
    assert has_sentence_end("what it's like to learn multiple languages,") is False


def test_trailing_segment_without_next_is_kept():
    segments = [seg("no end here", 0, 1000)]
    assert merge_segments(segments) == segments


def test_merged_endms_taken_from_next():
    segments = [
        {"text": "have been investigating", "startMs": 16883},
        {"text": "what it's like.", "startMs": 20000, "endMs": 22833},
    ]
    result = merge_segments(segments)
    assert result == [
        {"text": "have been investigating what it's like.", "startMs": 16883, "endMs": 22833}
    ]


def test_next_without_endms_leaves_it_empty():
    segments = [
        {"text": "have been investigating", "startMs": 16883, "endMs": 20000},
        {"text": "what it's like."},
    ]
    result = merge_segments(segments)
    assert result == [{"text": "have been investigating what it's like.", "startMs": 16883}]


def test_current_without_startms_stays_empty():
    segments = [
        {"text": "have been investigating"},
        {"text": "what it's like.", "startMs": 20000, "endMs": 22833},
    ]
    result = merge_segments(segments)
    assert result == [{"text": "have been investigating what it's like.", "endMs": 22833}]


def test_surfaced_fragment_is_completed_before_packing():
    # The surfaced fragment must be completed before the pack condition re-checks.
    segments = [
        seg("One.", 0, 500),
        seg("two three.", 500, 1000),
        seg("four", 1000, 1500),
        seg("five six.", 1500, 2000),
    ]
    result = merge_segments(segments, max_words=5)
    assert result == [
        seg("One. two three.", 0, 1000),  # 3 words < 5
        seg("four five six.", 1000, 2000),  # 3 + 3 == 6, not < 5
    ]


def test_empty_input():
    assert merge_segments([]) == []


def test_max_words_packs_sentences_backward():
    segments = [
        seg("One two three four.", 0, 1000),
        seg("Five six.", 1000, 2000),
        seg("Seven eight nine ten.", 2000, 3000),
    ]
    result = merge_segments(segments, max_words=10)
    assert result == [
        seg("One two three four. Five six.", 0, 2000),  # 6 words < 10
        seg("Seven eight nine ten.", 2000, 3000),  # 6 + 4 == 10, not < 10
    ]


def test_max_words_combined_equal_not_merged():
    segments = [
        seg("One two three four.", 0, 1000),
        seg("Five six seven.", 1000, 2000),
    ]
    result = merge_segments(segments, max_words=7)  # 4 + 3 == 7, not < 7
    assert result == segments


def test_max_words_packs_first_short_segment():
    segments = [
        seg("Hi.", 0, 500),
        seg("A long sentence follows here.", 500, 2000),
    ]
    result = merge_segments(segments, max_words=10)
    assert result == [seg("Hi. A long sentence follows here.", 0, 2000)]


def test_max_words_none_skips_packing():
    segments = [
        seg("One two three four.", 0, 1000),
        seg("Five six.", 1000, 2000),
    ]
    assert merge_segments(segments) == segments


def test_input_segments_not_mutated():
    segments = [seg("one", 0, 500), seg("two.", 500, 1000)]
    merge_segments(segments)
    assert segments[0] == {"text": "one", "startMs": 0, "endMs": 500}
    assert segments[1] == {"text": "two.", "startMs": 500, "endMs": 1000}


def test_oversized_sentence_split_by_periods():
    # Chunks above max_words split at .!?; only the anchored edges keep times.
    segments = [seg("One two three four. Five six seven eight.", 0, 2000)]
    result = merge_segments(segments, max_words=5)
    assert result == [
        {"text": "One two three four.", "startMs": 0},
        {"text": "Five six seven eight.", "endMs": 2000},
    ]


def test_split_then_pack():
    # The first split sentence packs into the previous chunk; endMs vanishes with the unknown boundary.
    segments = [
        seg("One.", 0, 500),
        seg("Two three four five. Six seven eight nine.", 500, 2500),
    ]
    result = merge_segments(segments, max_words=6)
    assert result == [
        {"text": "One. Two three four five.", "startMs": 0},
        {"text": "Six seven eight nine.", "endMs": 2500},
    ]


def test_split_respects_abbreviations():
    # "Mr." is not a sentence boundary even inside an oversized chunk.
    segments = [
        seg("He met Mr. Smith was late. The meeting started at noon exactly.", 0, 3000)
    ]
    result = merge_segments(segments, max_words=5)
    assert [s["text"] for s in result] == [
        "He met Mr. Smith was late.",
        "The meeting started at noon exactly.",
    ]


def test_split_sentences_run_and_tail():
    assert split_sentences("Really!? OK. Bye") == ["Really!?", "OK.", "Bye"]
    assert split_sentences("Hello.") == ["Hello."]


# --- group_runs ---


def test_group_runs_no_incomplete_segments():
    segments = [seg("A.", 0, 1000), seg("B.", 1000, 2000)]
    assert ms.group_runs(segments) == []


def test_group_runs_split_pair_forms_run():
    # First piece keeps startMs, last keeps endMs (the split case).
    segments = [seg("One two.", 116100, None), seg("Three four.", None, 129833)]
    assert ms.group_runs(segments) == [
        {"start": 116100, "end": 129833, "indices": [0, 1]}
    ]


def test_group_runs_middle_piece_belongs_to_run():
    # A chunk with neither startMs nor endMs sits in the middle of its run.
    segments = [seg("One.", 1000, None), seg("Two.", None, None), seg("Three.", None, 4000)]
    assert ms.group_runs(segments) == [
        {"start": 1000, "end": 4000, "indices": [0, 1, 2]}
    ]


def test_group_runs_two_runs_separated_by_complete_segment():
    segments = [
        seg("One.", 0, None),
        seg("Two.", None, 2000),
        seg("Full.", 2000, 3000),
        seg("Three.", 3000, None),
        seg("Four.", None, 5000),
    ]
    assert ms.group_runs(segments) == [
        {"start": 0, "end": 2000, "indices": [0, 1]},
        {"start": 3000, "end": 5000, "indices": [3, 4]},
    ]


def test_group_runs_first_missing_start_falls_back_to_previous_end():
    segments = [seg("Prev.", 0, 1000), seg("Mid.", None, 2000)]
    assert ms.group_runs(segments) == [{"start": 1000, "end": 2000, "indices": [1]}]


def test_group_runs_last_missing_end_falls_back_to_next_start():
    segments = [seg("Mid.", 1000, None), seg("Next.", 2000, 3000)]
    assert ms.group_runs(segments) == [{"start": 1000, "end": 2000, "indices": [0]}]


def test_group_runs_unbounded_run_skipped():
    # First segment of the list with no startMs and no previous anchor.
    segments = [seg("Lone.", None, 1000)]
    assert ms.group_runs(segments) == []


def test_group_runs_empty_input():
    assert ms.group_runs([]) == []


# --- fill timestamps (audio given) ---


def test_fill_pair_run(monkeypatch):
    # Missing edges come from the aligned words.
    segments = [seg("One two three.", 1000, None), seg("Four five six.", None, 4000)]
    calls = mock_align(
        monkeypatch,
        [
            entry(
                "One two three. Four five six.",
                [word("One", 1000, 1200), word("two", 1300, 1500), word("three.", 1600, 1800),
                 word("Four", 2000, 2200), word("five", 2300, 2500), word("six.", 2600, 2800)],
            )
        ],
    )

    result = merge_segments(segments, audio=np.zeros(16000))

    assert result[0] == {"text": "One two three.", "startMs": 1000, "endMs": 1800}
    assert result[1] == {"text": "Four five six.", "startMs": 2000, "endMs": 4000}
    # Window converted to seconds and texts concatenated.
    assert calls["texts"] == [
        {"start": 1.0, "end": 4.0, "text": "One two three. Four five six."}
    ]


def test_fill_middle_run(monkeypatch):
    # The middle piece (no keys at all) gets both edges.
    segments = [seg("One.", 1000, None), seg("Two.", None, None), seg("Three.", None, 4000)]
    mock_align(
        monkeypatch,
        [
            entry(
                "One. Two. Three.",
                [word("One", 1000, 1200), word("Two", 1300, 1500), word("Three", 1600, 1800)],
            )
        ],
    )

    result = merge_segments(segments, audio=np.zeros(16000))

    assert result[1] == {"text": "Two.", "startMs": 1300, "endMs": 1500}


def test_fill_two_runs_one_call(monkeypatch):
    segments = [
        seg("One.", 0, None),
        seg("Two.", None, 2000),
        seg("Full.", 2000, 3000),
        seg("Three.", 3000, None),
        seg("Four.", None, 5000),
    ]
    calls = mock_align(
        monkeypatch,
        [
            entry("One. Two.", [word("One", 0, 200), word("Two", 300, 500)], start=0.0, end=2.0),
            entry("Three. Four.", [word("Three", 3000, 3200), word("Four", 3300, 3500)], start=3.0, end=5.0),
        ],
    )

    result = merge_segments(segments, audio=np.zeros(16000))

    assert len(calls["texts"]) == 2  # one align call, all runs together
    assert result[0]["endMs"] == 200
    assert result[1]["startMs"] == 300
    assert result[3]["endMs"] == 3200
    assert result[4]["startMs"] == 3300


def test_fill_word_count_mismatch_skips_run(monkeypatch):
    segments = [seg("One two three.", 1000, None), seg("Four five six.", None, 4000)]
    mock_align(
        monkeypatch, [entry("One two three. Four five six.", [word("One", 1000, 1200)])]
    )  # 1 word instead of 6

    result = merge_segments(segments, audio=np.zeros(16000))

    assert result == [dict(s) for s in segments]


def test_fill_no_words_skips_run(monkeypatch):
    segments = [seg("One two three.", 1000, None), seg("Four five six.", None, 4000)]
    mock_align(monkeypatch, [entry("One two three. Four five six.", [])])

    result = merge_segments(segments, audio=np.zeros(16000))

    assert result == [dict(s) for s in segments]


def test_fill_no_runs_does_not_align(monkeypatch):
    def should_not_be_called(*args, **kwargs):
        raise AssertionError("align must not run without runs")

    monkeypatch.setattr(ms, "load_aligner", should_not_be_called)
    monkeypatch.setattr(ms, "align_texts", should_not_be_called)
    segments = [seg("A.", 0, 1000), seg("B.", 1000, 2000)]

    result = merge_segments(segments, audio=np.zeros(16000))

    assert result == [dict(s) for s in segments]


def test_fill_input_segments_not_mutated(monkeypatch):
    segments = [seg("One two three.", 1000, None), seg("Four five six.", None, 4000)]
    mock_align(
        monkeypatch,
        [
            entry(
                "One two three. Four five six.",
                [word("One", 1000, 1200), word("two", 1300, 1500), word("three.", 1600, 1800),
                 word("Four", 2000, 2200), word("five", 2300, 2500), word("six.", 2600, 2800)],
            )
        ],
    )

    merge_segments(segments, audio=np.zeros(16000))

    assert "endMs" not in segments[0]
    assert "startMs" not in segments[1]
