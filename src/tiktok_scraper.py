# src/tiktok_scraper.py
import requests
import os

def fetch_tiktok_videos():
    try:
        response = requests.get(
            'https://open.tiktokapis.com/v2/video/list/?fields=id,desc,cover_image_url',
            headers={'Authorization': f'Bearer {os.getenv("TIKTOK_ACCESS_TOKEN")}'}
        )
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    'url': f"https://www.tiktok.com/@user/video/{video['id']}",
                    'title': video['desc'] or 'TikTok video',
                    'thumb': video['cover_image_url']
                } for video in data.get('data', {}).get('videos', [])
            ]
        else:
            print(f"Failed to fetch TikTok videos: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching TikTok videos: {e}")
        return []

if __name__ == "__main__":
    videos = fetch_tiktok_videos()
    print(videos)
