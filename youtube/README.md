# Tool youtube

Bộ công cụ lấy dữ liệu từ YouTube — transcript, lời bài hát, audio, metadata. Chạy bằng `.venv` của repo agent_tools.

## Cài đặt

```bash
cd agent_tools
# 1) torch CUDA (bắt buộc cài TRƯỚC — whisperx pin torch ~=2.8.0)
.venv/bin/pip install torch==2.8.0 torchaudio==2.8.0 torchvision==0.23.0 \
  --index-url https://download.pytorch.org/whl/cu128
# 2) các dependency còn lại
.venv/bin/pip install -r youtube/requirements.txt
```

whisperx dùng wav2vec2 (tự tải `facebook/wav2vec2-base-960h` ~360MB từ HuggingFace lần đầu chạy) để forced alignment word-level; máy có GPU thì align chạy CUDA.

## Cấu trúc

```
youtube/
├── requirements.txt        # dependency chung toàn folder
├── fetch_audio.py          # CLI: tải audio track tốt nhất (giữ format gốc, không re-encode)
├── trim_audio.py           # CLI: cắt audio theo ms (không re-encode); --url tự tải audio
├── common/                 # thư viện dùng chung (validate_url)
├── tests/                  # test fetch_audio + trim_audio
└── transcript/             # pipeline transcript + lời bài hát (chi tiết: transcript/README.md)
    ├── helper/             # thư viện thuần: fetch_transcript, find_word, separate_vocals
    └── music/              # build_lyrics (tool tổng) + helper lọc/gộp lyrics
```

## Dùng nhanh

```bash
PYTHON=.venv/bin/python

# Lời bài hát + metadata (title/author/duration): URL -> fetch transcript -> filter ♪ -> merge
$PYTHON youtube/transcript/music/build_lyrics.py 'URL' --min-words 3 --max-words 25

# Audio: tải track tốt nhất / cắt theo ms
$PYTHON youtube/fetch_audio.py 'URL' -o audio
$PYTHON youtube/trim_audio.py audio.webm --start 45000 --end 75000
```

## Test

```bash
.venv/bin/pytest    # youtube/common + youtube/tests + youtube/transcript/* (không cần mạng)
```
