#!/bin/bash
source ~/viral-daily/viral-env/bin/activate
echo "⏰ Ejecutando rutina diaria..."
python3 fetch_videos.py
./deploy_to_netlify.sh
deactivate
