"""Tests for music/merge_lyrics.py."""

from merge_lyrics import join_text, merge_lyrics, word_count


def seg(text, start_ms, end_ms):
    return {"text": text, "startMs": start_ms, "endMs": end_ms}


def test_word_count_excludes_dash_markers():
    assert word_count("a - b – c") == 3
    assert word_count("Hey, hey, hey") == 3


def test_join_text_adds_dot_when_no_punctuation():
    assert join_text("Show you off", "Tonight") == "Show you off. Tonight"


def test_join_text_uses_space_when_already_punctuated():
    assert join_text("Done!", "Next") == "Done! Next"
    assert join_text("What...", "Oh") == "What... Oh"


def test_join_text_adds_dot_after_lyrics_with_inner_commas():
    # "Hey, hey, hey" has commas but does NOT end with sentence punctuation -> dot added
    assert join_text("Hey, hey, hey", "What you got") == "Hey, hey, hey. What you got"


def test_merge_no_limits_returns_unchanged():
    segments = [seg("a", 0, 1000), seg("b", 1000, 2000)]
    result = merge_lyrics(segments)
    assert result == segments
    assert result is not segments  # copy, not the original list


def test_merge_max_only_chains_until_max():
    segments = [seg("one", 0, 1000), seg("two", 1000, 2000), seg("three", 2000, 3000)]
    result = merge_lyrics(segments, max_words=5)
    assert len(result) == 1
    assert result[0]["text"] == "one. two. three"
    assert result[0]["startMs"] == 0
    assert result[0]["endMs"] == 3000


def test_merge_max_only_stops_at_max():
    segments = [seg("one two three four five", 0, 1000), seg("six seven", 1000, 2000)]
    result = merge_lyrics(segments, max_words=5)
    assert len(result) == 2  # 5 + 2 = 7 >= max -> no merge


def test_merge_min_and_max_merges_short_segments():
    segments = [
        seg("a b", 0, 1000),
        seg("c d", 1000, 2000),
        seg("e f g h", 2000, 3000),
    ]
    result = merge_lyrics(segments, min_words=3, max_words=10)
    assert len(result) == 2
    assert result[0]["text"] == "a b. c d"  # 2 < min -> merged; 4 words now
    assert result[0]["startMs"] == 0
    assert result[0]["endMs"] == 2000


def test_merge_keeps_merging_while_still_under_min():
    segments = [
        seg("a", 0, 1000),
        seg("b", 1000, 2000),
        seg("c", 2000, 3000),
    ]
    result = merge_lyrics(segments, min_words=3, max_words=10)
    assert len(result) == 1  # 1+1 -> 2 (< min) -> 2+1 -> 3 (>= min, stop)
    assert result[0]["text"] == "a. b. c"


def test_merge_skips_when_next_over_max():
    segments = [seg("x y", 0, 1000), seg("one two three four five six", 1000, 2000), seg("z w", 2000, 3000)]
    result = merge_lyrics(segments, min_words=3, max_words=5)
    # next (6 words) > max -> i += 2 -> cur "x y" stays short, "z w" untouched
    assert len(result) == 3
    assert result[0]["text"] == "x y"
    assert result[1]["text"] == "one two three four five six"


def test_merge_advances_when_cur_not_under_min():
    segments = [seg("a b c d", 0, 1000), seg("e f", 1000, 2000)]
    result = merge_lyrics(segments, min_words=3, max_words=10)
    assert len(result) == 2  # cur (4) >= min -> no merge, i += 1


def test_merge_min_only_chains_until_min():
    segments = [seg("a", 0, 1000), seg("b", 1000, 2000), seg("c", 2000, 3000),
                seg("d", 3000, 4000), seg("e", 4000, 5000), seg("f", 5000, 6000)]
    result = merge_lyrics(segments, min_words=3)
    assert [s["text"] for s in result] == ["a. b. c", "d. e. f"]


def test_merge_min_only_keeps_cur_when_at_min():
    segments = [seg("a b c", 0, 1000), seg("d e", 1000, 2000)]
    result = merge_lyrics(segments, min_words=3)
    assert len(result) == 2  # cur == min -> no merge, i += 1


def test_merge_min_only_last_short_segment_stays():
    segments = [seg("a b c", 0, 1000), seg("d", 1000, 2000)]
    result = merge_lyrics(segments, min_words=3)
    assert len(result) == 2  # "d" < min but no next -> stays
