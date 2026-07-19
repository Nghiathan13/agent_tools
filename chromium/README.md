# Chromium cho agent

Một Chromium riêng, điều khiển qua helper Python, có thể dùng để hỏi ChatGPT trong profile cục bộ của người dùng.

## Cài đặt

Yêu cầu: Python 3 và môi trường desktop Linux/macOS.

```bash
git clone <repository-url> agent_tools
cd agent_tools/chromium
bash setup.sh
```

Lần đầu mở Chromium, người dùng tự đăng nhập ChatGPT trong cửa sổ đó. Profile đăng nhập chỉ nằm ở máy cục bộ và bị Git bỏ qua.

## Dùng nhanh

```bash
PYTHON=.venv/bin/python

# Quản lý Chromium
$PYTHON helpers/open_chromium.py
$PYTHON helpers/show_open_tabs.py
$PYTHON helpers/close_chromium.py

# Hỏi ChatGPT
$PYTHON chatgpt/open_chatgpt.py new-session 'Câu hỏi'
$PYTHON chatgpt/show_sessions.py
$PYTHON chatgpt/open_chatgpt.py session '<id>' 'Câu hỏi tiếp theo'
```

Hướng dẫn helper Chromium: [helpers/README.md](helpers/README.md). Hướng dẫn ChatGPT: [chatgpt/README.md](chatgpt/README.md). Hướng dẫn cho coding agent: [AGENTS.md](AGENTS.md).
