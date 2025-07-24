#!/bin/bash

echo "🔄 Construyendo el sitio…"
mkdir -p dist
cp viral_daily.html dist/index.html

echo "🚀 Desplegando a Netlify…"
netlify deploy --dir=dist --prod

