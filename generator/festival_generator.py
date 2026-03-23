"""
generator/festival_generator.py — Dedicated generator for calendar-based festival posting.
"""
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from generator.llm_client import call_llm
from utils.logger import log

from generator.generator import PostQualityError, MIN_POST_LENGTH, MAX_POST_LENGTH

FESTIVAL_SYSTEM_PROMPT = """\
You are a senior tech builder and thought leader on LinkedIn.
Your audience: developers, founders, PMs, and tech enthusiasts.
Your style: sharp, warm, empathetic, professional — no corporate jargon.
You write holiday/festival greeting posts that spark genuine joy and connection, while tying back gracefully to productivity, building, or team culture without being forced.
"""

def build_festival_prompt(festival_name: str) -> str:
    return f"""\
Today is {festival_name}.

Write a single warm, professional LinkedIn post to wish your network a meaningful {festival_name}.

Guidelines:
- Open with a genuine, heartfelt sentiment — but NOT a generic "Happy {festival_name}!" first line.
- Weave in a builder's perspective: how the themes of {festival_name} (light, renewal, gratitude, new beginnings, hard work) connect to careers, teams, or building things.
- Closing: choose ONE that fits the tone naturally — a warm statement, a reflection, an inspiration, or a question. Rotate between these. Do NOT always end with a question. A beautiful closing line is often better.
- 3-5 relevant hashtags at the end.

Rules:
- Maximum 900 characters total (excluding hashtags).
- Separate paragraphs with a blank line.
- No markdown formatting — plain text only.
- 1-2 emojis max, not in the first line.
- Sound like a warm, real human — not a corporate newsletter or an AI chatbot.
- Do NOT include section labels in the text.
"""

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(PostQualityError),
    reraise=True,
)
def generate_festival_post(festival_name: str) -> str:
    """
    Generate a LinkedIn post specifically tailored to a festival.
    Retries up to 3 times if quality gate fails.
    Returns the cleaned post text.
    """
    log.info(f"[FestivalGen] Generating post for {festival_name} …")
    user_prompt = build_festival_prompt(festival_name)
    raw = call_llm(FESTIVAL_SYSTEM_PROMPT, user_prompt)

    # Quality gate
    if len(raw) < MIN_POST_LENGTH:
        raise PostQualityError(f"Post too short ({len(raw)} chars). Retrying …")
    if len(raw) > MAX_POST_LENGTH * 1.5:
        log.warning(f"[FestivalGen] Post is very long ({len(raw)} chars) — formatter will truncate.")

    log.info(f"[FestivalGen] Festival post generated ({len(raw)} chars).")
    return raw
