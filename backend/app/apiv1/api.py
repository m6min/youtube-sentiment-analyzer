from fastapi import APIRouter
from app.services.youtube import get_video_details

router = APIRouter()

@router.get("/health")
async def health():
    return {"result": True}

@router.get("/analyze")
async def analyze(video_id: str):
    video_data = await get_video_details(video_id)
    return {"status": "success", "data": video_data}