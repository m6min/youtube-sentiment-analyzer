import logging
import os

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")


API_URL = (
    "https://api-inference.huggingface.co/models/"
    "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
)

async def analyze_comments(comments: list[dict]) -> float:
    """Generates an average negative score for comments on video using HuggingFace Api (Zero-Shot)"""
    truncated_comments = [
        comment["text"][:300]
        for comment in comments
    ]
    if not truncated_comments:
        return 0.0
        
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": truncated_comments,
        "parameters": {
            "candidate_labels": ["pozitif", "negatif"]
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=30.0)
        
        response.raise_for_status()
        results = response.json()

        negative_count = 0
        analyzed_count = 0

        for res in results:
            if not isinstance(res, dict):
                continue
                
            labels = res.get("labels", [])
            scores = res.get("scores", [])
            
            if not labels or not scores:
                continue
            top_label = labels[0].lower()
            
            analyzed_count += 1
            if top_label == "negatif":
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