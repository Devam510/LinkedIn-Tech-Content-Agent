"""
generator/image_generator.py — Image generation orchestrator.
Primary: Gemini Imagen 3 (topic-specific AI image).
Fallback: Pillow branded text card (zero API cost).
"""
import os
from pathlib import Path
from utils.logger import log
from generator.card_generator import create_text_card

IMAGE_OUTPUT = "data/post_image.png"

# Keyword → visual prompt map for more relevant images
TOPIC_VISUAL_MAP: dict[str, str] = {
    "AI":          "futuristic glowing neural network diagram, dark background, vivid blue and purple",
    "LLM":         "abstract large language model architecture, floating tokens, deep space aesthetic",
    "agent":       "autonomous AI robot navigating a tech maze, cinematic lighting",
    "open source": "collaborative developers on glowing screens, open community feel",
    "startup":     "modern high-energy tech startup office, whiteboard, fast-paced",
    "funding":     "graph showing exponential growth, investment flow, minimal dark design",
    "cloud":       "cloud infrastructure servers glowing blue, server racks, serverless",
    "Python":      "Python snake intertwined with glowing code lines, dark background",
    "Rust":        "metallic Rust programming language gear cogs, orange and dark grey",
    "security":    "shield protecting a glowing network, cyberpunk aesthetic",
    "database":    "glowing vector database nodes interconnected, dark minimal",
    "research":    "scientific paper with AI brain overlay, academic meets futuristic",
}


def _build_image_prompt(item: dict) -> str:
    """Build a topic-aware Imagen prompt from item title/source."""
    title = item.get("title", "").lower()
    for keyword, visual in TOPIC_VISUAL_MAP.items():
        if keyword.lower() in title:
            return f"{visual}. Professional, flat design, no text overlays. LinkedIn 16:9."
    # Generic fallback prompt
    short_title = item.get("title", "")[:60]
    return (
        f"Modern tech illustration about: {short_title}. "
        "Flat design, dark background, vivid accent colours, no text. LinkedIn 16:9."
    )

FESTIVAL_VISUAL_MAP: dict[str, str] = {
    "New Year":         "colorful fireworks bursting over a glowing city skyline at midnight, festive and vibrant",
    "Diwali":           "hundreds of glowing oil diyas arranged in a pattern, warm golden light, dark night background, Indian festival, cinematic",
    "Holi":             "people joyfully throwing vivid rainbow powder in the air, bright colors exploding, celebration, India",
    "Gudi Padwa":       "traditional gudi flag decorated with colorful cloth and mango leaves, Indian New Year, bright morning sunlight, festive background",
    "Republic Day":     "Indian flag waving proudly against a blue sky, patriotic, national celebration",
    "Independence Day": "Indian tricolor flag against a golden sunrise sky, patriotic, freedom celebration",
    "Christmas":        "cozy decorated Christmas tree with glowing lights and ornaments, warmly lit room, festive",
    "Valentine":        "red and pink hearts on a warm bokeh background, romantic soft light",
    "Women's Day":      "diverse group of women celebrating together, vibrant colors, empowerment theme",
    "Earth Day":        "lush green planet earth from space, environmental awareness, clean energy",
    "Halloween":        "carved glowing jack-o-lanterns in autumn fog, spooky and cinematic",
    "Raksha Bandhan":   "colorful rakhi threads with flowers on a festive background, Indian celebration",
    "Teachers' Day":    "books and an apple on a wooden desk, warm light, knowledge and education theme",
    "Labor Day":        "diverse workers collaborating together, teamwork, professional setting, modern",
}


def _build_festival_image_prompt(festival_name: str) -> str:
    """Build a descriptive visual prompt specifically for a festival."""
    for keyword, visual in FESTIVAL_VISUAL_MAP.items():
        if keyword.lower() in festival_name.lower():
            return f"{visual}. Vibrant, professional, no text overlays. LinkedIn 16:9."
    # Generic festive fallback
    return (
        f"Festive celebration of {festival_name}, vibrant colors, joyful atmosphere, "
        "cultural decorations, warm lighting, no text overlays. LinkedIn 16:9."
    )


