import re
from collections import Counter

STOPWORDS = {
    "a","about","above","after","again","against","all","also","am","an","and",
    "any","are","as","at","be","because","been","before","being","below","between",
    "both","but","by","can","could","did","do","does","doing","down","during","each",
    "few","for","from","further","had","has","have","having","he","her","here","hers",
    "herself","him","himself","his","how","i","if","in","into","is","it","its","itself",
    "just","me","more","most","my","myself","no","nor","not","now","of","off","on","once",
    "only","or","other","our","ours","ourselves","out","over","own","s","same","she","should",
    "so","some","such","than","that","the","their","theirs","them","themselves","then","there",
    "these","they","this","those","through","to","too","under","until","up","very","was","we",
    "were","what","when","where","which","while","who","whom","why","with","would","you","your",
    "yours","yourself","yourselves"
}

NOISE_WORDS = {
    "youtube","video","channel","comment","comments","like","likes","subscribe","subscribers",
    "view","views","someone","people","thing","things","yeah","yes","no","one","want","thanks",
    "thank","hey","lol","wow","still","just","really","also","please","okay","ok","know","time",
    "many","much","good","great","nice","love","feel","think","say","said","will","would",
    "could","should","need","want","have","has","had","getting","get","got"
}

TERM_RE = re.compile(r"\b[a-z][a-z0-9]{2,}\b")


def detect_terms(text: str) -> list:
    tl = text.lower() or ""
    tokens = TERM_RE.findall(tl)
    return [t for t in tokens if t not in STOPWORDS and t not in NOISE_WORDS]


def count_term_mentions(comments: list) -> dict:
    data = {}
    for c in comments:
        if isinstance(c, dict):
            text = c.get("text_cleaned") or c.get("text_original", "")
            sentiment = c.get("sentiment_label", "neutral")
        else:
            text = getattr(c, "text_cleaned", None) or getattr(c, "text_original", "") or ""
            sentiment = getattr(c, "sentiment_label", "neutral") or "neutral"
        terms = set(detect_terms(text))
        for term in terms:
            if term not in data:
                data[term] = {"mentions": 0, "positive": 0, "negative": 0, "neutral": 0}
            data[term]["mentions"] += 1
            data[term][sentiment] += 1
    for term in data:
        total = data[term]["mentions"]
        data[term]["positive_pct"] = round(data[term]["positive"] / total * 100, 1) if total else 0
        data[term]["negative_pct"] = round(data[term]["negative"] / total * 100, 1) if total else 0
    return data


# Backward-compatible alias for older code.
count_brand_mentions = count_term_mentions
