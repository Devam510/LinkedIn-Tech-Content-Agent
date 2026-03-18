"""
generator/llm_client.py — Provider-agnostic LLM client.

Supported providers (set LLM_PROVIDER in .env):
  - "groq"   → Groq API (groq.com). gsk_ keys. Requires GROQ_API_KEY.
  - "grok"   → xAI Grok API (x.ai). xai- keys. Requires GROK_API_KEY.
  - "gemini" → Google Gemini Flash. Requires GEMINI_API_KEY.

Default: "groq"
"""
import os
from utils.logger import log


# ── Groq (groq.com) ───────────────────────────────────────────────────────────
def _call_groq(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in .env (get free key at console.groq.com)")
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    log.debug(f"[LLM] Calling Groq ({model}) …")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user",   "content": user_prompt.strip()},
        ],
        temperature=0.8,
        max_tokens=600,
    )
    text = response.choices[0].message.content.strip()
    log.debug(f"[LLM] Groq response: {len(text)} chars.")
    return text


# ── Grok (xAI) ────────────────────────────────────────────────────────────────
def _call_grok(system_prompt: str, user_prompt: str) -> str:
    from openai import OpenAI

    api_key = os.environ.get("GROK_API_KEY", "")
    if not api_key:
        raise ValueError("GROK_API_KEY is not set in .env")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )
    model = os.environ.get("GROK_MODEL", "grok-2")
    log.debug(f"[LLM] Calling Grok ({model}) …")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user",   "content": user_prompt.strip()},
        ],
        temperature=0.8,
        max_tokens=600,
    )
    text = response.choices[0].message.content.strip()
    log.debug(f"[LLM] Grok response: {len(text)} chars.")
    return text


# ── Gemini ────────────────────────────────────────────────────────────────────
def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env")

    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    log.debug(f"[LLM] Calling Gemini ({model_name}) …")

    model = genai.GenerativeModel(model_name)
    combined = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"
    response = model.generate_content(combined)
    text = response.text.strip()
    log.debug(f"[LLM] Gemini response: {len(text)} chars.")
    return text


# ── Public interface ──────────────────────────────────────────────────────────
def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Route the LLM call to the configured provider.
    Set LLM_PROVIDER=groq (default), grok, or gemini in .env
    """
    provider = os.environ.get("LLM_PROVIDER", "groq").lower().strip()

    if provider == "groq":
        log.info("[LLM] Provider: Groq (groq.com)")
        return _call_groq(system_prompt, user_prompt)
    elif provider == "grok":
        log.info("[LLM] Provider: Grok (xAI)")
        return _call_grok(system_prompt, user_prompt)
    elif provider == "gemini":
        log.info("[LLM] Provider: Gemini")
        return _call_gemini(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER='{provider}'. Use 'groq', 'grok', or 'gemini'.")
