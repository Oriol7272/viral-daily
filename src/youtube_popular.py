import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Cargar clave API de entorno
load_dotenv()
api_key = os.getenv("YOUTUBE_API_KEY")

if not api_key:
    raise ValueError("API Key de YouTube no encontrada")

# Cliente de API
youtube = build("youtube", "v3", developerKey=api_key)

def get_top_videos(region="ES", max_results=10):
    request = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region,
        maxResults=max_results
    )
    return request.execute().get("items", [])

if __name__ == "__main__":
    print("⏳ Obteniendo vídeos virales de YouTube...")
    try:
        videos = get_top_videos()
        for i, v in enumerate(videos, 1):
            title = v['snippet']['title']
            likes = v['statistics'].get('likeCount', 'N/A')
            print(f"{i}. {title} (👍 {likes})")
    except Exception as e:
        print("❌ Error al obtener vídeos:", e)

