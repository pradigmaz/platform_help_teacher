"""Shared helpers for announcement delivery and formatting."""

import re

from app.models.announcement import Announcement


def build_delivery_stats() -> dict[str, int]:
    """Create the default delivery stats payload."""
    return {"telegram_sent": 0, "vk_sent": 0, "skipped": 0, "errors": 0}


def normalize_announcement_text(content: str) -> str:
    """Render markdown-ish content to plain text for bot delivery."""
    text = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", content)
    text = re.sub(r"^[#>\-\*\+]+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`~]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_announcement_message(announcement: Announcement) -> str:
    """Format announcement text for Telegram/VK without markdown rendering."""
    content = normalize_announcement_text(announcement.content)
    return f"📢 {announcement.title}\n\n{content[:1000]}".strip()
