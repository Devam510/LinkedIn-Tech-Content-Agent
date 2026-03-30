# Lessons Learned

> Updated after every user correction. Each entry has: the mistake, the root cause, and the rule to prevent recurrence.

---

## Template

```
### [Short title of mistake]
- **Date**: YYYY-MM-DD
- **What happened**: Brief description of what went wrong.
- **Root cause**: Why it happened.
- **Rule**: The rule to follow next time to avoid this.
```

---

## Entries

<!-- Add new lessons below as they occur. Most recent first. -->

### GitHub Action git add failure due to .gitignore
- **Date**: 2026-03-30
- **What happened**: GitHub Actions job failed at the "Commit agent database" step because `data/agent.db` was listed in `.gitignore`.
- **Root cause**: `git add <file>` fails with an error if the file is tracked in `.gitignore`.
- **Rule**: Use `git add -f <path>` in GitHub Actions workflows when committing a generated/database file that is normally ignored in local development.

### Initial Setup
- **Date**: 2026-03-17
- **What happened**: N/A — baseline entry.
- **Root cause**: N/A
- **Rule**: Always read `tasks/lessons.md` at the start of each session before writing any code.

### Missing pip install after requirements.txt change
- **Date**: 2026-03-18
- **What happened**: Added `openai` to `requirements.txt` after initial `pip install`, so venv was missing the package. `main.py` crashed with `No module named 'openai'`.
- **Root cause**: `requirements.txt` was updated mid-session but `pip install -r requirements.txt` was not re-run.
- **Rule**: Whenever `requirements.txt` is modified, immediately run `venv\Scripts\pip install -r requirements.txt` before any test or run.

### Wrong Grok model name
- **Date**: 2026-03-18
- **What happened**: Used `grok-2-latest` as the model name — xAI API returned `Model not found`.
- **Root cause**: Assumed model name suffix without verifying against xAI's actual model list.
- **Rule**: Always verify exact model names from the provider's official docs before hardcoding. For xAI, use `grok-2` or `grok-3-mini`.

### Groq (groq.com) vs Grok (x.ai) confusion
- **Date**: 2026-03-18
- **What happened**: User's API key starting with `gsk_` is a Groq (groq.com) key, not xAI Grok. Initially used wrong base URL `api.x.ai/v1` causing auth failures.
- **Root cause**: "Groq" and "Grok" sound identical — two completely different services.
- **Rule**: `gsk_` prefix = Groq (groq.com, base_url=`api.groq.com/openai/v1`). `xai-` prefix = xAI Grok (api.x.ai/v1).

### Brittle Playwright selectors break on LinkedIn UI updates
- **Date**: 2026-03-18
- **What happened**: `page.get_by_text("Start a post")` timed out — LinkedIn changed their feed UI.
- **Root cause**: Single hard-coded selector with no fallback.
- **Rule**: Always use multiple selector fallbacks for LinkedIn automation. Try text → aria-label → placeholder → CSS class → data attribute in sequence.

### PowerShell does not support Linux env var syntax
- **Date**: 2026-03-18
- **What happened**: User tried `UNSPLASH_ACCESS_KEY=value` in PowerShell — failed with command not found.
- **Root cause**: Linux `KEY=value` syntax is invalid in PowerShell.
- **Rule**: Never instruct user to set env vars via terminal. Always tell them to edit the `.env` file directly. PowerShell syntax would be `$env:KEY = "value"` but `.env` file is simpler and persists.

### Textbox selector changes after image upload in LinkedIn
- **Date**: 2026-03-18
- **What happened**: Textbox found and clicked when no image uploaded, but "all selectors failed" after image upload.
- **Root cause**: LinkedIn renders a different post composer modal when media is attached — different aria-labels and DOM structure.
- **Rule**: Always add screenshot-on-failure in Playwright scripts. Add explicit wait (`page.wait_for_timeout(3000)`) after any modal-triggering action before searching for elements.

### Playwright uses "Enter" not "Return" for keyboard key names
- **Date**: 2026-03-18
- **What happened**: `page.keyboard.press("Control+Return")` threw `Unknown key: "Return"`.
- **Root cause**: Playwright follows browser keyboard event naming — uses `"Enter"` not `"Return"`.
- **Rule**: In Playwright, always use `"Enter"` not `"Return"`. Full shortcut: `page.keyboard.press("Control+Enter")`.

