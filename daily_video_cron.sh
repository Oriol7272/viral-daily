#!/bin/bash
source ~/viral-daily/viral-env/bin/activate
echo "⏰ Ejecutando rutina diaria..."
python3 src/youtube_popular.py
python3 src/tiktok_scraper.py
python3 src/main.py
python3 fetch_videos.py
python3 src/html_report.py
mkdir -p public
mv videos.json public/videos.json
./deploy_to_netlify.sh
deactivate
