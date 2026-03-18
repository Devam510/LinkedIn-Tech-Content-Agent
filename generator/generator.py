"""
generator/generator.py — Post generation with retry and quality gate.
"""
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from generator.llm_client import call_llm
from generator.prompts import SYSTEM_PROMPT, build_user_prompt
from utils.logger import log

MIN_POST_LENGTH = 200
MAX_POST_LENGTH = 1300


class PostQualityError(Exception):
    """Raised when a generated post fails quality checks."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(PostQualityError),
    reraise=True,
)
def generate_post(item: dict) -> str:
    """
    Generate a LinkedIn post for the given item.
    Retries up to 3 times if quality gate fails.
    Returns the cleaned post text.
    """
    log.info(f"[Generator] Generating post for: {item['title'][:60]} …")
    user_prompt = build_user_prompt(item)
    raw = call_llm(SYSTEM_PROMPT, user_prompt)

    # Quality gate
    if len(raw) < MIN_POST_LENGTH:
        raise PostQualityError(f"Post too short ({len(raw)} chars). Retrying …")
    if len(raw) > MAX_POST_LENGTH * 1.5:
        # Truncation will be handled in formatter; just warn
        log.warning(f"[Generator] Post is very long ({len(raw)} chars) — formatter will truncate.")

    log.info(f"[Generator] Post generated ({len(raw)} chars).")
    return raw
