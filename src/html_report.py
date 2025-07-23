from jinja2 import Template
from datetime import datetime
HTML = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Viral Daily – {{date}}</title>
<style>body{font-family:sans-serif;margin:0;background:#fafafa}
h1{padding:12px;background:#111;color:#fff;margin:0}
section{padding:20px}.card{display:flex;align-items:center;margin:8px 0}
.card img{width:120px;height:68px;border-radius:8px;margin-right:12px;object-fit:cover}
a{text-decoration:none;color:#111;font-weight:600}small{color:#666;font-size:12px}</style>
</head><body><h1>🔥 Viral Daily — {{date}}</h1>
{% for n,items in data.items() %}<section><h2>{{n}}</h2>
{% for v in items %}<div class="card"><img src="{{v.thumb}}" alt="">
<div><a href="{{v.url}}" target="_blank">{{v.title}}</a><br><small>{{v.url}}</small></div></div>{% endfor %}
</section>{% endfor %}</body></html>"""
def build_html(report):
    html = Template(HTML).render(date=datetime.now().strftime("%Y-%m-%d"), data=report)
    with open("viral_daily.html","w",encoding="utf-8") as f: f.write(html)
    print("✅ viral_daily.html generado")
