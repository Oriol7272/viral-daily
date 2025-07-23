from googleapiclient.discovery import build
import os
API_KEY=os.getenv("YOUTUBE_API_KEY")
service=build("youtube","v3",developerKey=API_KEY)
def fetch_trending_videos(limit=10):
    res=service.videos().list(part="snippet",chart="mostPopular",regionCode="ES",maxResults=limit).execute()
    vids=[]
    for i in res["items"]:
        vids.append({"url":f"https://www.youtube.com/watch?v={i['id']}",
                     "title":i["snippet"]["title"],
                     "thumb":i["snippet"]["thumbnails"]["high"]["url"]})
    return vids
