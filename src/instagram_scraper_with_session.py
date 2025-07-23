# src/instagram_scraper_with_session.py
# -*- coding: utf-8 -*-
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path("instagram_session.json")

# --- helpers --------------------------------------------------------------
LINK_RE = re.compile(r"/(?:reel|p)/[A-Za-z0-9_-]+/?")

def collect_links(page) -> list[str]:
    """Devuelve href absolutos únicos que parezcan posts/reels."""
    hrefs = page.eval_on_selector_all(
        "a[href]", "els => els.map(e => e.href)"
    )
    out = []
    seen = set()
    for h in hrefs:
        if LINK_RE.search(h) and h not in seen:
            seen.add(h)
            out.append(h.split("?")[0])
    return out


def fetch_instagram_reels_with_session(limit: int = 10) -> list[dict]:
    if not SESSION_FILE.exists():
        print("⚠️  Ejecuta primero instagram_login_and_save_session.py")
        return []

    cookies = json.load(SESSION_FILE.open())
    result = []

    with sync_playwright() as p:
        br = p.chromium.launch(headless=False)
        ctx = br.new_context()
        ctx.add_cookies(cookies)
        pg = ctx.new_page()

        pg.goto("https://www.instagram.com/explore/tags/viral/", timeout=60000)
        pg.wait_for_timeout(5000)  # carga inicial

        # ⬇ hace scroll 3 veces para forzar ‘lazy‑load’
        for _ in range(3):
            pg.mouse.wheel(0, 2000)
            pg.wait_for_timeout(3000)

        links = collect_links(pg)[:limit]

        for l in links:
            result.append(
                {
                    "url":   l,
                    "title": "Instagram post",
                    # mini‑icono por defecto; no necesitamos la miniatura real
                    "thumb": "https://www.svgrepo.com/show/506697/instagram.svg",
                }
            )

        br.close()
    return result


if __name__ == "__main__":
    print("📸 Probando scraper IG…")
    data = fetch_instagram_reels_with_session()
    print("Obtenidos", len(data), "posts")
    for i, d in enumerate(data, 1):
        print(f"{i}. {d['url']}")

