"""
poster/linkedin_networker.py — Automated safe connection requests.

Navigates to the "My Network" page and sends 3-5 connection requests
to "Suggested" people to grow the network organically without triggering bans.
Handles the "You can customize this invitation" modals safely.
"""
import random
import time
from playwright.sync_api import Page
from utils.logger import log

CONNECTION_NOTES = [
    "Hi! I built an AI agent that posts daily tech news and safely manages my network autonomously. It found your profile—would love to connect!",
    "Hey! I'm growing my network using a custom AI agent I built from scratch (it's actually sending you this request right now). Let's connect and talk tech!",
    "Hi there! Fun fact: my autonomous AI agent sent you this request! I built it to post tech news and grow my network. Would love to connect with a fellow builder.",
    "Hey! I wrote an AI script to automate my LinkedIn presence, and it recommended your profile! Let's connect and share what we're working on.",
    "Hi! Trying out a new AI agent I created to manage my LinkedIn autonomously. It thought we should connect, and I agree! Hope you're having a great week."
]

# CRITICAL SAFETY LIMIT
# LinkedIn allows ~100 requests per week. We run twice a day (14 runs/week).
# 5 * 14 = 70 requests/week. Safe range.
MAX_CONNECTIONS_PER_RUN = 5


def _human_delay(min_sec: float = 2.0, max_sec: float = 6.0) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def send_connection_requests(page: Page) -> int:
    """
    Go to My Network, find people to connect with, and send safe amount of requests.
    Returns the number of successful connection requests sent.
    """
    log.info("[Networker] Navigating to My Network …")
    page.goto("https://www.linkedin.com/mynetwork/", wait_until="domcontentloaded")
    
    # Wait for the suggestions to load
    try:
        page.wait_for_selector('button:has-text("Connect")', timeout=10000)
    except Exception:
        log.warning("[Networker] No 'Connect' buttons found on My Network. Skipping connections.")
        return 0

    _human_delay(3, 5)

    # Locate all 'Connect' buttons on the page
    # Using exact text to avoid clicking generic "Follow" or "Join" buttons
    connect_buttons = page.locator('button:has-text("Connect")').all()
    
    # In extremely rare cases where 'Connect' spans inside an inner span
    if not connect_buttons:
        connect_buttons = page.locator('button[aria-label^="Invite"]').all()

    total_found = len(connect_buttons)
    log.info(f"[Networker] Found {total_found} 'Connect' buttons.")
    
    if total_found == 0:
        return 0

    # Pick a random number to connect with this session (between 3 and MAX)
    target_count = random.randint(3, MAX_CONNECTIONS_PER_RUN)
    actual_sent = 0
    
    for i, button in enumerate(connect_buttons):
        if actual_sent >= target_count:
            break
            
        try:
            # Scroll button into view to act human
            button.scroll_into_view_if_needed()
            _human_delay(1, 3)
            
            button.click()
            log.info(f"[Networker] Clicked 'Connect' for profile #{i+1} …")
            _human_delay(1.5, 3.0)

            # --- Modal Handling ---
            # LinkedIn sometimes asks "You can customize this invitation" or 
            # "How do you know this person?"
            
            # Case 1: "Add a note" button exists (The standard customization modal)
            add_note_btn = page.get_by_role("button", name="Add a note")
            if add_note_btn.count() > 0 and add_note_btn.first.is_visible():
                add_note_btn.first.click()
                log.info("[Networker] Clicked 'Add a note'.")
                _human_delay(1, 2)
                
                # Type the custom message
                textarea = page.locator('textarea[name="message"], #custom-message').first
                if textarea.is_visible():
                    selected_note = random.choice(CONNECTION_NOTES)
                    textarea.fill(selected_note)
                    _human_delay(1, 2)

                    
                    # Click the modal's Send button
                    page.locator('button[aria-label="Send now"], button:has-text("Send")').last.click()
                    log.info("[Networker] Sent request WITH custom note.")
                    actual_sent += 1
                    _human_delay(2, 4)
                    continue

            # Fallback: "Send without a note" button exists (if Add a note failed)
            send_without_note = page.get_by_role("button", name="Send without a note")
            if send_without_note.count() > 0 and send_without_note.is_visible():
                send_without_note.click()
                log.info("[Networker] Clicked 'Send without a note'.")
                actual_sent += 1
                _human_delay(2, 4)
                continue
                
            # Case 2: Ordinary "Send" button exists (customization modal)
            send_btn = page.locator('button[aria-label="Send now"], button:has-text("Send")').filter(has_text="Send")
            if send_btn.count() > 0 and send_btn.first.is_visible():
                # They might ask for an email. If there's an email input, cancel.
                if page.locator('input[type="email"]').count() > 0:
                    log.warning("[Networker] Wants email verification. Canceling request.")
                    page.locator('button[aria-label="Dismiss"]').click()
                    continue
                
                send_btn.first.click()
                log.info("[Networker] Clicked 'Send' on modal.")
                actual_sent += 1
                _human_delay(2, 4)
                continue
            
            # Case 3: No modal appeared, the button just changed to "Pending"
            # This happens for easy 2nd/3rd degree connections
            actual_sent += 1
            log.info("[Networker] Request sent instantly (no modal).")
            _human_delay(2, 4)
            
        except Exception as e:
            log.warning(f"[Networker] Failed to process a connect button: {e}")
            # Try to close any stuck modal
            try:
                page.locator('button[aria-label="Dismiss"]').click()
            except:
                pass

    log.info(f"[Networker] Finished connecting. Sent {actual_sent} total requests this run.")
    return actual_sent
