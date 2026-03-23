"""
generator/prompt_variations.py — Dynamic prompt templates to avoid repetitive post structures.
"""
import random

TEMPLATE_CLASSIC = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post based on this.

1. OPENING (1–2 lines): A sharp, direct statement that immediately conveys the significance of this news. Not a question.
2. CONTEXT (3–4 lines): What is happening, why it matters, who it affects. Give concrete, specific detail.
3. BUILDER'S TAKE (2–3 lines): What this means for developers or founders specifically. What do they need to act on or rethink?
4. CLOSE (1 line): End with EITHER a bold prediction, a call to action ("go build this"), or a sharp rhetorical closing statement. A question is allowed here but NOT required — use your judgment.
5. HASHTAGS (3–5 only): Specific and relevant.
"""

TEMPLATE_CONTRARIAN = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post based on this.

1. THE POPULAR TAKE (1–2 lines): State the obvious reaction most people in tech are having to this.
2. THE REAL PICTURE (3–4 lines): Challenge that narrative. What is everyone missing or oversimplifying? Bring in data, nuance, or a different lens.
3. THE ACTUAL IMPACT (2 lines): For a developer or founder, what does the reality — not the hype — actually mean?
4. CLOSE (1 line): A strong closing statement. A bold contrarian declaration or a sharp observation. Do NOT end with a generic question if a statement is more powerful.
5. HASHTAGS (3–5 only): Specific and relevant.
"""

TEMPLATE_STORYTELLER = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post based on this.

1. THE SCENE (1–2 lines): Set the stage. Describe the problem or the world that existed *before* this development.
2. THE SHIFT (3–4 lines): What changed? How does this technology or event alter that picture?
3. THE LESSON (2 lines): Extract one broad, honest lesson for anyone building software or products.
4. CLOSE (1 line): A concise, memorable final line — could be a quote-style observation, a challenge to the reader, or an inspirational close. A question is fine if it's genuinely thought-provoking, but do NOT default to it.
5. HASHTAGS (3–5 only): Specific and relevant.
"""

TEMPLATE_QUICK_TAKE = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post in a fast, punchy format.

1. ONE SENTENCE SUMMARY: Capture the news in a single razor-sharp sentence.
2. KEY TAKEAWAYS (3 bullet points): The most important things to know. Short, direct.
3. SO WHAT (2 lines): The single most important implication for a working developer or technical founder.
4. CLOSE (1 line): Something memorable. A prediction, a challenge, a provocation, or a closing insight. Not necessarily a question.
5. HASHTAGS (3–5 only): Specific and relevant.
"""

ALL_TEMPLATES = [
    TEMPLATE_CLASSIC,
    TEMPLATE_CONTRARIAN,
    TEMPLATE_STORYTELLER,
    TEMPLATE_QUICK_TAKE
]

def get_random_prompt_template() -> str:
    """Returns a randomly selected prompt template."""
    return random.choice(ALL_TEMPLATES)
