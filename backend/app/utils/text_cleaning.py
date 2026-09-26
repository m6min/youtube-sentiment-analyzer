import re

import emoji


def clean_text(text: str, max_chars: int = 1000) -> str:
    """Cleans emojis, null characters etc. from the comment, and checks if its long for model
    """
    text = re.sub(r'\s+', ' ', text)
    text = emoji.replace_emoji(text, replace='')
    text = text.strip()
    if not any(char.isalnum() for char in text):
        return ""
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    return text
