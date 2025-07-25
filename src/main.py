from TikTokApi import TikTokApi
import asyncio
import os
import json

ms_token = os.getenv("MS_TOKEN")

async def fetch_tiktok_viral(count=10):
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        videos = []
        async for video in api.trending.videos(count=count):
            videos.append({
                'title': video.as_dict.get('desc', 'TikTok video'),
                'url': f"https://www.tiktok.com/@{video.as_dict['author']['uniqueId']}/video/{video.as_dict['id']}",
                'thumb': video.as_dict.get('video', {}).get('cover', 'https://via.placeholder.com/120')
            })
        return videos

if __name__ == "__main__":
    videos = asyncio.run(fetch_tiktok_viral())
    print("10 videos más virales de TikTok:")
    for video in videos:
        print(f"Title: {video['title']}, URL: {video['url']}, Thumb: {video['thumb']}")
    with open('videos.json', 'w') as f:
        json.dump(videos, f, indent=2)
