from fastapi import APIRouter
from app.services.youtube import get_video_details, get_video_comments
router = APIRouter()

@router.get("/health")
async def health():
    return {"result": True}

@router.get("/analyze")
async def analyze(video_id: str):
    video_data = await get_video_details(video_id)
    owner_id = video_data["channel_id"]
    comments_data = await get_video_comments(video_id, owner_id)

    return {
        "status": "success", 
        "video_info": video_data,
        "comments_count_retrieved": len(comments_data),
        "comments": comments_data 
    }