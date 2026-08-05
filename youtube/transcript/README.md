# Tool transcript

Pipeline transcript + lời bài hát trong `youtube/transcript/` (music + speech). Cài đặt chung, console scripts và helper dùng chung (`youtube/common/`): xem [youtube/README.md](../README.md).

## Dùng nhanh

```bash
# Lời bài hát: URL -> fetch -> giữ ♪ -> merge thành dòng
.venv/bin/build-lyrics 'URL' --min-words 3 --max-words 25

# Transcript nội dung nói (BBC...): URL -> fetch -> clean \n -> merge -> fill timestamp thiếu
.venv/bin/build-transcript 'URL' --max-words 15
```

Cách chạy tương đương: `.venv/bin/python -m youtube.transcript.music.build_lyrics 'URL'` (từ repo root) — không còn chạy trực tiếp `python file.py` vì code import theo package.

## Helper — thư viện thuần (import theo package, không có CLI)

```python
# youtube/transcript/helper/ — pipeline transcript chung
from youtube.transcript.helper.fetch_transcript import fetch_segments, fetch_segments_and_metadata, fetch_xml
from youtube.transcript.helper.separate_vocals import separate_vocals, pick_device

# youtube/transcript/music/helper/ — riêng music
from youtube.transcript.music.helper.filter_lyrics import filter_lyrics, strip_markers
from youtube.transcript.music.helper.merge_lyrics import merge_lyrics

# youtube/transcript/speech/helper/ — riêng speech
from youtube.transcript.speech.helper.clean_text import clean_text
from youtube.transcript.speech.helper.merge_segments import merge_segments
```

- `fetch_segments(video_id)` → [{text, startMs, endMs}]; `fetch_segments_and_metadata(video_id, languages=("en",))` → (segments, {title, author, duration}) từ CÙNG 1 player response; `fetch_xml(video_id)` → timedtext thô
- `separate_vocals.separate_vocals(audio, output)` → tách vocal bằng demucs (htdemucs_ft)

## Tool music (`music/`)

```bash
.venv/bin/build-lyrics 'URL' [--min-words N] [--max-words N] [--keep-markers]
```

Giữ segment ♪ (mặc định strip ♪), gộp theo flag:

- min + max: gộp segment < min (nếu tổng < max)
- max only: gộp thành block dài nhất ≤ max từ
- min only: gộp segment < min từ cho đến khi đủ (không giới hạn trên)
- không flag: giữ nguyên

## Tool speech (`speech/`)

```bash
.venv/bin/build-transcript 'URL' [--max-words N]
```

Hoàn chỉnh câu theo .!? → split chunk > max tại .!? (mảnh đầu giữ startMs, cuối giữ endMs, giữa trống) → pack ngược < max. Có `--max-words` thì tự tải audio tạm và align 1 lần để điền mốc THẬT cho mảnh thiếu (chỉ fill key trống, không ghi đè). BBC caption là `en-GB` → tự fetch `("en-GB", "en")`. Kết quả ghi `output/{videoId}.json` (đã ignore trong git).
