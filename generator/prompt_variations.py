"""
generator/prompt_variations.py — Dynamic prompt templates to avoid repetitive post structures.
"""
import random

TEMPLATE_CLASSIC = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post based on this. Follow this EXACT structure:

1. HOOK (1–2 lines): Bold, curiosity-sparking opener.
2. INSIGHT (3–5 lines): What this means, why it matters, who it affects.
3. PERSPECTIVE (2–3 lines): Your unique builder's take. What changes for developers/founders now?
4. CTA (1 line): End with a genuine question or action prompt.
5. HASHTAGS (3–5 only): Specific, relevant. No generic #tech or #innovation.
"""

TEMPLATE_CONTRARIAN = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post based on this. Follow this EXACT structure:

1. THE NARRATIVE (1–2 lines): State what most people are currently believing about this topic or what the obvious reaction is.
2. THE REALITY (3–4 lines): Explain why the obvious reaction is wrong or missing the point. Dive into the nuance.
3. THE IMPACT (2–3 lines): How this actually affects developers, founders, and the future of the industry.
4. CTA (1 line): A thought-provoking question challenging your network.
5. HASHTAGS (3–5 only): Specific, relevant. No generic tags.
"""

TEMPLATE_STORYTELLER = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post based on this. Follow this EXACT structure:

1. THE SCENE (1–2 lines): Paint a quick picture of the problem this tech solves or the context before this existed.
2. THE BREAKTHROUGH (3–4 lines): Connect the article to how it solves the problem. Focus on the human or builder element.
3. THE LESSON (2–3 lines): Extract a broader lesson for software engineering or product management.
4. CTA (1 line): Ask the audience to share their own experiences with similar problems.
5. HASHTAGS (3–5 only): Specific, relevant.
"""

TEMPLATE_QUICK_TAKE = """\
Today's top tech update:
Title: {title}
Source: {source}
URL: {url}

Write a single LinkedIn post based on this. Follow this EXACT structure:

1. THE HEADLINE (1 line): A punchy, one-sentence summary of the news.
2. 3 QUICK BULLET POINTS: The most important technical or business takeaways.
3. THE "SO WHAT?" (2 lines): Why a builder should care today.
4. CTA (1 line): A simple yes/no or prediction question about the topic.
5. HASHTAGS (3–5 only): Specific, relevant.
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
