import re

POSITIVE = {"good","great","excellent","amazing","awesome","fantastic","love","best",
            "perfect","beautiful","impressive","outstanding","superb","brilliant",
            "incredible","nice","happy","pleased","satisfied","recommend","worth","like"}
NEGATIVE = {"bad","terrible","awful","horrible","worst","hate","poor","useless",
            "disappointed","trash","garbage","broken","bug","slow","lag","crash",
            "issue","problem","sucks","fail","ugly","cheap","boring","frustrating","mediocre"}
INTENSIFIERS = {"very","extremely","incredibly","absolutely","really","so","too","highly"}


def analyze_sentiment(text: str) -> tuple:
    words = re.findall(r"\w+", text.lower())
    pos = neg = 0
    intensity = 1.0
    for i, w in enumerate(words):
        if w in INTENSIFIERS and i + 1 < len(words):
            if words[i+1] in POSITIVE or words[i+1] in NEGATIVE:
                intensity = 1.5
        if w in POSITIVE:
            pos += intensity
            intensity = 1.0
        elif w in NEGATIVE:
            neg += intensity
            intensity = 1.0
    total = pos + neg
    if total == 0:
        return "neutral", 0.0
    score = (pos - neg) / total
    score = max(-1.0, min(1.0, score))
    label = "positive" if score > 0.2 else ("negative" if score < -0.2 else "neutral")
    return label, round(score, 3)
