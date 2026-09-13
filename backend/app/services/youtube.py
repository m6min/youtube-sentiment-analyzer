import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.utils.text_cleaning import clean_text

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
        "channel_id": snippet["channelId"],
        "view_count": statistics.get("viewCount", "0"),
        "like_count": statistics.get("likeCount", "0"),
        "comment_count": statistics.get("commentCount", "0")
    }

async def get_video_comments(video_id: str, channel_owner_id: str, max_pages: int = 5) -> list:
    """Gets [max_results] comments, checks if its written by channel or not and returns comments

    Args:
        video_id (str):
        channel_owner_id (str):
        max_pages (int, optional): Defaults to 5

    Raises:
        HTTPException

    Returns:
        list
    """
    COMMENTS_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    next_page_token = None
    pages_fetched = 0
    async with httpx.AsyncClient() as client:
        while pages_fetched < max_pages:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "key": settings.YOUTUBE_API_KEY,
                "maxResults": 100,
                "textFormat": "plainText"
            }
            if next_page_token:
                params["pageToken"] = next_page_token
            response = await client.get(COMMENTS_API_URL, params=params)
            data = response.json()
            if response.status_code != 200:
                    error_reason = data.get("error", {}).get("errors", [{}])[0].get("reason")
                    if error_reason == "commentsDisabled":
                        return []
                    raise HTTPException(detail="There was an error while trying to get comments. Please try again.", status_code=response.status_code)
            if "items" in data:
                    for item in data["items"]:
                        comment_id = item["id"]
                        comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
                        # If comment written by channel owner we will skip it
                        comment_author_id = comment_snippet.get("authorChannelId", {}).get("value", "")
                        if comment_author_id == channel_owner_id:
                            continue
                        clean_comment = clean_text(comment_snippet["textDisplay"])
                        comments.append({
                            "comment_id": comment_id,
                            "author": comment_snippet["authorDisplayName"],
                            "text": clean_comment,
                            "like_count": comment_snippet["likeCount"],
                            "published_at": comment_snippet["publishedAt"]
                        })
            next_page_token = data.get("pageToken")
            pages_fetched += 1
            if not next_page_token:
                break
    return comments