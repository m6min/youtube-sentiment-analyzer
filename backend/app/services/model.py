import json
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()
logger = logging.getLogger(__name__)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = AsyncGroq(api_key=GROQ_API_KEY)

async def analyze_comments(comments: list[dict]) -> float:
    """Generates an average negative score for comments on video using Groq API (LLaMA 3)"""
    truncated_comments = [
        comment["text"][:300]
        for comment in comments if comment.get("text")
    ]
    
    if not truncated_comments:
        return 0.0

    system_prompt = (
        "Sen sadece JSON formatında yanıt veren bir Türkçe duygu analizi API'sisin. "
        "Sana verilen yorum dizisindeki her bir yorum için analiz yap ve SADECE şu formatta bir JSON döndür: "
        "{\"results\": [{\"label\": \"positive\"}, {\"label\": \"negative\"}]}. "
        "Duygu durumunu belirtmek için sadece 'positive' veya 'negative' kelimelerini kullan."
        "Asla giriş, gelişme cümlesi veya Markdown (```json gibi) ifadeler veya işaretler kullanma."
    )

    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Yorumlar:\n{json.dumps(truncated_comments, ensure_ascii=False)}"}
            ],
            model="llama3-8b-8192",
            temperature=0,
            response_format={"type": "json_object"}
        )

        response_content = chat_completion.choices[0].message.content
        parsed_data = json.loads(response_content)

        results = parsed_data.get("results", [])

        negative_count = 0
        analyzed_count = 0

        for res in results:
            if not isinstance(res, dict):
                continue
                
            label = res.get("label", "").lower()
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
        logger.exception("Groq API error: %s", str(err))
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
