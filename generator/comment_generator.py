"""
generator/comment_generator.py — LLM chain for writing engaging LinkedIn comments.
"""
from tenacity import retry, stop_after_attempt, wait_fixed
from generator.llm_client import call_llm
from utils.logger import log

COMMENT_SYSTEM_PROMPT = """\
You are a senior tech professional, data analyst, and builder on LinkedIn.
You are reading a post from a connection in your network.
Your goal is to write a single, highly engaging, empathetic, and intelligent comment.

Rules for your comment:
1. ADD VALUE: Do not just say "Great post!" or "Thanks for sharing." Add a specific insight, ask a smart follow-up question, or share a brief related experience.
2. BE CONCISE: 1-3 sentences maximum. Keep it punchy.
3. TONE: Warm, professional, supportive, but intellectually sharp. Not robotic.
4. FORMAT: Plain text only. No hashtags. 1 emoji maximum.
5. CONTEXT: Directly reference something specific they said so it proves you read it.
"""

def build_comment_user_prompt(author: str, post_text: str) -> str:
    return f"""\
Author: {author}
Post: "{post_text}"

Write a thoughtful comment to leave on this post.
"""

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def generate_comment(author: str, post_text: str) -> str:
    """Generate a highly contextual LinkedIn comment."""
    log.info(f"[CommentGen] Drafting comment for post by {author}...")
    user_prompt = build_comment_user_prompt(author, post_text)
    
    raw = call_llm(COMMENT_SYSTEM_PROMPT, user_prompt)
    
    # Strip quotes if the LLM wrapped the comment in them
    cleaned = raw.strip(' "''')
    log.debug(f"[CommentGen] Drafted: {cleaned}")
    return cleaned
