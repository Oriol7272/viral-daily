#!/bin/bash
echo "🔄 Construyendo el sitio…"
cp viral_daily.html public/index.html
echo "🚀 Desplegando a Netlify…"
netlify deploy --prod --dir=public --message "📈 Auto-update $(date)"

