from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime,timedelta,timezone
from app.db.models import Video


async def get_video(db: AsyncSession, video_id: str):
    """
    Query to find videos by video id, for caching
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    return result.scalars().first()

async def create_video(db: AsyncSession, video_data: dict):
    """Creates video object for table and saves it into the database
    """
    db_video = Video(
        id=video_data["video_id"],
        channel_id=video_data["channel_id"],
        title=video_data["title"]
    )
    db.add(db_video)
    await db.commit()
    return db_video

async def get_weekly_rankings(db: AsyncSession):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    query = (
        select(Video).where(
            Video.is_analyzed == True,
            Video.created_at >= seven_days_ago
        ).order_by(Video.clickbait_score.asc()).limit(5)
    )
    result = await db.execute(query)
    return result.scalars().all()
