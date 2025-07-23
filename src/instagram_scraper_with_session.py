import json,os
from playwright.sync_api import sync_playwright
def fetch_instagram_reels_with_session():
    if not os.path.exists("instagram_session.json"): return []
    cookies=json.load(open("instagram_session.json"))
    with sync_playwright() as pw:
        br=pw.chromium.launch(headless=True); ctx=br.new_context(); ctx.add_cookies(cookies)
        pg=ctx.new_page(); pg.goto("https://www.instagram.com/explore/tags/viral/"); pg.wait_for_timeout(5000)
        links=pg.eval_on_selector_all("article a","els=>els.map(e=>e.href)")
        out=[]; seen=set()
        for l in links:
            if ("/reel/" in l or "/p/" in l) and l not in seen:
                seen.add(l); out.append({"url":l,"title":"Post IG","thumb":"https://via.placeholder.com/120"})
                if len(out)>=10: break
        br.close(); return out