def get_festival_image(festival_name: str, output: str = IMAGE_OUTPUT) -> str:
    """
    Generate a festival-appropriate image.
    Uses AI (Pollinations) with a festive prompt, falls back to Unsplash or Pillow card.
    Does NOT attempt og:image scraping (no article URL exists for festivals).
    """
    festival_item = {"title": festival_name}  # slim item just for the fallback paths
    prompt = _build_festival_image_prompt(festival_name)

    # ── 1. Pollinations with festive prompt ────────────────────────────────────
    try:
        from generator.pollinations import fetch_pollinations_image
        # Override the item title with our rich festive prompt
        return fetch_pollinations_image({"title": prompt}, output)
    except Exception as e:
        log.warning(f"[FestivalImage] Pollinations failed ({e}) — trying Unsplash …")

    # ── 2. Unsplash with festival keyword ──────────────────────────────────────
    try:
        from generator.unsplash import fetch_unsplash_photo
        return fetch_unsplash_photo({"title": festival_name}, output_path=output)
    except Exception as e:
        log.warning(f"[FestivalImage] Unsplash failed ({e}) — using Pillow fallback …")

    # ── 3. Pillow branded card ─────────────────────────────────────────────────
    return create_text_card(headline=f"Happy {festival_name}! 🎉", output_path=output)


def _fetch_article_og_image(item: dict, output: str) -> str:
    """
    Fetch the og:image (Open Graph) from the article's source URL.
    This is the exact image the article author chose — always relevant.
    Returns output path on success, raises on failure.
    """
    import requests
    from bs4 import BeautifulSoup

    url = item.get("url", "")
    if not url:
        raise ValueError("No URL in item to fetch og:image from")

    if "github.com" in url.lower():
        log.info("[Image] Intercepted GitHub URL — skipping OG image to avoid generic repo cards.")
        raise ValueError("GitHub OG images are generic; forcing fallback.")

    log.info(f"[Image] Fetching og:image from: {url[:80]} …")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    og_image = None
    for tag in soup.find_all("meta"):
        prop = tag.get("property", "") or tag.get("name", "")
        if prop in ("og:image", "twitter:image"):
            og_image = tag.get("content", "").strip()
            if og_image:
                break

    if not og_image:
        raise ValueError("No og:image found on page")

    log.info(f"[Image] Downloading og:image: {og_image[:80]} …")
    img_resp = requests.get(og_image, headers=headers, timeout=15)
    img_resp.raise_for_status()

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        f.write(img_resp.content)
    log.info(f"[Image] og:image saved → {output}")
    return output


def get_post_image(item: dict, output: str = IMAGE_OUTPUT) -> str:
    """
    Orchestrate image generation — best quality first, graceful fallback:
      1. Pollinations.ai  — Free, custom AI-generated, topic-specific
      2. Article og:image — Exact image from source (if AI fails)
      3. Unsplash         — Professional web photo, topic-matched
      4. Pillow card      — Branded text card (zero cost, always works)
    Returns path to generated image.
    """
    # ── 1. Try Pollinations.ai (Free custom AI image) ──────────────────────────
    try:
        from generator.pollinations import fetch_pollinations_image
        return fetch_pollinations_image(item, output)
    except Exception as e:
        log.warning(f"[Image] Pollinations failed ({e}) — trying article og:image …")

    # ── 2. Try article's own og:image ──────────────────────────────────────────
    try:
        return _fetch_article_og_image(item, output)
    except Exception as e:
        log.warning(f"[Image] og:image fetch failed ({e}) — trying Unsplash …")

    # ── 3. Try Unsplash ────────────────────────────────────────────────────────
    try:
        from generator.unsplash import fetch_unsplash_photo
        return fetch_unsplash_photo(item, output_path=output)
    except Exception as e:
        log.warning(f"[Image] Unsplash failed ({e}) — using Pillow fallback …")

    # ── 4. Pillow branded card (always works) ──────────────────────────────────
    return create_text_card(headline=item.get("title", "Today in Tech"), output_path=output)
