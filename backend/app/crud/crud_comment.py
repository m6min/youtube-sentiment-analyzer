from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.db.models import Comment


async def create_comments(db: AsyncSession, video_id: str, comment_data: list) -> int:
    """Gets comments, transform them to db 'Comment' objects and
    saves into database
    
    Return: number of comments 
    """
    db_comment_objects = []
    for c in comment_data:
        new_comment = Comment(
            yt_comment_id = c["comment_id"],
            video_id = video_id,
            author = c["author"],
            text = c["text"],
            like_count = c["like_count"]
        )
        db_comment_objects.append(new_comment)
    db.add_all(db_comment_objects)
    await db.commit()
    return len(db_comment_objects)

async def delete_comms_by_video(db: AsyncSession, video_id: str):
    query = delete(Comment).where(Comment.video_id == video_id)
    await db.execute(query)
    await db.commit()