import json
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

def save_instagram_session():
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        print("❌ Falta usuario o contraseña de Instagram en el archivo .env")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.instagram.com/accounts/login/", timeout=60000)

        page.wait_for_selector("input[name='username']")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        page.wait_for_timeout(10000)  # Espera a que inicie sesión

        cookies = context.cookies()
        with open("instagram_session.json", "w") as f:
            json.dump(cookies, f)

        print("✅ Sesión guardada en instagram_session.json")
        browser.close()

if __name__ == "__main__":
    save_instagram_session()

