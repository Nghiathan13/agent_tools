# Tool lấy transcript YouTube

Lấy script (transcript/subtitle) từ video YouTube chỉ qua URL hoặc video ID, dùng [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) — pure Python, nhanh, không cần tải video hay chạy JS runtime.

## Cài đặt

```bash
cd agent_tools
# 1) torch CUDA (bắt buộc cài trước — whisperx pin torch ~=2.8.0)
.venv/bin/pip install torch==2.8.0 torchaudio==2.8.0 torchvision==0.23.0 \
  --index-url https://download.pytorch.org/whl/cu128
# 2) các dependency còn lại
.venv/bin/pip install -r youtube/requirements.txt
```

whisperx dùng wav2vec2 (tự tải `facebook/wav2vec2-base-960h` ~360MB từ HuggingFace lần đầu chạy) để forced alignment word-level; máy có GPU thì align tự chạy trên CUDA.

## Dùng nhanh

```bash
PYTHON=.venv/bin/python

# Lời bài hát + metadata (title/author/duration): URL -> fetch transcript -> filter ♪ -> merge
$PYTHON youtube/transcript/music/build_lyrics.py 'URL' --min-words 3 --max-words 25
```

Hỗ trợ mọi định dạng URL YouTube: `watch?v=`, `youtu.be/`, `shorts/`, `embed/`, `live/`, hoặc video ID trần 11 ký tự.

## Helper

Các helper trong `transcript/helper/` là THƯ VIỆN THUẦN (chỉ import được, không có CLI):

```python
from helper.fetch_transcript import fetch_segments, fetch_segments_and_metadata, fetch_xml
from helper.find_word import prepare_audio, crop_audio, load_aligner, align_sentence, find_word_in
from helper.separate_vocals import separate_vocals, pick_device
```

- `fetch_transcript.fetch_segments(video_id)` → segments {text, startMs, endMs}
- `fetch_transcript.fetch_segments_and_metadata(video_id)` → (segments, {title, author, duration}) — cùng 1 player response
- `fetch_transcript.fetch_xml(video_id)` → XML thô timedtext
- `find_word.*` → align wav2vec2 để tìm timestamp từ (crop numpy trong RAM, không cần file trung gian)
- `separate_vocals.separate_vocals(audio, output)` → tách vocal bằng demucs (htdemucs_ft)

Tool audio CLI đặt ở `youtube/` (chạy trực tiếp được):

```bash
# Tải audio track tốt nhất (giữ format gốc, không re-encode) — input URL, output file audio
$PYTHON youtube/fetch_audio.py 'URL' -o audio

# Cắt audio theo phạm vi thời gian (ms) — input file audio, không re-encode
$PYTHON youtube/trim_audio.py audio.webm --start 45000 --end 75000

# Hoặc cắt thẳng từ URL (tự tải audio qua fetch_audio rồi cắt, dọn file tạm)
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

Test: `.venv/bin/pytest` (youtube/common + youtube + youtube/transcript/*, không cần mạng).

## Lưu ý

- Video tắt transcript/subtitle sẽ báo lỗi (YouTubeTranscriptApiException).
- YouTube có thể chặn request (IpBlocked / "YouTube is blocking"): chờ một lúc rồi chạy lại.
- Tool chỉ lấy caption có sẵn; video không có caption thì cần fallback Whisper (chưa cài trong tool này).
