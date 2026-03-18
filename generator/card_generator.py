"""
generator/card_generator.py — Pillow fallback image card (1200×627 branded card).
Used when Gemini Imagen 3 is unavailable or quota is exceeded.
Requires: Pillow, Inter font files at utils/fonts/Inter-Bold.ttf & Inter-Regular.ttf
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
from utils.logger import log

FONTS_DIR = Path("utils/fonts")
FONT_BOLD    = FONTS_DIR / "Inter-Bold.ttf"
FONT_REGULAR = FONTS_DIR / "Inter-Regular.ttf"

WIDTH, HEIGHT = 1200, 627

BG_COLOR    = "#0D0D2B"   # deep navy
ACCENT_COLOR = "#6C63FF"  # vivid purple
TEXT_COLOR  = "#FFFFFF"
MUTED_COLOR = "#888888"
STRIP_WIDTH = 12


def _load_font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), size)
    except IOError:
        log.warning(f"[Card] Font not found at {path} — using default PIL font.")
        return ImageFont.load_default()


def create_text_card(headline: str, output_path: str = "data/post_image.png") -> str:
    """
    Generate a branded 1200×627 text card PNG for use as a LinkedIn post image.
    Returns the path to the saved image.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    img  = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Left accent bar
    draw.rectangle([(0, 0), (STRIP_WIDTH, HEIGHT)], fill=ACCENT_COLOR)

    # Subtle bottom gradient strip
    draw.rectangle([(0, HEIGHT - 60), (WIDTH, HEIGHT)], fill="#0A0A22")

    font_big = _load_font(FONT_BOLD, 56)
    font_sub = _load_font(FONT_REGULAR, 28)
    font_tag = _load_font(FONT_REGULAR, 24)

    # Wrap headline
    lines = textwrap.wrap(headline, width=30)
    y = 150
    for line in lines[:4]:   # max 4 lines to stay within card
        draw.text((80, y), line, font=font_big, fill=TEXT_COLOR)
        y += 78

    # Decorative accent line under headline
    draw.rectangle([(80, y + 10), (80 + 80, y + 14)], fill=ACCENT_COLOR)

    # Footer
    draw.text((80, HEIGHT - 46), "Daily Tech Brief  •  Powered by AI", font=font_tag, fill=MUTED_COLOR)

    img.save(output_path, format="PNG", optimize=True)
    log.info(f"[Card] Branded text card saved → {output_path}")
    return output_path
