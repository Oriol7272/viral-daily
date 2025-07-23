from playwright.sync_api import sync_playwright

def fetch_tiktok_trending():
    print("🎵 Accediendo a TikTok para buscar vídeos virales...")

    videos = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.tiktok.com/tag/viral", timeout=60000)

        page.wait_for_timeout(5000)

        links = page.eval_on_selector_all("a", "els => els.map(e => e.href)")
        seen = set()

        for link in links:
            if "/video/" in link and link not in seen:
                seen.add(link)
                videos.append(link)
            if len(videos) >= 10:
                break

        browser.close()

    return videos

