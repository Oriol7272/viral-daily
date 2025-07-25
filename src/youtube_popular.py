import requests
import os

def fetch_youtube_popular():
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'part': 'snippet',
        'chart': 'mostPopular',
        'maxResults': 10,
        'key': os.getenv("YOUTUBE_API_KEY")
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch YouTube videos: {response.status_code} - {response.text}")
        return []
    data = response.json()
    videos = []
    for item in data.get('items', []):
        title = item['snippet']['title']
        url = f"https://www.youtube.com/watch?v={item['id']}"
        thumb = item['snippet']['thumbnails']['medium']['url']
        videos.append({'title': title, 'url': url, 'thumb': thumb})
    return videos

if __name__ == "__main__":
    videos = fetch_youtube_popular()
    print(videos)
