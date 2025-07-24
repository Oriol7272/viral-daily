import requests
from bs4 import BeautifulSoup
import json

def scrape_tiktok_trending():
url = "https://www.tiktok.com/trending"
headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
response = requests.get(url, headers=headers)
if response.status_code != 200:
print("Failed to fetch TikTok trending page")
return []

soup = BeautifulSoup(response.text, 'html.parser')
videos = []
script_tags = soup.find_all('script', id='UNIVERSAL_DATA_FOR_REHYDRATION')
if script_tags:
data_str = script_tags[0].string
data = json.loads(data_str)
trending_videos = data['DEFAULT_SCOPE']['webapp.video-detail']['itemInfo']['itemStruct']['video']
Note: This is a placeholder; TikTok structure may vary. Adjust based on actual data.
For real scraping, use Selenium or API if available.

videos.append({'title': data['DEFAULT_SCOPE']['webapp.video-detail']['itemInfo']['itemStruct']['desc'], 'url': "https://www.tiktok.com/@user/video/" + trending_videos['id']})
return videos

if name == "main":
videos = scrape_tiktok_trending()
print(videos)
