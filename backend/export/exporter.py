import json


def export_job_result(job: dict, clusters: list, competitors: dict, insights: dict) -> dict:
    return {
        "video": job.get("video_title", "Unknown"),
        "video_url": job.get("video_url", ""),
        "total_comments": job.get("total_comments", 0),
        "comments_extracted": job.get("comments_extracted", 0),
        "opportunity_score": insights.get("opportunity_score", 0),
        "top_features": _aggregate_top_features(clusters),
        "pain_points": insights.get("problems", _extract_pain_points(clusters)),
        "questions": insights.get("questions", []),
        "suggestions": insights.get("suggestions", []),
        "emerging_themes": insights.get("emerging_themes", []),
        "top_terms": [
            {"name": b, "mentions": d["mentions"],
             "positive_pct": d.get("positive_pct", 0),
             "negative_pct": d.get("negative_pct", 0)}
            for b, d in sorted(competitors.items(), key=lambda x: -x[1]["mentions"])
        ],
        "competitors": [
            {"name": b, "mentions": d["mentions"],
             "positive_pct": d.get("positive_pct", 0),
             "negative_pct": d.get("negative_pct", 0)}
            for b, d in sorted(competitors.items(), key=lambda x: -x[1]["mentions"])
        ],
        "purchase_intent": _calculate_purchase_intent(clusters),
        "demand_scores": {c.get("label", f"Cluster {i}"): c.get("demand_score", 0)
                          for i, c in enumerate(clusters)},
        "clusters": [
            {
                "id": c.get("cluster_id", i),
                "label": c.get("label", f"Cluster {i}"),
                "size": c.get("size", 0),
                "frequency_pct": c.get("frequency_pct", 0),
                "demand_score": c.get("demand_score", 0),
                "urgency": c.get("urgency", "low"),
                "sentiment_positive_pct": c.get("sentiment_positive_pct", 0),
                "sentiment_negative_pct": c.get("sentiment_negative_pct", 0),
                "keywords": c.get("keywords", {}),
                "sample_comments": c.get("sample_comments", [])[:3],
                "llm_analysis": c.get("llm_analysis", {}),
            }
            for i, c in enumerate(clusters)
        ],
        "business_opportunities": _extract_opportunities(clusters),
        "future_video_ideas": _extract_video_ideas(clusters),
    }


def _aggregate_top_features(clusters: list) -> list:
    feat_count = {}
    for c in clusters:
        for kw in (c.get("keywords", {}) or {}):
            kw_l = kw.lower()
            feat_count[kw_l] = feat_count.get(kw_l, 0) + c.get("size", 0)
    return sorted([{"feature": k, "mentions": v} for k, v in feat_count.items()],
                  key=lambda x: -x["mentions"])[:15]


def _extract_pain_points(clusters: list) -> list:
    points = []
    for c in clusters:
        llm = c.get("llm_analysis", {}) or {}
        if llm.get("pain_point") and llm["pain_point"] != "null":
            points.append({"pain": llm["pain_point"], "cluster": c.get("label", ""),
                          "frequency": c.get("size", 0), "demand_score": c.get("demand_score", 0)})
    if not points:
        # ML-derived fallback: use negative-sentiment clusters with high demand
        for c in clusters:
            neg_pct = c.get("sentiment_negative_pct", 0) or 0
            demand = c.get("demand_score", 0) or 0
            if neg_pct > 20 and demand > 30:
                top_kw = _top_features_of_cluster(c)
                if top_kw:
                    kw_str = ", ".join(k[:40] for k, _ in top_kw[:3])
                    points.append({
                        "pain": f"Negative sentiment cluster: {kw_str}",
                        "cluster": c.get("label", ""),
                        "frequency": c.get("size", 0),
                        "demand_score": demand,
                    })
    return sorted(points, key=lambda x: -x["frequency"])[:10]


def _top_features_of_cluster(c: dict) -> list:
    kws = c.get("keywords", {}) or {}
    if isinstance(kws, dict):
        return sorted(kws.items(), key=lambda x: -x[1])[:5]
    return []


def _calculate_purchase_intent(clusters: list) -> dict:
    total = sum(c.get("size", 0) for c in clusters) or 1
    high = sum(c.get("purchase_intent_count", 0) for c in clusters)
    return {
        "level": "high" if high / total > 0.1 else ("medium" if high / total > 0.03 else "low"),
        "count": high,
        "percentage": round(high / total * 100, 1),
    }


def _extract_opportunities(clusters: list) -> list:
    ops = []
    for c in clusters:
        llm = c.get("llm_analysis", {}) or {}
        for key in ("business_opportunity", "hidden_need"):
            val = llm.get(key)
            if val and val != "null":
                ops.append({"opportunity": val, "source_cluster": c.get("label", ""),
                           "demand_score": c.get("demand_score", 0)})
    if not ops:
        # ML-derived fallback: high-demand clusters with purchase intent
        for c in clusters:
            demand = c.get("demand_score", 0) or 0
            pct = c.get("purchase_intent_count", 0) or 0
            size = c.get("size", 0) or 1
            if demand > 40 or (pct / size) > 0.05:
                top_kw = _top_features_of_cluster(c)
                if top_kw:
                    kw_str = ", ".join(k[:40] for k, _ in top_kw[:2])
                    ops.append({
                        "opportunity": f"High-demand cluster: {kw_str}",
                        "source_cluster": c.get("label", ""),
                        "demand_score": demand,
                    })
    return sorted(ops, key=lambda x: -x["demand_score"])[:10]


def _extract_video_ideas(clusters: list) -> list:
    ideas = []
    for c in clusters:
        llm = c.get("llm_analysis", {}) or {}
        fr = llm.get("feature_request")
        if fr and fr != "null":
            ideas.append({"idea": f"In-depth review: {fr}",
                          "demand_score": c.get("demand_score", 0)})
    if not ideas:
        # ML-derived fallback: feature keywords from top clusters
        for c in sorted(clusters, key=lambda x: -(x.get("demand_score", 0) or 0))[:5]:
            top_kw = _top_features_of_cluster(c)
            if top_kw:
                kw_str = ", ".join(k[:40] for k, _ in top_kw[:2])
                ideas.append({
                    "idea": f"Explore trending topic: {kw_str}",
                    "demand_score": c.get("demand_score", 0),
                })
    return sorted(ideas, key=lambda x: -x["demand_score"])[:10]
