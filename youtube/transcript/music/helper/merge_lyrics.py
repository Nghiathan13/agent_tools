"""Merge lyric segments into lines using min/max word rules (music-specific logic)."""

SENTENCE_END = (".", "!", "?", "...", ",")


def word_count(text: str) -> int:
    """Count words, ignoring standalone '-' and '–' markers."""
    return len([w for w in text.split() if w not in ("-", "–")])


def join_text(cur_text: str, nxt_text: str) -> str:
    """Join two segments, adding a '.' between them when the first lacks sentence-ending punctuation."""
    cur_text = cur_text.strip()
    nxt_text = nxt_text.strip()
    if cur_text.endswith(SENTENCE_END):
        return f"{cur_text} {nxt_text}"
    return f"{cur_text}. {nxt_text}"


def merge_lyrics(
    segments: list[dict],
    min_words: int | None = None,
    max_words: int | None = None,
) -> list[dict]:
    """Merge short lyric segments into longer lines.

    - No limits given: return segments unchanged.
    - max only: keep merging while cur + next stays below max.
    - min only: keep merging while cur stays below min (no upper bound).
    - min + max: merge when cur < min and cur + next < max; a segment
      larger than max is skipped together with the current one (i += 2).
    """
    if min_words is None and max_words is None:
        return [dict(segment) for segment in segments]
    merged = [dict(segment) for segment in segments]
    i = 0
    while i + 1 < len(merged):
        cur = merged[i]
        nxt = merged[i + 1]
        if max_words is not None and word_count(nxt["text"]) > max_words:
            i += 2
            continue
        cur_wc = word_count(cur["text"])
        under_min = min_words is None or cur_wc < min_words
        under_max = max_words is None or cur_wc + word_count(nxt["text"]) < max_words
        if under_min and under_max:
            cur["text"] = join_text(cur["text"], nxt["text"])
            if "endMs" in nxt:
                cur["endMs"] = nxt["endMs"]
            del merged[i + 1]
            continue  # i stays: re-check the merged segment
        i += 1
    return merged
