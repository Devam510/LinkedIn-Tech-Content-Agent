from playwright.sync_api import sync_playwright
from utils.auth import load_session, save_session
from poster.linkedin_networker import send_connection_requests
import logging

logging.basicConfig(level=logging.INFO)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
    )

    if not load_session(ctx):
        print("No session!")
        browser.close()
        exit(1)

    page = ctx.new_page()
    print("Sending connection requests...")
    count = send_connection_requests(page)
    print(f"Total sent: {count}")
    
    save_session(ctx)
    browser.close()
