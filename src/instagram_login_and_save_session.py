import json,os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
load_dotenv(Path(__file__).resolve().parent.parent/".env")
def save_instagram_session():
    u=os.getenv("INSTAGRAM_USERNAME"); p=os.getenv("INSTAGRAM_PASSWORD")
    if not u or not p: print("❌ Falta INSTAGRAM_USERNAME/PASSWORD"); return
    with sync_playwright() as pw:
        br=pw.chromium.launch(headless=False); ctx=br.new_context(); pg=ctx.new_page()
        pg.goto("https://www.instagram.com/accounts/login/"); pg.wait_for_selector("input[name='username']")
        pg.fill("input[name='username']",u); pg.fill("input[name='password']",p); pg.click("button[type='submit']")
        pg.wait_for_timeout(10000)
        json.dump(ctx.cookies(),open("instagram_session.json","w"))
        print("✅ Sesión guardada"); br.close()
if __name__=="__main__": save_instagram_session()
