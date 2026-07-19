#!/usr/bin/env python3
"""Show saved ChatGPT sessions without opening Chromium."""

import json
from pathlib import Path


sessions_path = Path(__file__).resolve().parent / "sessions.json"


def main() -> None:
    if not sessions_path.exists():
        print("No saved ChatGPT sessions.")
        return
    sessions = json.loads(sessions_path.read_text()).get("sessions", [])
    for session in sessions:
        print(
            f"{session['id']} | {session['title'] or '(untitled)'} | "
            f"last used {session['lastUsedAt']} | {session['url']}"
        )


if __name__ == "__main__":
    main()
