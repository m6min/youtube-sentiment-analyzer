from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime,timedelta, timezone
from app.crud.crud_comment import create_comments
from app.crud.crud_video import create_video, get_video
from app.db.session import get_db
from app.services.model import analyzer_service
from app.services.youtube import get_video_comments, get_video_details
from app.utils.extract_video_id import extract_video_id

from .request import AnalyzeRequest

router = APIRouter()

@router.get("/health")
async def health():
    return {"live": True}

@router.post("/analyze")
async def analyze(request: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    url = str(request.video_url)
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid video url")
    db_video = await get_video(db, video_id)
    if db_video and db_video.is_analyzed:
        now = datetime.now(timezone.utc)
        ten_days_ago = now - timedelta(days=10)
        if db_video.created_at > ten_days_ago:
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
        nlp_results = {"clickbait_score": 0.0, "overall_sentiment": "undefined"}
    else:
        nlp_results = analyzer_service.analyze_comments(comments_data)

    # IF VIDEO EXISTS IN DB BUT HAVE NOT ANALYZED
    if db_video:
        db_video.is_analyzed = True
        db_video.clickbait_score = nlp_results["clickbait_score"]
        db_video.overall_sentiment = nlp_results["overall_sentiment"]
        await db.commit()
    else:
    # WE DONT HAVE VIDEO ON DB
        video_data["is_analyzed"] = True
        video_data["clickbait_score"] = nlp_results["clickbait_score"]
        video_data["overall_sentiment"] = nlp_results["overall_sentiment"]
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
