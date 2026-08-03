# Tool lấy transcript YouTube

Lấy script (transcript/subtitle) từ video YouTube chỉ qua URL hoặc video ID, dùng [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) — pure Python, nhanh, không cần tải video hay chạy JS runtime.

Cài đặt chung (torch CUDA + requirements.txt): xem [youtube/README.md](../README.md).

## Dùng nhanh

```bash
PYTHON=.venv/bin/python

# Lời bài hát + metadata (title/author/duration): URL -> fetch transcript -> filter ♪ -> merge
$PYTHON youtube/transcript/music/build_lyrics.py 'URL' --min-words 3 --max-words 25
```

Hỗ trợ mọi định dạng URL YouTube: `watch?v=`, `youtu.be/`, `shorts/`, `embed/`, `live/`, hoặc video ID trần 11 ký tự.

## Helper

Các helper là THƯ VIỆN THUẦN (chỉ import được, không có CLI):

```python
# youtube/common/ — dùng chung toàn bộ tool
from common.validate_url import extract_video_id
from common.fetch_audio import download_audio
from common.align_text import align_texts, find_words

# youtube/transcript/helper/ — riêng pipeline transcript
from helper.fetch_transcript import fetch_segments, fetch_segments_and_metadata, fetch_xml
from helper.find_word import prepare_audio, crop_audio, load_aligner, align_sentence, find_word_in
from helper.separate_vocals import separate_vocals, pick_device
```

- `fetch_transcript.fetch_segments(video_id)` → segments {text, startMs, endMs}
- `fetch_transcript.fetch_segments_and_metadata(video_id)` → (segments, {title, author, duration}) — cùng 1 player response
- `fetch_transcript.fetch_xml(video_id)` → XML thô timedtext
- `find_word.*` → align wav2vec2 để tìm timestamp từ (crop numpy trong RAM, không cần file trung gian)
- `separate_vocals.separate_vocals(audio, output)` → tách vocal bằng demucs (htdemucs_ft)
- `align_text.align_texts(texts, model, metadata, audio, device)` → align NHIỀU {text, start, end} window trong 1 lần gọi (1 forward pass) → words {word, start_ms, end_ms}; `find_words(entries, targets)` → timestamp từ mong muốn

Tool audio CLI đặt ở `youtube/` (chạy trực tiếp được):

```bash
# Cắt audio theo phạm vi thời gian (ms) — input file audio, không re-encode
$PYTHON youtube/trim_audio.py audio.webm --start 45000 --end 75000

# Hoặc cắt thẳng từ URL (tự tải audio qua common/fetch_audio rồi cắt, dọn file tạm)
$PYTHON youtube/trim_audio.py --url 'URL' --start 45000 --end 75000 -o clip.webm
```

## Tool music

Lấy lời bài hát từ URL (trong `music/`):

```bash
# PIPELINE TỔNG: URL -> fetch transcript -> filter ♪ -> merge thành dòng
# Input như merge: --min-words / --max-words (mặc định strip ♪, dùng --keep-markers nếu cần)
$PYTHON youtube/transcript/music/build_lyrics.py 'URL' --min-words 3 --max-words 25

# Các helper music (trong music/helper/, thư viện thuần — chỉ import được):
#   filter_lyrics.filter_lyrics(segments): giữ segment ♪, clean \n
#   filter_lyrics.strip_markers(text): bỏ dấu ♪
#   merge_lyrics.merge_lyrics(segments, min_words, max_words):
#     --min-words 3 --max-words 25: gộp segment < 3 từ (nếu tổng < 25), thêm "." giữa 2 segment
#     max-words 25 (không min): gộp tất cả thành block dài nhất ≤ 25 từ
#     min-words 3 (không max): gộp segment < 3 từ cho đến khi đủ 3 từ (không giới hạn trên)
#     không flag: giữ nguyên

Lưu ý find_word: cửa sổ thời gian là của CÂU (từ caption); text phải chứa word;
crop trong bộ nhớ nên chính xác tuyệt đối theo ms. Wav2vec2 không align được số/ký hiệu (vd "2014")
→ trả null. Tùy chọn model khác qua `load_aligner(model_name=...)` (vd large-960h).
Trên video NHẠC, nên tách vocal trước (separate_vocals) rồi align trên vocals — đo thực tế:
lệch drift cuối câu giảm từ ~3s xuống ~0.1s (world).

## Tool speech

Transcript cho nội dung NÓI sạch (BBC 6 Minute English...) trong `speech/`:

```bash
# PIPELINE TỔNG: URL -> fetch caption -> clean \n -> merge -> fill timestamp thiếu
# --max-words: gom câu thành chunk ≤ max từ (split quá dài tại .!?); khi có flag,
# tool tự tải audio tạm (common/fetch_audio) và align để điền mốc THẬT cho chunk thiếu
$PYTHON youtube/transcript/speech/build_transcript.py 'URL' --max-words 15
```

- Caption BBC là `en-GB` → build tự fetch `("en-GB", "en")`
- `merge_segments(segments, max_words, audio)`: hoàn chỉnh câu theo .!? → split chunk quá
  max (mảnh đầu giữ startMs, cuối giữ endMs, giữa trống) → pack ngược < max; có `audio` thì
  tự gom run thiếu → align_texts 1 lần → cắt theo word-count → fill key thiếu (không ghi đè)
- Kết quả ghi `output/{videoId}.json` (đã bỏ qua trong git)

Test: `.venv/bin/pytest` (youtube/common + youtube + youtube/transcript/*, không cần mạng).

## Lưu ý

- Video tắt transcript/subtitle sẽ báo lỗi (YouTubeTranscriptApiException).
- YouTube có thể chặn request (IpBlocked / "YouTube is blocking"): chờ một lúc rồi chạy lại.
- Tool chỉ lấy caption có sẵn; video không có caption thì cần fallback Whisper (chưa cài trong tool này).
