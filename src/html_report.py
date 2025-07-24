import json
import os

def generate_html(yt_videos, ig_videos, tk_videos):
    # Ignoramos ig_videos (Instagram no se usa)
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viral Daily</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Google AdSense Auto Ads Code - Replace with your client ID -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-your-adsense-id" crossorigin="anonymous"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .platform {
            margin: 20px 0;
        }
        .platform h2 {
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 5px;
        }
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        .video {
            background: white;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .video img {
            max-width: 100%;
            border-radius: 5px;
        }
        .video a {
            text-decoration: none;
            color: #0066cc;
            font-weight: bold;
            display: block;
            margin: 10px 0;
        }
        .video a:hover {
            color: #003366;
        }
        .affiliate-link {
            font-size: 0.8em;
            color: #888;
            margin-top: 5px;
        }
        .subscription-button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
        }
        .filter {
            text-align: center;
            margin: 20px 0;
        }
        .filter button {
            padding: 10px 20px;
            margin: 0 5px;
            border: none;
            border-radius: 5px;
            background-color: #0066cc;
            color: white;
            cursor: pointer;
        }
        .filter button:hover {
            background-color: #003366;
        }
        .filter button.active {
            background-color: #003366;
        }
        #video-chart {
            max-width: 600px;
            margin: 20px auto;
        }
        .search {
            text-align: center;
            margin: 10px 0;
        }
        .search input {
            padding: 10px;
            width: 300px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        .ad-container {
            text-align: center;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>Viral Daily</h1>

    <div class="subscription-button" onclick="subscribe()">Subscribe for Premium (Ad-Free)</div>

    <div class="search">
        <input type="text" id="search-input" placeholder="Buscar videos...">
    </div>

    <div class="filter">
        <button class="platform-filter active" data-platform="all">Todos</button>
        <button class="platform-filter" data-platform="youtube">YouTube</button>
        <button class="platform-filter" data-platform="tiktok">TikTok</button>
    </div>

    <div class="ad-container">
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-your-adsense-id"
             data-ad-slot="your-ad-unit-id"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
    </div>

    <canvas id="video-chart"></canvas>

    <section class="platform" id="youtube">
        <h2>🎥 YouTube</h2>
        <div class="video-grid" id="youtube-videos">
            {}
        </div>
    </section>

    <section class="platform" id="tiktok">
        <h2>🎵 TikTok</h2>
        <div class="video-grid" id="tiktok-videos">
            {}
        </div>
    </section>

    <script src="/script.js"></script>
</body>
</html>
"""

    # Cargar videos de TikTok desde videos.json
    tk_videos = []
    if os.path.exists("videos.json"):
        with open("videos.json", "r") as f:
            tk_videos = json.load(f)

    # Generar HTML para videos
    yt_html = "".join(f"""
        <div class="video" data-platform="youtube">
            <a href="{v}">{v}</a>
            <img src="https://via.placeholder.com/120" alt="Thumbnail">
            <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
        </div>
    """ for v in yt_videos)
    tk_html = "".join(f"""
        <div class="video" data-platform="tiktok">
            <a href="{v['url']}">{v['title']}</a>
            <img src="{v['thumb']}" alt="Thumbnail">
            <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
        </div>
    """ for v in tk_videos)

    html = html.format(yt_html, tk_html)

    # Guardar HTML
    with open("viral_daily.html", "w") as f:
        f.write(html)

    # Copiar a public/index.html para Netlify
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w") as f:
        f.write(html)

    print("✅ viral_daily.html generado y copiado a public/index.html")
