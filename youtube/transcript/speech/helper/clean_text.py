"""Clean raw caption text for spoken-content transcripts."""


def clean_text(text: str) -> str:
    """Replace caption line-break artifacts (\\n) with a space."""
    return text.replace("\n", " ")
