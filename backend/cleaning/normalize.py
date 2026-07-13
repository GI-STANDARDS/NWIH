import re
import emoji
from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 42

URL_RE = re.compile(r"https?://\S+|www\.\S+")
EXCESS_PUNCT = re.compile(r"([!?.]){3,}")
MULTI_SPACE = re.compile(r"\s{2,}")
REPEAT_CHAR = re.compile(r"(.)\1{3,}")


def clean_comment(text: str) -> dict:
    original = text.strip()

    cleaned = original
    emojis_found = list(emoji.distinct_emoji_list(cleaned))
    for e in emojis_found:
        cleaned = cleaned.replace(e, "")

    cleaned = URL_RE.sub("", cleaned)
    cleaned = EXCESS_PUNCT.sub(r"\1\1", cleaned)
    cleaned = REPEAT_CHAR.sub(r"\1\1", cleaned)
    cleaned = MULTI_SPACE.sub(" ", cleaned).strip()

    try:
        lang = detect(cleaned[:200]) if cleaned else "unknown"
    except LangDetectException:
        lang = "unknown"

    return {
        "text_original": original,
        "text_cleaned": cleaned,
        "emojis": emojis_found,
        "has_emojis": len(emojis_found) > 0,
        "language": lang,
        "comment_length": len(cleaned),
        "has_links": bool(URL_RE.search(original)),
        "has_excessive_punctuation": bool(EXCESS_PUNCT.search(original)),
        "is_spam": _is_spam(cleaned),
    }


def _is_spam(text: str) -> bool:
    t = text.lower()
    signals = 0
    for kw in ["subscribe", "check out my", "follow me", "click here",
               "free money", "earn money", "giveaway", "congratulations",
               "you won", "claim your", "act now"]:
        if kw in t:
            signals += 1
    if len(text) > 50 and text.count("!") > 5:
        signals += 1
    if len(text) > 100 and len(re.findall(r"https?://", text)) > 2:
        signals += 1
    return signals >= 2
