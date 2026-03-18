"""
generator/pollinations.py — Free AI Image Generation via Pollinations.ai.
No API key, no billing required. Uses state-of-the-art Flux models.
"""
import urllib.parse
import requests
from pathlib import Path
from utils.logger import log

from generator.image_generator import TOPIC_VISUAL_MAP

def _build_pollinations_prompt(item: dict) -> str:
    """Build a rich, descriptive prompt for Pollinations based on the article."""
    title = item.get("title", "").lower()
    
    # Check if we have a tailored visual for this topic
    visual_base = None
    for keyword, visual in TOPIC_VISUAL_MAP.items():
        if keyword.lower() in title:
            visual_base = visual
            break
            
    if not visual_base:
        # Generic high-quality tech fallback prompt
        short_title = item.get("title", "")[:60]
        visual_base = f"Modern tech illustration about: {short_title}"

    # Add style modifiers to ensure professional quality suitable for LinkedIn
    full_prompt = (
        f"{visual_base}. High quality, professional 3D render, flat design, "
        f"dark background, vivid accent colours, highly detailed, no text overlays, "
        f"corporate technology aesthetic, 8k resolution."
    )
    return full_prompt

def fetch_pollinations_image(item: dict, output_path: str = "data/post_image.png") -> str:
    """
    Generates a free custom AI image via Pollinations.ai.
    Returns path to saved image on success, raises on failure.
    """
    prompt = _build_pollinations_prompt(item)
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Use standard LinkedIn post aspect ratio (approx 1200x627, we use 1280x720)
    # nologo=true removes the pollinations watermark
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&model=flux&nologo=true"
    
    log.info(f"[Pollinations] Generating image for prompt: {prompt[:80]}…")
    
    headers = {
        "User-Agent": "LinkedInAgent/1.0",
    }
    
    # Give it up to 30 seconds as image generation takes a moment
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.warning(f"[Pollinations] API error (likely rate limited or 500): {e}")
        raise ValueError("Pollinations generation failed")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(resp.content)

    log.info(f"[Pollinations] AI Image saved → {output_path}")
    return output_path
