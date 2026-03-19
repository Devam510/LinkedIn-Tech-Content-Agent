# LinkedIn Agent — Task Tracker

> Track all implementation tasks here. Mark `[ ]` → `[/]` (in progress) → `[x]` (done).

---

## Phase 1 — Data Collection

- [x] Set up project structure and virtual environment (`venv`)
- [x] Create `requirements.txt` with all dependencies
- [x] Create `.env.example` with all required env variable keys
- [x] Implement `utils/db.py` — SQLite schema (`raw_items`, `posted_history`)
- [x] Implement `scraper/base.py` — base fetch with tenacity retry logic
- [x] Implement `scraper/hacker_news.py` — fetch top 30 HN stories
- [x] Implement `scraper/rss_feeds.py` — parse 5 RSS feeds with feedparser
- [x] Implement `scraper/reddit.py` — fetch top posts from 3 subreddits
- [x] Implement `scraper/github_trending.py` — scrape GitHub trending page
- [x] Implement `scraper/product_hunt.py` — fetch top PH launches (optional)
- [x] Test each scraper independently; print raw output to console

---

## Phase 2 — Filtering & Ranking

- [x] Implement `filter/config.py` — HIGH_SIGNAL_KEYWORDS and NOISE_KEYWORDS lists
- [x] Implement `filter/scorer.py` — full scoring formula (engagement + keyword + recency)
- [x] Implement `filter/deduplicator.py` — skip seen URLs/titles via SQLite
- [x] Wire scrapers + filter in `main.py` stub
- [x] Log top-5 selected items to console and verify quality

---

## Phase 3 — Content Generation + Image

- [x] Set up Gemini API key; implement `generator/llm_client.py`
- [x] Build prompt templates in `generator/prompts.py` (system + user prompt)
- [x] Implement `generator/generator.py` — `generate_post()` with retry & quality gate
- [x] Implement `formatter/formatter.py` — validate length, strip markdown, truncate
- [x] Test: pipe top-ranked item through generator → print formatted post
- [x] Download `Inter-Bold.ttf` and `Inter-Regular.ttf` into `utils/fonts/`
- [x] Implement `generator/card_generator.py` — Pillow branded 1200×627 fallback card
- [x] Implement `generator/image_generator.py` — Gemini Imagen 3 primary call
- [x] Implement `get_post_image()` orchestrator — try Imagen 3 → fallback Pillow
- [x] Test: generate image for sample topic; inspect output PNG at `data/post_image.png`

---

## Phase 4 — LinkedIn Automation

- [x] Implement `utils/auth.py` — first-time login (headful) + cookie save/load
- [x] Implement `poster/linkedin_poster.py` — Playwright with image upload + human timing
- [x] Implement `poster/draft_saver.py` — save failed posts to `data/drafts/`
- [x] Test: post dummy text-only post to LinkedIn
- [x] Test: post with image attached; verify image appears in preview
- [x] Implement failure recovery (retry × 2 → save draft on all fails)
- [x] Wire full pipeline end-to-end in `main.py`

---

## Phase 5 — Optimization & Deployment

- [x] Set up `utils/logger.py` with Loguru (rotation + retention)
- [/] Add logging throughout all modules (scrape, filter, generate, post)
- [ ] Add Slack/email webhook alert on posting failure
- [x] Set up `.github/workflows/daily_post.yml` — cron at 9:00 AM & 6:00 PM IST
- [x] Add GitHub Actions secrets: `GROQ_API_KEY`, `UNSPLASH_ACCESS_KEY`, `LINKEDIN_COOKIES_B64`
- [x] Fix post typing (missing first chars) — switch to `insert_text`
- [x] Fix image relevance — extract og:image from source article URL
- [x] Run 3 full dry-runs end-to-end; validate output quality
- [x] Fix Playwright GitHub Action ubuntu-latest error (via Copilot apt-get fix)
- [x] Deploy and monitor for 1 week

---

## Phase 6 — Network Automation

- [x] Implement `poster/linkedin_networker.py` to navigate to My Network
- [x] Safe logic to find "Connect" buttons and loop (MAX_CONNECTIONS_PER_RUN = 5)
- [x] Handle "Add a note" / "Send without a note" modals
- [x] Wire `send_connection_requests` into `main.py`
- [x] Test with headful dry run

---

## Phase 7 — Infrastructure Stabilization

- [/] Pin GitHub runner to `ubuntu-22.04` for OS stability
- [/] Use `playwright install-deps` for robust dependency management
- [ ] Verify successful scheduled run

---

## Review

### Phase 1 Review
- Status: ✅ Verified live — all 5 scrapers working (HN 29 stories, RSS 50 items, Reddit, GitHub, ProductHunt)
- Notes: Full run completed successfully on 2026-03-18.

### Phase 2 Review
- Status: ✅ Verified live — scoring + dedup working, SQLite recording items correctly.

### Phase 3 Review
- Status: ✅ Verified live — Groq llama-3.3-70b-versatile generated 670-1062 char posts. Pillow card fallback working (Imagen 3 not configured).

### Phase 4 Review
- Status: ✅ Verified live — Post submitted via `button[aria-label="Post"]` with disabled-attribute polling. Post visible on LinkedIn on 2026-03-18.
- Notes: Fixed dropped first characters (switching to `insert_text`). Fixed image mismatch (adding og:image extraction as priority).

### Phase 5 Review
- Status: ✅ Deployed — Cron schedule updated to 9 AM and 6 PM IST. GitHub Actions workflow configured with correct secrets. Code is ready to be pushed to main.
- Next: the agent will post completely autonomously on GitHub.
