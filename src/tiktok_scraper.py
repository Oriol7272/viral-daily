from playwright.sync_api import sync_playwright
import time

def fetch_tiktok_trending(limit=10):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.tiktok.com/trending", timeout=60000)
        time.sleep(5)

        links = page.query_selector_all("a[href*='video']")
        for a in links:
            href = a.get_attribute("href")
            if href and href.startswith("https://www.tiktok.com/") and "/video/" in href:
                if href not in results:
                    results.append(href)
            if len(results) >= limit:
                break

        browser.close()
    return results

if __name__ == "__main__":
    print("🎵 Buscando vídeos virales en TikTok...")
    videos = fetch_tiktok_trending()
    for i, url in enumerate(videos, 1):
        print(f"{i}. {url}")

