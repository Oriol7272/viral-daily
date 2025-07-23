from playwright.sync_api import sync_playwright
def fetch_tiktok_trending(limit=10):
    with sync_playwright() as pw:
        br=pw.chromium.launch(headless=True); pg=br.new_page()
        pg.goto("https://www.tiktok.com/tag/viral"); pg.wait_for_timeout(5000)
        links=pg.eval_on_selector_all("a","els=>els.map(e=>e.href)")
        out=[]; seen=set()
        for l in links:
            if "/video/" in l and l not in seen:
                seen.add(l); out.append({"url":l,"title":"TikTok Video","thumb":"https://via.placeholder.com/120"})
                if len(out)>=limit: break
        br.close(); return out
