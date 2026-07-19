# Helper ChatGPT

Chạy từ root của repository:

```bash
PYTHON=.venv/bin/python
```

- Tạo session mới trong tab ChatGPT focus: `$PYTHON chatgpt/open_chatgpt.py new-session 'Câu hỏi'`
- Tiếp tục session đã lưu: `$PYTHON chatgpt/open_chatgpt.py session '<id>' 'Câu hỏi tiếp theo'`
- Xem session đã lưu: `$PYTHON chatgpt/show_sessions.py`
- Xóa session đã lưu: `$PYTHON chatgpt/delete_session.py '<id>'`

Với `new-session`, helper tìm tab có URL chính xác `https://chatgpt.com/` và focus tab đó. Nếu không có, helper tạo tab ChatGPT mới. Các URL `/c/<id>` là session cũ và không được dùng để tạo session mới. Với `session`, helper tìm tab có URL chính xác bằng URL đã lưu của session; nếu không có, helper dùng tab root hoặc tạo tab root rồi điều hướng đến URL đó. Log kỹ thuật được ghi ra `stderr`; câu trả lời hoàn chỉnh được ghi ra `stdout`. Dùng `--timeout <giây>` để đổi giới hạn tổng, mặc định là 300 giây.

Focus được lưu trong `../open-tabs.json` và hiện chỉ phản ánh focus cuối cùng do helper đặt. `sessions.json` chỉ nằm ở máy cục bộ.

Lệnh xóa mở menu ba chấm của đúng session, xác nhận dialog Delete, kiểm tra session biến mất khỏi sidebar rồi mới xóa record tương ứng trong `sessions.json`.
