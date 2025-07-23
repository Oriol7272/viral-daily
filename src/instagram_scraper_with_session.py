import json
import os
from playwright.sync_api import sync_playwright

def fetch_instagram_reels_with_session():
    print("📸 Accediendo a Instagram #viral con sesión guardada...")

    session_file = "instagram_session.json"
    if not os.path.exists(session_file):
        print("❌ No se encontró una sesión guardada de Instagram.")
        return []

    with open(session_file, "r") as f:
        cookies = json.load(f)

    reels = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Restaurar sesión
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto("https://www.instagram.com/explore/tags/viral/", timeout=60000)

        page.wait_for_timeout(5000)

        links = page.eval_on_selector_all("article a", "els => els.map(e => e.href)")
        for link in links:
            if "/reel/" in link or "/p/" in link:
                reels.append(link)

            if len(reels) >= 10:
                break

        browser.close()

    return reels

