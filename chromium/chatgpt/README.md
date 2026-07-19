# Helper ChatGPT

Chạy từ root của repository:

```bash
PYTHON=.venv/bin/python
```

- Tạo session mới trong tab ChatGPT focus: `$PYTHON chatgpt/open_chatgpt.py new-session 'Câu hỏi'`
- Tiếp tục session đã lưu trong tab ChatGPT focus: `$PYTHON chatgpt/open_chatgpt.py session '<id>' 'Câu hỏi tiếp theo'`
- Xem session đã lưu: `$PYTHON chatgpt/show_sessions.py`

Nếu tab đang focus không phải ChatGPT hoặc chưa có tab nào, helper sẽ tạo tab ChatGPT mới và đặt nó thành focus. Log kỹ thuật được ghi ra `stderr`; câu trả lời hoàn chỉnh được ghi ra `stdout`. Dùng `--timeout <giây>` để đổi giới hạn tổng, mặc định là 300 giây.

Focus được lưu trong `../open-tabs.json` và hiện chỉ phản ánh focus cuối cùng do helper đặt. `sessions.json` chỉ nằm ở máy cục bộ.
