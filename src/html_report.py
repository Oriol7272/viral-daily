def generate_html(youtube_videos, instagram_videos, tiktok_videos):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>📈 Vídeos Virales del Día</title>
    </head>
    <body>
        <h1>📺 YouTube</h1>
        <ul>{}</ul>
        <h1>🎵 TikTok</h1>
        <ul>{}</ul>
    </body>
    </html>
    """

    yt_block = "\n".join(f"<li><a href='{v['link']}'>{v['title']}</a></li>" for v in youtube_videos)
    tk_block = "\n".join(f"<li><a href='{v}'>{v}</a></li>" for v in tiktok_videos)

    final = html.format(yt_block, tk_block)

    with open("viral_daily.html", "w") as f:
        f.write(final)
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w") as f:
        f.write(final)

