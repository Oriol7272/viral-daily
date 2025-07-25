import json
import os

def generate_html(yt_videos, ig_videos, tk_videos):
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viral Daily</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-your-adsense-id" crossorigin="anonymous"></script>
    <link rel="manifest" href="/manifest.json">
    <style>
        .video-card { margin-bottom: 20px; }
        .hero-section { background: linear-gradient(135deg, #0066cc, #69C9D0); color: white; padding: 50px 0; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Viral Daily</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item"><a class="nav-link active" href="#">Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="#youtube">YouTube</a></li>
                    <li class="nav-item"><a class="nav-link" href="#tiktok">TikTok</a></li>
                    <li class="nav-item"><a class="nav-link" href="#instagram">Instagram</a></li>
                    <li class="nav-item"><a class="nav-link" href="#x">X</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container my-5 hero-section text-center">
        <h1>Welcome to Viral Daily</h1>
        <p class="lead">Discover the most viral videos from YouTube, TikTok, Instagram, and X.</p>
        <button class="btn btn-primary subscription-button">Subscribe for Premium (Ad-Free)</button>
    </div>

    <div class="container text-center">
        <input type="text" id="search-input" class="form-control" placeholder="Buscar videos..." style="max-width: 300px; margin: 10px auto;">
    </div>

    <div class="container text-center">
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-your-adsense-id"
             data-ad-slot="your-ad-unit-id"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
    </div>

    <div class="container">
        <canvas id="video-chart"></canvas>
    </div>

    <section class="container my-5" id="youtube">
        <h2>🎥 YouTube</h2>
        <div class="row">{}</div>
    </section>

    <section class="container my-5" id="tiktok">
        <h2>🎵 TikTok</h2>
        <div class="row">{}</div>
    </section>

    <section class="container my-5" id="instagram">
        <h2>📸 Instagram</h2>
        <div class="row">
            <div class="col-md-4">
                <div class="card video-card">
                    <img src="https://via.placeholder.com/250" class="card-img-top" alt="Instagram Viral">
                    <div class="card-body">
                        <h5 class="card-title">Viral Bhayani Post</h5>
                        <p class="card-text">153 likes, 15 comments - viralbhayani on July 24, 2025.</p>
                        <a href="https://www.instagram.com/reel/DMfiyDxTZS4/" class="btn btn-primary">View Post</a>
                        <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card video-card">
                    <img src="https://via.placeholder.com/250" class="card-img-top" alt="Instagram Viral">
                    <div class="card-body">
                        <h5 class="card-title">Viral Bhayani Post</h5>
                        <p class="card-text">631 likes, 20 comments - viralbhayani on July 24, 2025.</p>
                        <a href="https://www.instagram.com/reel/DMffAwwTGvg/" class="btn btn-primary">View Post</a>
                        <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="container my-5" id="x">
        <h2>🐦 X</h2>
        <div class="row">
            <div class="col-md-4">
                <div class="card video-card">
                    <img src="https://via.placeholder.com/250" class="card-img-top" alt="X Viral">
                    <div class="card-body">
                        <h5 class="card-title">OnlyFans model Woesenpai viral drama</h5>
                        <p class="card-text">OnlyFans model Woesenpai is going viral after her ex-boyfriend released videos accusing her of being abusive.</p>
                        <a href="https://x.com/FearedBuck/status/1948367738851762404" class="btn btn-primary">View Post</a>
                        <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card video-card">
                    <img src="https://via.placeholder.com/250" class="card-img-top" alt="X Viral">
                    <div class="card-body">
                        <h5 class="card-title">Funny video Mauro Icardi</h5>
                        <p class="card-text">Omg funny video Mauro Icardi on Twitter and Reddit famosos natasha.</p>
                        <a href="https://x.com/Takafumi1107/status/1948418505092558849" class="btn btn-primary">View Post</a>
                        <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <script src="/script.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
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
        <div class="col-md-4">
            <div class="card video-card">
                <img src="https://via.placeholder.com/250" class="card-img-top" alt="Thumbnail">
                <div class="card-body">
                    <h5 class="card-title">{v}</h5>
                    <a href="{v}" class="btn btn-primary">View Video</a>
                    <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                </div>
            </div>
        </div>
    """ for v in yt_videos)
    tk_html = "".join(f"""
        <div class="col-md-4">
            <div class="card video-card">
                <img src="{v['thumb']}" class="card-img-top" alt="Thumbnail">
                <div class="card-body">
                    <h5 class="card-title">{v['title']}</h5>
                    <a href="{v['url']}" class="btn btn-primary">View Video</a>
                    <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                </div>
            </div>
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
