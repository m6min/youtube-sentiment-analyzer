from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

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