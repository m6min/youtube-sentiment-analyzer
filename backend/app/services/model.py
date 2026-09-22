import os

from dotenv import load_dotenv
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          pipeline)


class CommentAnalyzer:
    def __init__(self):
        model_name = "savasy/bert-base-turkish-sentiment-cased"

        load_dotenv()
        hf_token = os.getenv("HF_TOKEN")
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.analyzer = pipeline(
            "sentiment-analysis", # type: ignore
            model=model,
            tokenizer=tokenizer
        )

    def analyze_comments(self, comments: list):
        """Sends comment list to model, returns clikbait_score and overall_sentiment"""

        texts = [c["text"][:1500] for c in comments]
        results = self.analyzer(texts, truncation=True, max_length=512)
        negative_count = sum(1 for res in results if res["label"] == "negative")
        clickbait_ratio = (negative_count / len(comments)) * 100

        if clickbait_ratio >= 45:
            overall = "clickbait"
        elif clickbait_ratio >= 30:
            overall = "neutral"
        else:
            overall = "relevant"

        return {"clickbait_score": round(clickbait_ratio),
                "overall_sentiment": overall}

analyzer_service = CommentAnalyzer()
