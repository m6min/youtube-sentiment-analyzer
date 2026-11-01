import logging
import os

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = (
    "https://router.huggingface.co/hf-inference/models/"
    "savasy/bert-base-turkish-sentiment-cased"
)

async def analyze_comments(comments: list[dict]) -> float:
    """Generates an average negative score for comments on video using HuggingFace Api"""
    truncated_comments = [
        comment["text"][:512]
        for comment in comments
    ]
    if not truncated_comments:
        return 0.0
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": truncated_comments}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        results = response.json()

        negative_count = 0
        analyzed_count = 0

        for res in results:
            prediction = res[0] if isinstance(res, list) and res else res

            if not isinstance(prediction, dict):
                continue

            label = prediction.get("label", "").lower()

            if label not in {"negative", "positive"}:
                continue

            analyzed_count += 1

            if label == "negative":
                negative_count += 1

        if analyzed_count == 0:
            return 0.0

        ratio = (negative_count / analyzed_count) * 100

        return round(ratio, 2)

    except Exception as err:
        logger.exception("HuggingFace API error: %s", str(err))
        raise

def analyze_title(title: str, pipeline) -> int:
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
