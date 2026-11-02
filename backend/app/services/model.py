
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
    """Calculate the percentage of negative Turkish comments."""

    truncated_comments = [
        comment["text"][:300]
        for comment in comments
        if comment.get("text")
    ]

    if not truncated_comments:
        return 0.0

    system_prompt = (
        "You are a Turkish sentiment analysis classifier. "
        "Classify each comment as positive or negative. "
        "Return exactly one label per comment in the same order. "
        "Use only positive or negative labels. "
        "For neutral or ambiguous comments, choose the closer label."
    )

    response_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "sentiment_analysis",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "enum": ["positive", "negative"]
                                }
                            },
                            "required": ["label"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["results"],
                "additionalProperties": False
            }
        }
    }

    try:
        chat_completion = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        truncated_comments,
                        ensure_ascii=False
                    )
                }
            ],
            response_format=response_schema,
            reasoning_format="hidden",
            temperature=0
        )

        raw_response = chat_completion.choices[0].message.content

        logger.debug("Groq response: %s", raw_response)

        if not raw_response:
            raise ValueError("Groq returned an empty response")

        parsed_data = json.loads(raw_response)
        results = parsed_data["results"]

        if len(results) != len(truncated_comments):
            raise ValueError(
                f"Expected {len(truncated_comments)} labels, "
                f"but received {len(results)}"
            )

        negative_count = sum(
            1 for result in results
            if result["label"] == "negative"
        )

        ratio = (negative_count / len(results)) * 100

        return round(ratio, 2)

    except Exception as err:
        logger.exception("Groq API error: %s", str(err))
        raise


def analyze_title(title: str, pipeline) -> int:
    """Calculate clickbait probability using local model."""

    exclamation_count = title.count('!')
    letters = [i for i in title if i.isalpha()]
    uppercase_ratio = 0.0

    if len(letters) > 0:
        uppercase_ratio = round(
            sum(1 for i in letters if i.isupper()) / len(letters),
            2
        )

    data = pd.DataFrame({
        'title': [title],
        'exclamation_count': [exclamation_count],
        'uppercase_ratio': [uppercase_ratio]
    })

    proba = pipeline.predict_proba(data)[0][1]

    return round(proba * 100, 2)
