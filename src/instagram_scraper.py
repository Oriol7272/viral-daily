from playwright.sync_api import sync_playwright
import time

def fetch_instagram_reels(hashtag="viral", limit=10):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = context.new_page()

        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        page.goto(url, timeout=60000)
        time.sleep(7)

        for _ in range(3):
            page.mouse.wheel(0, 1000)
            time.sleep(2)

        anchors = page.query_selector_all("a")
        for a in anchors:
            href = a.get_attribute("href")
            if href and ("/reel/" in href or "/p/" in href):
                full_url = "https://www.instagram.com" + href
                if full_url not in results:
                    results.append(full_url)
            if len(results) >= limit:
                break

        browser.close()
    return results

if __name__ == "__main__":
    print("📸 Buscando vídeos virales en Instagram...")
    reels = fetch_instagram_reels()
    for i, url in enumerate(reels, 1):
        print(f"{i}. {url}")
:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        page.goto(url, timeout=60000)
        page.wait_for_selector('article', timeout=10000)

        time.sleep(5)

        links = page.query_selector_all("article a")
        for link in links[:limit]:
            href = link.get_attribute("href")
            if "/reel/" in href or "/p/" in href:
                videos.append("https://www.instagram.com" + href)

        browser.close()
    return videos

if __name__ == "__main__":
    print("📸 Buscando vídeos virales en Instagram...")
    reels = fetch_instagram_reels()
    for i, url in enumerate(reels, 1):
        print(f"{i}. {url}")

