import logging
from datetime import datetime, timedelta, timezone

from app.crud.crud_comment import create_comments, delete_comms_by_video
from app.crud.crud_video import create_video, get_video, get_weekly_rankings
from app.db.session import get_db
from app.limiter import limiter
from app.services.model import analyze_comments
from app.services.youtube import get_video_comments, get_video_details
from app.utils.extract_video_id import extract_video_id
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .request import AnalyzeRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health():
    return {"live": True}

@router.post("/analyze")
@limiter.limit("5/minute")
async def analyze(request: Request, payload: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    url = str(payload.video_url)
    video_id = extract_video_id(url)
    logger.info("New analyze requested. Video id: %s", video_id)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid video url")
    db_video = await get_video(db, video_id)
    if db_video and db_video.is_analyzed:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        ten_days_ago = now - timedelta(days=10)
        if db_video.created_at > ten_days_ago:
            logging.info("Video has found on cache, returning with id: %s", video_id)
            return {
                "status": "success",
                "source": "database",
                "video_info": {
                    "id": db_video.id,
                    "title": db_video.title
                },
                "analyze_results":{
                    "clickbait_score": db_video.clickbait_score,
                    "overall_sentiment": db_video.overall_sentiment
                }
                }

    video_data = await get_video_details(video_id)
    owner_id = video_data["channel_id"]
    comments_data = await get_video_comments(video_id, owner_id)

    if not comments_data:
        logger.warning("No comment found for this video: %s", video_id)
        nlp_results = {"clickbait_score": 0.0, "overall_sentiment": "undefined"}
    else:
        logger.info("Model is working.. %s comment will be analyzed", len(comments_data))
        nlp_results = await analyze_comments(comments_data)
        logger.info("Analyze is over, clickbait score: %s", nlp_results["clickbait_score"])

    # IF VIDEO EXISTS IN DB BUT HAVE NOT ANALYZED
    if db_video:
        db_video.is_analyzed = True
        db_video.clickbait_score = nlp_results["clickbait_score"]
        db_video.overall_sentiment = nlp_results["overall_sentiment"]
        db_video.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        if comments_data:
            await delete_comms_by_video(db, video_id)
            await create_comments(db, video_id, comments_data)
    else:
    # WE DONT HAVE VIDEO ON DB
        video_data["is_analyzed"] = True
        video_data["clickbait_score"] = nlp_results["clickbait_score"]
        video_data["overall_sentiment"] = nlp_results["overall_sentiment"]
        video_data["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
        await create_video(db, video_data)


        if comments_data:
            await create_comments(db, video_id, comments_data)


    return {
        "status": "success",
        "source": "youtube_api_and_nlp",
        "video_info": video_data,
        "comments_count_retrieved": len(comments_data),
        "message": "Video has been analyzed and saved into database",
        "comments": comments_data,
        "analyze_results":{
                            "clickbait_score": nlp_results["clickbait_score"],
                            "overall_sentiment": nlp_results["overall_sentiment"]
                        }
    }

@router.get("/rankings")
@limiter.limit("30/minute")
async def get_rankings(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        results = await get_weekly_rankings(db)
        if not results:
            return {
                "status": "success",
                "message": "There is no analyzed video for this week yet.",
                "rankings": []
            }
        formatted_videos = []
        for res in results:
            formatted_videos.append({
                "video_id": res.id,
                "title": res.title,
                "clickbait_score": res.clickbait_score,
                "thumbnail_url": f"https://img.youtube.com/vi/{res.id}/hqdefault.jpg",
            })
        return {
            "status": "success",
            "message": "Top 5 video has been fetched from database.",
            "rankings": formatted_videos
        }
    except Exception as e:
        logger.warning("An error occurred on rankings endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail=f"There is an error occurred while getting rankings: {str(e)}")
