"""
formatter/formatter.py — Post text cleanup and validation.
Strips markdown artifacts, enforces character limit, ensures readability.
"""
import re
from utils.logger import log

MAX_CHARS = 1300
TRUNCATE_SUFFIX = " …"


def _strip_markdown(text: str) -> str:
    """Remove markdown bold (**), italic (*), headers (#), and code fences."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)   # **bold** → bold
    text = re.sub(r"\*(.+?)\*",     r"\1", text)   # *italic* → italic
    text = re.sub(r"__(.+?)__",     r"\1", text)   # __bold__ → bold
    text = re.sub(r"#+\s",          "",    text)   # ## headers
    text = re.sub(r"```.*?```",     "",    text, flags=re.DOTALL)  # code fences
    text = re.sub(r"`(.+?)`",       r"\1", text)   # inline code
    return text


def _clean_spacing(text: str) -> str:
    """Normalise excessive blank lines (max 1 blank line between paragraphs)."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _enforce_limit(text: str) -> str:
    """Truncate to MAX_CHARS if needed, cutting at last full word."""
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS - len(TRUNCATE_SUFFIX)]
    # Cut at last newline or space to avoid mid-word truncation
    last_break = max(cut.rfind("\n"), cut.rfind(" "))
    if last_break > MAX_CHARS * 0.8:
        cut = cut[:last_break]
    log.warning(f"[Formatter] Post truncated from {len(text)} → {len(cut) + len(TRUNCATE_SUFFIX)} chars.")
    return cut + TRUNCATE_SUFFIX


def format_post(raw_text: str) -> str:
    """
    Full formatting pipeline:
    1. Strip markdown artifacts
    2. Clean spacing
    3. Enforce 1300-char limit
    Returns the clean, publish-ready post string.
    """
    text = _strip_markdown(raw_text)
    text = _clean_spacing(text)
    text = _enforce_limit(text)
    log.info(f"[Formatter] Post formatted — {len(text)} chars.")
    return text
