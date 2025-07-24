# src/html_report.py

def generate_html(yt_videos, ig_videos, tk_videos):
    html = "<html><head><meta charset='utf-8'><title>Viral Daily</title></head><body>"
    html += "<h1>🎥 YouTube</h1>" + "".join(f"<p><a href='{v}'>{v}</a></p>" for v in yt_videos)
    html += "<h1>📸 Instagram</h1>" + "".join(f"<p><a href='{v}'>{v}</a></p>" for v in ig_videos)
    html += "<h1>🎵 TikTok</h1>" + "".join(f"<p><a href='{v}'>{v}</a></p>" for v in tk_videos)
    html += "</body></html>"

    with open("viral_daily.html", "w") as f:
        f.write(html)

    # También lo copiamos a public/index.html para Netlify
    import os
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w") as f:
        f.write(html)

    print("✅ viral_daily.html generado y copiado a public/index.html")

