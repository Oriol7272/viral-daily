from playwright.sync_api import sync_playwright, TimeoutError
from playwright_stealth import stealth_sync

def fetch_tiktok_trending(limit=10):
    out=[]
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context()
        pg  = ctx.new_page()
        stealth_sync(pg)                       # evita detección
        pg.goto("https://www.tiktok.com/tag/viral", timeout=60000)
        pg.wait_for_timeout(5000)
        links = pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
        seen=set()
        for l in links:
            if "/video/" in l and l not in seen:
                seen.add(l)
                out.append({
                    "url": l,
                    "title":"TikTok",
                    "thumb":"https://www.svgrepo.com/show/508906/tiktok.svg"
                })
                if len(out) >= limit: break
        br.close()
    return out

if __name__ == "__main__":
    print("🎵 Probando scraper TikTok…")
    vids = fetch_tiktok_trending()
    print("Obtenidos", len(vids), "vídeos")
    for i,v in enumerate(vids,1): print(i, v["url"])

