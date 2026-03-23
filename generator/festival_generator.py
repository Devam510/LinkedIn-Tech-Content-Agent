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

Write a single LinkedIn post to thoughtfully wish your network a wonderful {festival_name}.

Structure:
1. WARM HOOK: A short, genuine greeting for {festival_name}.
2. THE BUILDER'S TIE-IN: A reflection on how the themes of {festival_name} (like light, renewal, gratitude, hard work, etc.) apply to our lives as builders, developers, or founders.
3. INQUIRY / CTA: A warm wrap-up asking the audience how they are celebrating or resting.
4. HASHTAGS: 3-5 relevant tags (including the festival name).

Rules:
- Maximum 1000 characters total.
- Separate every section with a blank line.
- No markdown bold (**text**) — plain text only.
- Very light use of emojis is okay.
- Do NOT include section labels (like 'WARM HOOK', 'CTA', etc.) in the text.
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
