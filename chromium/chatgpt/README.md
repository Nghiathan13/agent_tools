# ChatGPT helper

Chạy từ root của repository:

```bash
PYTHON=.venv/bin/python
```

- Tạo session mới trong tab ChatGPT focus: `$PYTHON chatgpt/open_chatgpt.py new-session 'Câu hỏi'`
- Tiếp tục session đã lưu trong tab ChatGPT focus: `$PYTHON chatgpt/open_chatgpt.py session '<id>' 'Câu hỏi tiếp theo'`
- Xem session đã lưu: `$PYTHON chatgpt/show_sessions.py`

Nếu tab focus không phải ChatGPT hoặc chưa có tab nào, helper tạo tab ChatGPT mới và đặt nó thành focus. Log kỹ thuật đi stderr; câu trả lời hoàn chỉnh đi stdout. Dùng `--timeout <giây>` để đổi giới hạn tổng, mặc định 300 giây.

Focus được lưu trong `../open-tabs.json` và hiện chỉ phản ánh focus cuối cùng do helper đặt. `sessions.json` chỉ nằm ở máy cục bộ.
