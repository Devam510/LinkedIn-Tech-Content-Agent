"""
filter/config.py — Configurable keyword lists for the scoring engine.
Edit HIGH_SIGNAL_KEYWORDS and NOISE_KEYWORDS to tune relevance.
"""

HIGH_SIGNAL_KEYWORDS: list[str] = [
    # AI / ML
    "AI", "LLM", "GPT", "Claude", "Gemini", "ChatGPT", "agent", "RAG",
    "fine-tune", "fine tuning", "multimodal", "embedding", "vector",
    "transformer", "diffusion", "benchmark", "model", "inference",
    # Dev / Tools
    "open source", "launch", "release", "v2", "v3", "API", "SDK",
    "Python", "Rust", "Go", "TypeScript", "WebAssembly",
    "framework", "library", "tool", "CLI", "terminal",
    # Business / Startup
    "startup", "funding", "raises", "Series A", "Series B", "YC",
    "acqui", "open-source", "developer",
    # Cloud / Infra
    "cloud", "edge computing", "serverless", "container", "Kubernetes",
    "database", "vector db", "performance", "latency", "throughput",
    # Research
    "research", "paper", "study", "breakthrough", "discovered",
]

NOISE_KEYWORDS: list[str] = [
    "opinion", "rant", "hot take", "drama",
    "NFT", "crypto scam", "metaverse", "web3 hype",
    "politics", "election", "war",
    "celebrity", "sports",
    "Ask HN", "askHN", "Tell HN",
    "hiring", "job post", "we're hiring",
]

# Minimum score for an item to be considered
MIN_SCORE_THRESHOLD: float = 0.5

# Number of top items to pass to the LLM
TOP_N_ITEMS: int = 5
