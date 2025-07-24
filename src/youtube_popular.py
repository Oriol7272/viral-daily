mport requests
from bs4 import BeautifulSoup
import json

def scrape_youtube_popular():
url = "https://www.youtube.com/feed/trending"
headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
response = requests.get(url, headers=headers)
if response.status_code != 200:
print("Failed to fetch YouTube trending page")
return []

soup = BeautifulSoup(response.text, 'html.parser')
videos = []
script_tags = soup.find_all('script')
for script in script_tags:
if 'var ytInitialData = ' in script.string:
data_str = script.string.split('var ytInitialData = ')[1].rstrip(';')
data = json.loads(data_str)
contents = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
for content in contents:
if 'videoRenderer' in content:
video = content['videoRenderer']
title = video['title']['runs'][0]['text']
url = "https://www.youtube.com/watch?v=" + video['videoId']
videos.append({'title': title, 'url': url})
break
return videos

if name == "main":
videos = scrape_youtube_popular()
print(videos)
