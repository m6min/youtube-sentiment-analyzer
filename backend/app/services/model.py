import pandas as pd
from starlette.concurrency import run_in_threadpool

from app.services.sentiment import SentimentAnalyzer


async def analyze_comments(comments: list[dict], model: SentimentAnalyzer) -> float:
    return await run_in_threadpool(model.negative_percentage, comments)


def analyze_title(title: str, pipeline) -> float:
    """Generates a clickbait probability using local_model which loaded with lifespan"""
    exclamation_count = title.count('!')
    letters = [i for i in title if i.isalpha()]
    uppercase_ratio = 0.0
    if len(letters) > 0:
        uppercase_ratio = round(sum(1 for i in letters if i.isupper()) / len(letters), 2)
    data = pd.DataFrame({
        'title': [title],
        'exclamation_count': [exclamation_count],
        'uppercase_ratio': [uppercase_ratio]
    })
    proba = pipeline.predict_proba(data)[0][1]
    return round(proba * 100, 2)
