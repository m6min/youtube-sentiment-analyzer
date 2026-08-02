import httpx
from fastapi import HTTPException
from app.core.config import settings

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"

async def get_video_details(video_id: str) -> dict:
    """Gets youtube video details for the given video id

    Args:
        video_id (str)
    """
    params = {
        "part": "snippet,statistics",
        "id": video_id,
        "key": settings.YOUTUBE_API_KEY
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(YOUTUBE_API_URL, params=params)
    data = response.json()
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, 
                            detail=data.get("error",{}).get("message","Youtube API Error"))
    if not data.get("items"):
        raise HTTPException(status_code=404, detail="Video not found")
    video_info = data["items"][0]
    snippet = video_info["snippet"]
    statistics = video_info["statistics"]
    return {
        "video_id": video_id,
        "title": snippet["title"],
        "channel_title": snippet["channelTitle"],
        "view_count": statistics.get("viewCount", "0"),
        "like_count": statistics.get("likeCount", "0"),
        "comment_count": statistics.get("commentCount", "0")
    }