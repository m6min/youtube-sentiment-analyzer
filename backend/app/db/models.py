from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    channel_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    is_analyzed: Mapped[bool] = mapped_column(default=False)
    clickbait_score: Mapped[float] = mapped_column(nullable=True)
    # relevant, neutral or clickbait
    overall_sentiment: Mapped[str] = mapped_column(String, nullable=True)
    # one to many relationship
    comments: Mapped[list['Comment']] = relationship(back_populates="video", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    yt_comment_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"))
    author: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    video: Mapped["Video"] = relationship(back_populates="comments")
