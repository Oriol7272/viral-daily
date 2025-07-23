from youtube_popular import fetch_trending_videos
from instagram_scraper_with_session import fetch_instagram_reels_with_session
from tiktok_scraper import fetch_tiktok_trending
from html_report import build_html
from email.message import EmailMessage
import os, smtplib, ssl
def send_email(path):
    user=os.getenv("SMTP_USER"); pwd=os.getenv("SMTP_PASS"); to=os.getenv("EMAIL_TO")
    if not all([user,pwd,to]): print("ℹ️ Configura SMTP_USER, SMTP_PASS, EMAIL_TO"); return
    msg=EmailMessage(); msg["Subject"]="Viral Daily"; msg["From"]=user; msg["To"]=to
    msg.add_alternative(open(path).read(), subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context()) as s:
        s.login(user,pwd); s.send_message(msg)
        print("📧 Correo enviado a",to)
if __name__=="__main__":
    yt=fetch_trending_videos(); ig=fetch_instagram_reels_with_session(); tk=fetch_tiktok_trending()
    build_html({"YouTube":yt,"Instagram":ig,"TikTok":tk})
    send_email("viral_daily.html")
