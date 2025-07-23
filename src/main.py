from youtube_popular import fetch_trending_videos as fetch_youtube
from instagram_scraper_with_session import fetch_instagram_reels_with_session as fetch_instagram
from tiktok_scraper import fetch_tiktok_reels as fetch_tiktok

from datetime import datetime

def generar_html(videos):
    fecha = datetime.now().strftime("%Y-%m-%d")
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Viral Daily - {fecha}</title>
</head>
<body>
    <h1>🔥 Vídeos virales del día ({fecha})</h1>
"""
    for plataforma, links in videos.items():
        html += f"<h2>{plataforma}</h2>\n<ul>\n"
        for url in links:
            html += f'  <li><a href="{url}" target="_blank">{url}</a></li>\n'
        html += "</ul>\n"

    html += "</body>\n</html>"
    return html

if __name__ == "__main__":
    print("🚀 Recopilando vídeos virales...")

    print("📺 YouTube...")
    youtube_videos = fetch_youtube()

    print("📸 Instagram...")
    instagram_videos = fetch_instagram()

    print("🎵 TikTok...")
    tiktok_videos = fetch_tiktok()

    all_videos = {
        "YouTube": youtube_videos,
        "Instagram": instagram_videos,
        "TikTok": tiktok_videos
    }

    html_resultado = generar_html(all_videos)

    with open("viral_daily.html", "w", encoding="utf-8") as f:
        f.write(html_resultado)

    print("✅ HTML generado: viral_daily.html")

