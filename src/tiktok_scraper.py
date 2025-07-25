import requests
import os

def fetch_tiktok_trending():
    url = "https://open.tiktokapis.com/v2/video/query/"
    params = {
        'fields': 'id,title,cover_image_url'
    }
    headers = {
        'Authorization': f'Bearer {os.getenv("TIKTOK_ACCESS_TOKEN")}'
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch TikTok videos: {response.status_code} - {response.text}")
        return []
    data = response.json()
    videos = []
    for video in data.get('data', {}).get('videos', []):
        title = video.get('title', 'TikTok video')
        url = f"https://www.tiktok.com/@user/video/{video['id']}"
        thumb = video.get('cover_image_url', 'https://via.placeholder.com/120')
        videos.append({'title': title, 'url': url, 'thumb': thumb})
    return videos

if __name__ == "__main__":
    videos = fetch_tiktok_trending()
    print(videos)
