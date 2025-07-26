#!/bin/bash
cd ~/Downloads/viral-daily
source ./viral-env/bin/activate
echo "⏰ Ejecutando rutina diaria..."
python src/main.py
./deploy_to_netlify.sh

