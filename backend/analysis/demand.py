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
    "many","much","much","good","great","nice","love","feel","think","say","said","will","would",
    "could","should","need","need","want","want","have","has","had","getting","get","got"
}

def extract_features(text: str) -> dict:
    tl = text.lower()
    tokens = re.findall(r"\b[a-z][a-z0-9]{2,}\b", tl)
    tokens = [t for t in tokens if t not in STOPWORDS and t not in NOISE_WORDS]
    counts = Counter(tokens)
    return dict(counts)

PURCHASE_PATTERNS = [
    (r"(?:would|will|gonna|going to)\s+(?:buy|purchase|get|order|upgrade)", "general"),
    (r"(?:take|have)\s+my\s+money", "high"),
    (r"(?:instant|day one|day\s*1)\s+(?:buy|purchase|order)", "high"),
    (r"(?:worth|value)\s+(?:it|every penny)", "medium"),
    (r"(?:i'?d|i would|will)\s+(?:pay|spend)\s+\$?(\d+(?:,\d{3})*(?:\.\d+)?)", "wtp"),
    (r"shut\s+up\s+and\s+take\s+my\s+money", "high"),
    (r"sign\s+me\s+up", "medium"),
    (r"pre.?order", "high"),
    (r"no\s+brainer", "high"),
]

URGENCY_HIGH = ["urgent","asap","immediately","desperately","can't wait","need this now",
                "critical","must have","deal breaker","unusable"]
URGENCY_MED = ["annoying","frustrating","wish","hope","should","would be nice","need","want"]


def detect_purchase_intent(text: str) -> dict:
    tl = text.lower()
    for pattern, level in PURCHASE_PATTERNS:
        m = re.search(pattern, tl)
        if m:
            amt = None
            if level == "wtp" and m.lastindex and m.group(1):
                try:
                    amt = float(m.group(1).replace(",", ""))
                except ValueError:
                    pass
            return {"has_intent": True, "confidence": level, "amount": amt,
                    "currency": _detect_currency(text)}
    return {"has_intent": False, "confidence": "low", "amount": None, "currency": None}


def _detect_currency(text: str) -> str:
    if any(c in text for c in ["£", "euro", "eur"]):
        return "EUR"
    if any(c in text for c in ["₹", "inr", "rupees"]):
        return "INR"
    return "USD"


def assess_urgency(text: str) -> str:
    tl = text.lower()
    for kw in URGENCY_HIGH:
        if kw in tl:
            return "high"
    for kw in URGENCY_MED:
        if kw in tl:
            return "medium"
    return "low"


def compute_demand_score(stats: dict) -> float:
    score = 0.0
    score += min(stats.get("frequency_pct", 0) / 10, 30)
    score += min(stats.get("sentiment_negative_pct", 0), 30)
    score += {"high": 20, "medium": 10, "low": 0}.get(stats.get("urgency", "low"), 0)
    score += min(stats.get("purchase_intent_pct", 0) * 2, 20)
    return min(round(score, 1), 100)
