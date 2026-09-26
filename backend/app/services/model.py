import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = (
    "https://router.huggingface.co/hf-inference/models/"
    "savasy/bert-base-turkish-sentiment-cased"
)

async def analyze_comments(comments: list[dict]) -> dict:
    truncated_comments = [
        comment["text"][:512]
        for comment in comments
    ]
    if not truncated_comments:
        return {
            "clickbait_score": 0.0,
            "overall_sentiment": "undefined"
        }
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
                return {
                    "clickbait_score": 0.0,
                    "overall_sentiment": "undefined"
                }

        clickbait_ratio = (negative_count / analyzed_count) * 100

        if clickbait_ratio >= 45:
            overall = "clickbait"
        elif clickbait_ratio >= 25:
            overall = "neutral"
        else:
            overall = "relevant"

        return {"clickbait_score": round(clickbait_ratio, 2),
                "overall_sentiment": overall}

    except Exception as err:
        logger.exception("HuggingFace API error: %s", str(err))
        raise
