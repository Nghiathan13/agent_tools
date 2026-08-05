# Tool youtube

Bộ công cụ lấy dữ liệu từ YouTube — transcript, lời bài hát, audio, metadata. Chạy bằng `.venv` của repo agent_tools; package `youtube` cài editable nên console scripts nằm trong `.venv/bin`.

## Cài đặt

```bash
cd agent_tools
# 1) torch CUDA (bắt buộc TRƯỚC — whisperx pin torch ~=2.8.0)
.venv/bin/pip install torch==2.8.0 torchaudio==2.8.0 torchvision==0.23.0 \
  --index-url https://download.pytorch.org/whl/cu128
# 2) dependency còn lại
.venv/bin/pip install -r youtube/requirements.txt
# 3) cài package youtube + console scripts (build-lyrics, build-transcript, trim-audio)
.venv/bin/pip install -e . --no-build-isolation
```

whisperx dùng wav2vec2 (tự tải `facebook/wav2vec2-base-960h` ~360MB từ HuggingFace lần đầu chạy) để forced alignment word-level; máy có GPU thì align chạy CUDA.

## Cấu trúc

```
youtube/
├── requirements.txt        # dependency chung toàn folder
├── trim_audio.py           # CLI: cắt audio theo ms (không re-encode); --url tự tải audio
├── common/                 # thư viện dùng chung (import-only): validate_url, fetch_audio, align_words
├── tests/                  # test trim_audio
└── transcript/             # pipeline transcript + lời bài hát (chi tiết: transcript/README.md)
    ├── helper/             # thư viện thuần: fetch_transcript, separate_vocals
    ├── music/              # build_lyrics (tool tổng) + helper lọc/gộp lyrics (output/ bị git bỏ qua)
    └── speech/             # build_transcript (tool tổng cho nội dung nói, output/ bị git bỏ qua)
```

Mọi thư mục đều là package (có `__init__.py`); code import theo đường dẫn package (`youtube.common.*`, `youtube.transcript.*`) — không còn sys.path hack, nên không chạy trực tiếp `python file.py` được.

## Dùng nhanh

```bash
# Lời bài hát + metadata (title/author/duration): URL -> fetch transcript -> filter ♪ -> merge
.venv/bin/build-lyrics 'URL' --min-words 3 --max-words 25

# Transcript nội dung nói (BBC...): URL -> fetch caption (en-GB) -> clean -> merge -> fill timestamp thiếu
.venv/bin/build-transcript 'URL' --max-words 15

# Audio: cắt theo ms (không re-encode); --url tự tải audio qua common/fetch_audio rồi cắt
.venv/bin/trim-audio audio.webm --start 45000 --end 75000
.venv/bin/trim-audio --url 'URL' --start 45000 --end 75000 -o clip.webm
```

Cách chạy tương đương: `.venv/bin/python -m youtube.transcript.music.build_lyrics 'URL'` (từ repo root). Hỗ trợ mọi URL YouTube: `watch?v=`, `youtu.be/`, `shorts/`, `embed/`, `live/`, hoặc video ID 11 ký tự.

## Helper dùng chung (`youtube/common/`, import-only)

```python
from youtube.common.validate_url import extract_video_id
from youtube.common.fetch_audio import download_audio
from youtube.common.align_words import prepare_audio, load_aligner, pick_device, align_words, find_words
```

- `validate_url.extract_video_id(url)` → video ID hoặc None; `is_valid_youtube_url(url)` → bool
- `fetch_audio.download_audio(url, output)` → yt-dlp bestaudio giữ định dạng gốc (không re-encode), trả Path file thật
- `align_words` → align wav2vec2 lấy word timestamp: `prepare_audio(path)` → waveform 16 kHz; `load_aligner(language, device)` → model có cache (load 1 lần, align nhiều); `pick_device()` → "cuda"/"cpu"; `align_words([{text, start, end}], model, metadata, audio, device)` → align NHIỀU window trong 1 forward pass; `find_words(entries, targets)` → timestamp từ. Cửa sổ là của CÂU (caption) và text phải chứa word; wav2vec2 không align được số/ký hiệu (vd "2014"); video nhạc nên tách vocal trước (drift cuối câu giảm ~3s → ~0.1s)

## Lưu ý

- Video tắt transcript/subtitle → `YouTubeTranscriptApiException`.
- YouTube chặn request tạm (`IpBlocked`) khi gọi liên tục: chờ rồi chạy lại.
- Chỉ lấy caption có sẵn; video không caption cần fallback Whisper (chưa có trong tool).
- Test: `.venv/bin/pytest` (offline).
