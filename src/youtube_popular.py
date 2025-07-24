# src/youtube_popular.py
import requests
import os

def fetch_youtube_popular():
    try:
        response = requests.get(
            'https://www.googleapis.com/youtube/v3/videos',
            params={
                'part': 'snippet',
                'chart': 'mostPopular',
                'maxResults': 10,
                'key': os.getenv('YOUTUBE_API_KEY')
            }
        )
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'title': item['snippet']['title'],
                    'thumb': item['snippet']['thumbnails']['medium']['url']
                } for item in data.get('items', [])
            ]
        else:
            print(f"Failed to fetch YouTube videos: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        return []

if __name__ == "__main__":
    videos = fetch_youtube_popular()
    print(videos)
