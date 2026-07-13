import re
from collections import Counter

QUESTION_RE = re.compile(r"\b(what|why|how|when|where|who|which|is|are|can|should|would|could|do|does|did)\b", re.I)
SUGGESTION_RE = re.compile(r"\b(should|need|need to|want to|could|would be great|it would be nice|wish|prefer|please|recommend|better if|would like|should have|need help)\b", re.I)
PAIN_RE = re.compile(r"\b(problem|issue|trouble|frustration|difficult|hard|annoying|slow|broken|bug|fail|disappoint|hate|useless|waste|scam|bad|poor|damage|complain)\b", re.I)


def _get_text(item):
    if isinstance(item, dict):
        return (item.get("text_cleaned") or item.get("text_original") or "").strip()
    return (getattr(item, "text_cleaned", None) or getattr(item, "text_original", None) or "").strip()


def _get_sentiment(item):
    if isinstance(item, dict):
        return (item.get("sentiment_label") or "neutral").lower()
    return (getattr(item, "sentiment_label", None) or "neutral").lower()


def _top_keywords(cluster: dict, n: int = 3) -> list:
    keywords = cluster.get("keywords") or {}
    if isinstance(keywords, dict):
        return [k for k, _ in sorted(keywords.items(), key=lambda x: -x[1])[:n]]
    return []


def _format_cluster_reference(cluster: dict) -> str:
    label = cluster.get("label")
    if label:
        return label
    kws = _top_keywords(cluster, 3)
    return ", ".join(kws) if kws else f"Cluster {cluster.get('cluster_id', '?')}"


def _is_question(text: str) -> bool:
    return "?" in text or bool(QUESTION_RE.search(text))


def _is_suggestion(text: str) -> bool:
    return bool(SUGGESTION_RE.search(text))


def _is_pain(text: str) -> bool:
    return bool(PAIN_RE.search(text))


def _truncate(text: str, length: int = 140) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= length else clean[:length].rstrip() + "..."


def analyze_insights(clusters: list, comments: list) -> dict:
    demands = []
    problems = []
    suggestions = []
    questions = []
    themes = []
    seen_questions = set()
    seen_suggestions = set()

    for cluster in clusters:
        label = _format_cluster_reference(cluster)
        demand_score = float(cluster.get("demand_score", 0) or 0)
        size = int(cluster.get("size", 0) or 0)
        urgency = cluster.get("urgency", "low")
        purchase_intent = int(cluster.get("purchase_intent_count", 0) or 0)
        summary = cluster.get("summary") or ""
        top_keywords = _top_keywords(cluster, 5)

        if demand_score >= 25 or purchase_intent > 0 or urgency == "high":
            demands.append({
                "title": label,
                "detail": summary or f"{size} comments · Demand {demand_score}",
                "keywords": top_keywords,
                "score": round(demand_score, 1),
                "size": size,
            })

        llm = cluster.get("llm_analysis") or {}
        if llm and llm.get("pain_point"):
            problems.append({
                "pain": llm["pain_point"],
                "cluster": label,
                "frequency": size,
                "demand_score": demand_score,
            })
        elif cluster.get("sentiment_negative_pct", 0) >= 35 and demand_score >= 25:
            problems.append({
                "pain": f"Negative sentiment around {label}",
                "cluster": label,
                "frequency": size,
                "demand_score": demand_score,
            })

        if llm and llm.get("business_opportunity"):
            themes.append({
                "theme": llm["business_opportunity"],
                "cluster": label,
                "score": demand_score,
            })
        elif summary:
            themes.append({
                "theme": summary,
                "cluster": label,
                "score": demand_score,
            })

    for comment in comments:
        text = _get_text(comment)
        if not text:
            continue
        if _is_question(text):
            candidate = _truncate(text)
            if candidate not in seen_questions:
                seen_questions.add(candidate)
                questions.append({"question": candidate, "source": _get_text(comment)})
        if _is_suggestion(text):
            candidate = _truncate(text)
            if candidate not in seen_suggestions:
                seen_suggestions.add(candidate)
                suggestions.append({"suggestion": candidate, "source": _get_text(comment)})

    questions = questions[:10]
    suggestions = suggestions[:10]
    problems = sorted(problems, key=lambda x: (-x["frequency"], -x["demand_score"]))[:10]
    demands = sorted(demands, key=lambda x: (-x["score"], -x["size"]))[:10]
    themes = sorted(themes, key=lambda x: -x["score"])[:10]

    total_weight = sum(max(int(c.get("size", 0) or 0), 1) for c in clusters) or 1
    weighted_score = sum((float(c.get("demand_score", 0) or 0) * max(int(c.get("size", 0) or 0), 1)) for c in clusters)
    opportunity_score = round(min(100.0, weighted_score / total_weight), 1)

    return {
        "demands": demands,
        "problems": problems,
        "questions": questions,
        "suggestions": suggestions,
        "emerging_themes": themes,
        "opportunity_score": opportunity_score,
    }