### Ctrl+Enter in LinkedIn contenteditable inserts a newline, not submit
- **Date**: 2026-03-18
- **What happened**: `page.keyboard.press("Control+Enter")` was pressed but the post was never submitted — it only added a blank line in the textbox.
- **Root cause**: LinkedIn's rich-text editor (Quill/contenteditable) intercepts Ctrl+Enter to insert a line break, not to submit.
- **Rule**: Never use keyboard shortcuts to submit LinkedIn posts. Always find and click the actual "Post" button using `page.get_by_role("button", name="Post", exact=True)` or `button[aria-label="Post"]`.

### div[role="dialog"] matches LinkedIn's video player, not the post composer
- **Date**: 2026-03-18
- **What happened**: `is_modal_open()` checked `page.locator('div[role="dialog"]').count() > 0` — always returned True even after post was done.
- **Root cause**: LinkedIn's embedded video player also uses `div[role="dialog"]`, so the count never drops to 0.
- **Rule**: Never use `div[role="dialog"]` to detect the post composer. Instead, check if the composer element (`.share-box-v2`, `.share-creation-state__main`) is still visible, OR wait for the "Your post was sent" toast notification.

### Post button disabled attribute must be polled before clicking
- **Date**: 2026-03-18
- **What happened**: Post button was visible but clicking it silently did nothing — it was still `disabled` while LinkedIn processed the uploaded image.
- **Root cause**: LinkedIn disables the button during image upload processing and re-enables it asynchronously.
- **Rule**: After uploading an image, poll `element.get_attribute("disabled")` until it returns `None` before clicking the Post button. Allow up to 10 seconds.

### Character-by-character typing drops first chars in Quill editors
- **Date**: 2026-03-18
- **What happened**: First try: The first 2-4 chars were missing. Second try (`insert_text`): Text was completely missing from the final published post.
- **Root cause**: LinkedIn's Quill/React editor initialises event listeners slightly after the click. If we type immediately, chars are lost. But if we use `insert_text`, it bypasses React's `onChange`/keyboard events entirely, causing the form submission payload to be empty.
- **Rule**: Never use `insert_text` for React-based rich-text editors. Wait 2 seconds (`page.wait_for_timeout(2000)`) after clicking the text box to let it initialize, THEN use `page.keyboard.type(post_text, delay=10)` to simulate real user keystrokes so React registers the content.

### Use og:image from source article for relevant images
- **Date**: 2026-03-18
- **What happened**: Unsplash returned a car photo for a GPT-5.4 article.
- **Root cause**: Unsplash keyword search is hit-or-miss for niche tech topics.
- **Rule**: Always try to fetch `og:image` or `twitter:image` from the article's URL first using `BeautifulSoup`. This is the exact image the author chose and is always relevant. Only fall back to Imagen 3 / Unsplash / Pillow if og:image is missing.

### Free APIs like Pollinations.ai can return 429 or 500
- **Date**: 2026-03-18
- **What happened**: Tested Pollinations.ai generation and received HTTP 500 / 429.
- **Root cause**: Free open-access APIs get rate-limited or overloaded easily during peak hours.
- **Rule**: Always wrap free image API calls in `try...except` block, catch `requests.exceptions.RequestException`, and gracefully fall back to the next reliable source (like `og:image` or `Unsplash`) so the entire posting script doesn't crash.

### Workflow Failure: Moving Target "Latest" OS
- **Date**: 2026-03-19
- **What happened**: GitHub Actions failed with `libasound2` missing after GitHub upgraded `ubuntu-latest` to 24.04 (Noble).
- **Root cause**: Ubuntu 24.04 renamed the package to `libasound2t64`, breaking Playwright versions that hard-coded the old name.
- **Root Cause Solution**: Never use `ubuntu-latest` for production automation. Always pin the runner to a specific, stable OS version (e.g., `ubuntu-22.04`) to prevent background OS upgrades from breaking dependencies.
- **Rule**: Pin GitHub runners to verified versions (`ubuntu-22.04`) and use `playwright install-deps` explicitly for robust setup.

### openai SDK 'proxies' error on fresh installs
- **Date**: 2026-03-20
- **What happened**: GitHub Actions run "succeeded" but no post appeared on LinkedIn. Logs showed `Client.__init__() got an unexpected keyword argument 'proxies'` from the Groq/OpenAI client.
- **Root cause**: `openai==1.30.0` passes a `proxies` kwarg to `httpx.Client`. When GitHub installs fresh packages, it pulls `httpx>=0.28.0` which removed the `proxies` argument, causing a crash before any post could be generated.
- **Rule**: Always pin `httpx` explicitly in `requirements.txt`. Use `httpx>=0.27.0,<0.28.0` to prevent a transitive dependency from breaking the OpenAI SDK. Or upgrade `openai>=1.52.0` which removed the proxies usage internally.
