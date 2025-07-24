#!/bin/bash
source ~/viral-daily/viral-env/bin/activate
echo "⏰ Ejecutando rutina diaria..."
python3 src/youtube_popular.py
python3 src/tiktok_scraper.py
python3 src/main.py  # Genera videos.json con videos virales de TikTok
python3 fetch_videos.py
python3 src/html_report.py  # Genera HTML con videos
mkdir -p public  # Crea carpeta pública
mv videos.json public/videos.json  # Mueve videos.json a public/
./deploy_to_netlify.sh
deactivate
