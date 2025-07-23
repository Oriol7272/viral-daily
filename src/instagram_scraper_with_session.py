"""
src/instagram_scraper_with_session.py
-------------------------------------
Devuelve hasta 10 posts del hashtag #viral (reels o fotos) usando la
sesión guardada en instagram_session.json.

Estrategia:
  • abre el hashtag, hace scroll, extrae enlaces únicos
  • visita cada enlace, espera al DOM, y toma:
        - título: meta og:title (si existe)
        - miniatura: meta og:image  ⟶ si falta, usa el primer <img>.src
"""

import json, os, re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

SESSION  = Path("instagram_session.json")
TAG_URL  = "https://www.instagram.com/explore/tags/viral/"
META_IMG = 'meta[property="og:image"]'
META_TIT = 'meta[property="og:title"]'


def fetch_instagram_reels_with_session(limit: int = 10) -> list[dict]:
    if not SESSION.exists():
        print("⚠️  Falta instagram_session.json — ejecuta el login primero")
        return []

    cookies = json.load(SESSION.open())
    posts: list[dict] = []

    with sync_playwright() as p:
        br = p.chromium.launch(headless=True, timeout=60000)
        ctx = br.new_context(); ctx.add_cookies(cookies)
        pg = ctx.new_page()

        # 1) Abre hashtag y scroll
        pg.goto(TAG_URL); pg.wait_for_timeout(6000)
        for _ in range(3):
            pg.mouse.wheel(0, 2500); pg.wait_for_timeout(2000)

        links = pg.eval_on_selector_all(
            'a[href*="/reel/"], a[href*="/p/"]',
            "els => [...new Set(els.map(e => e.href))]"
        )
        print("DEBUG IG links:", len(links))

        for url in links:
            if len(posts) >= limit:
                break
            if not re.search(r"/(reel|p)/", url):
                continue
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=10000)

                # título
                title = pg.get_attribute(META_TIT, "content") or "Instagram post"

                # miniatura: meta og:image o primer <img>
                thumb = pg.get_attribute(META_IMG, "content")
                if not thumb:
                    thumb = pg.eval_on_selector(
                        "article img",
                        "el => el?.src",
                    )

                if thumb:
                    posts.append({"url": url, "title": title, "thumb": thumb})
            except TimeoutError:
                continue

        br.close()
    return posts


# test manual
if __name__ == "__main__":
    print("📸 Probando scraper IG…")
    results = fetch_instagram_reels_with_session()
    print("Obtenidos", len(results), "posts")
    for i, post in enumerate(results, 1):
        print(f"{i}. {post['url']} — {post['title'][:60]}")

