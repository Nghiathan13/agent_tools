# Chromium helpers

Chạy từ root của repository:

```bash
PYTHON=.venv/bin/python
```

- Mở Chromium nếu chưa chạy: `$PYTHON helpers/open_chromium.py`
- Đóng Chromium agent: `$PYTHON helpers/close_chromium.py`
- Mở tab: `$PYTHON helpers/new_tab.py 'https://example.com'`
- Lưu snapshot tab: `$PYTHON helpers/save_tabs.py`
- Xem tab trong snapshot: `$PYTHON helpers/show_open_tabs.py`
- Chuyển focus sang tab: `$PYTHON helpers/focus_tab.py '<id>'`
- Đóng tab theo ID: `$PYTHON helpers/close_tab.py '<id>'`

`open-tabs.json` chứa `focusedTabId` do helper đặt. Click tab thủ công trong Chromium chưa được theo dõi.
