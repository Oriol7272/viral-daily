# src/main.py
from dotenv import load_dotenv
load_dotenv()                                 # ← carga las variables de .env

from youtube_popular import fetch_trending_videos
from instagram_scraper_with_session import fetch_instagram_reels_with_session
from tiktok_scraper import fetch_tiktok_trending
from html_report import build_html

from email.message import EmailMessage
import os, smtplib, ssl


def send_email(path: str) -> None:
    """Envía el HTML generado por correo usando SMTP (Gmail)."""
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    to   = os.getenv("EMAIL_TO")

    if not all([user, pwd, to]):
        print("ℹ️  Configura SMTP_USER, SMTP_PASS y EMAIL_TO en tu .env")
        return

    # Crea mensaje
    msg = EmailMessage()
    msg["Subject"] = "Viral Daily"
    msg["From"]    = user
    msg["To"]      = to

    with open(path, encoding="utf-8") as f:
        html = f.read()
    msg.add_alternative(html, subtype="html")

    # Envío seguro con SSL
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as smtp:
        smtp.login(user, pwd)
        smtp.send_message(msg)
        print("📧  Correo enviado a", to)

