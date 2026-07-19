# Agent instructions

Run commands from the repository root with `.venv/bin/python`. If `.venv` does not exist, run `bash setup.sh` first.

Use helpers instead of reading or editing local state files directly:

- `helpers/show_open_tabs.py` lists tabs and helper-managed focus.
- `helpers/focus_tab.py <id>` sets the working tab.
- `chatgpt/show_sessions.py` lists saved ChatGPT sessions.
- `chatgpt/open_chatgpt.py new-session <prompt>` creates a conversation in the focused ChatGPT tab.
- `chatgpt/open_chatgpt.py session <id> <prompt>` continues a saved conversation in that tab.

`profile/`, `open-tabs.json`, and `chatgpt/sessions.json` are local private state. Never commit or edit them manually. `focusedTabId` reflects the last focus set by a helper, not manual tab clicks.
