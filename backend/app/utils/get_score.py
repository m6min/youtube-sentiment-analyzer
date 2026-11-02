
def get_overall(comment_score: float = 0.0, title_score: float = 0.0) -> dict:
    """Combines both comment and title scores, returns overall
    return {"clickbait_score": round(clickbait_ratio, 2),
                    "overall_sentiment": overall}
    """
    comment_score = max(0.0, min(100.0, float(comment_score)))
    title_score = max(0.0, min(100.0, float(title_score)))

    overall_score = round(
        (comment_score * 0.7) + (title_score * 0.3), 2)

    if overall_score >= 60:
        overall = "clickbait"
    elif overall_score >= 40:
        overall = "neutral"
    else:
        overall = "relevant"

    return {
        "clickbait_score": overall_score,
        "overall_sentiment": overall
    }
