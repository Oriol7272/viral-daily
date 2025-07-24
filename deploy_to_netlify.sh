#!/bin/bash
echo "Desplegando a Netlify..."
npx netlify deploy --prod --dir=.#!/bin/bash
<<<<<<< HEAD
echo "Desplegando a Netlify..."
npx netlify deploy --prod --dir=.
=======

echo "🔄 Construyendo el sitio…"
mkdir -p dist
cp viral_daily.html dist/index.html

echo "🚀 Desplegando a Netlify…"
netlify deploy --dir=dist --prod

>>>>>>> 4485a23a0b10a0b15f5f72800dbd8b855307b6f8
