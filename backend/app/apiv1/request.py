from pydantic import BaseModel, HttpUrl


class AnalyzeRequest(BaseModel):
    video_url: HttpUrl