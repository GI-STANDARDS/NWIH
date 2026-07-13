"""
AI-powered intent and opportunity analysis for comment clusters.
Detects what users want, pain points, and market trends using semantic analysis.
"""
import re
from collections import Counter
from typing import List, Dict

# User Intent Patterns
INTENT_PATTERNS = {
    "learn": re.compile(r"\b(want|need|interested|teach|teach me|learn|guidance|guide|help|explain)\b", re.I),
    "join_course": re.compile(r"\b(join|enroll|course|class|training|how to|join\s+you|interested|paid)\b", re.I),
    "pricing_interest": re.compile(r"\b(price|cost|how much|pay|fee|affordable|expensive|amount)\b", re.I),
    "skill_specific": re.compile(r"\b(video editing|graphic design|social media|seo|content creation|freelance|affiliate|ads|monetize|ai)\b", re.I),
    "contact_request": re.compile(r"\b(contact|whatsapp|number|dm|message|reach|reply|help|please|mam|sir)\b", re.I),
    "complaint": re.compile(r"\b(not|didn't|no reply|didn't respond|expensive|hard|difficult|problem|issue|can't|unable)\b", re.I),
    "success_validation": re.compile(r"\b(great|good|awesome|excellent|amazing|love|perfect|mashallah|thanks|nice)\b", re.I),
    "urgency": re.compile(r"\b(soon|asap|quick|urgent|immediately|losing job|need money|urgent|emergency)\b", re.I),
}

PAIN_POINT_KEYWORDS = {
    "no_response": ["reply", "respond", "message", "contact", "reach"],
    "pricing": ["expensive", "cost", "price", "afford", "pay"],
    "clarity": ["how", "what", "when", "where", "confusing", "understand"],
    "access": ["join", "enroll", "access", "get", "reach"],
    "job_loss": ["losing job", "unemployment", "lost job", "need money"],
    "skill_gap": ["don't know", "don't understand", "learn from zero"],
}

OPPORTUNITY_KEYWORDS = {
    "skill_demand": ["editing", "design", "content", "seo", "marketing", "freelance", "ai", "coding"],
    "monetization": ["earn", "make money", "income", "revenue", "business"],
    "audience_segment": ["student", "housewife", "unemployed", "beginner", "freelancer"],
}


def analyze_user_intents(comments: List[Dict]) -> Dict:
    """Extract user intents and desires from comments."""
    intents = Counter()
    pain_points = []
    user_desires = []
    urgency_mentions = []
    
    for comment in comments:
        text = (comment.get("text_cleaned") or comment.get("text_original") or "").lower()
        if not text or len(text) < 5:
            continue
        
        # Detect intents
        for intent_type, pattern in INTENT_PATTERNS.items():
            if pattern.search(text):
                intents[intent_type] += 1
        
        # Extract pain points
        for pain_type, keywords in PAIN_POINT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                pain_points.append({
                    "type": pain_type,
                    "text": text[:120],
                    "comment_full": comment.get("text_original", "")[:200]
                })
        
        # Extract user desires
        if "learn" in intents or INTENT_PATTERNS["learn"].search(text):
            user_desires.append({
                "desire": "Learning",
                "text": text[:120],
                "sentiment": comment.get("sentiment_label", "neutral")
            })
        if "join_course" in intents or INTENT_PATTERNS["join_course"].search(text):
            user_desires.append({
                "desire": "Course Enrollment",
                "text": text[:120],
                "sentiment": comment.get("sentiment_label", "neutral")
            })
        if "skill_specific" in intents or INTENT_PATTERNS["skill_specific"].search(text):
            skill_match = INTENT_PATTERNS["skill_specific"].search(text)
            if skill_match:
                user_desires.append({
                    "desire": f"Skill Interest: {skill_match.group(0).title()}",
                    "text": text[:120],
                    "sentiment": comment.get("sentiment_label", "neutral")
                })
        if "urgency" in intents or INTENT_PATTERNS["urgency"].search(text):
            urgency_mentions.append({
                "type": "Urgent Need",
                "text": text[:120],
                "sentiment": comment.get("sentiment_label", "neutral")
            })
    
    return {
        "user_intents": dict(intents),
        "top_intents": intents.most_common(5),
        "pain_points": pain_points[:15],
        "user_desires": user_desires[:15],
        "urgency_mentions": urgency_mentions[:10],
    }


def find_trending_topics(clusters: List[Dict]) -> Dict:
    """Identify trending topics based on cluster size, sentiment, and engagement."""
    trending = []
    
    for cluster in clusters:
        size = int(cluster.get("size", 0) or 0)
        freq_pct = float(cluster.get("frequency_pct", 0) or 0)
        pos_pct = float(cluster.get("sentiment_positive_pct", 0) or 0)
        neg_pct = float(cluster.get("sentiment_negative_pct", 0) or 0)
        demand_score = float(cluster.get("demand_score", 0) or 0)
        keywords = cluster.get("keywords", {}) or {}
        
        # Calculate trend score (size + positive sentiment + demand)
        trend_score = (size * 0.4) + (pos_pct * 2) + (demand_score * 0.5)
        
        if size >= 20:  # Minimum cluster size
            top_kws = sorted(keywords.items(), key=lambda x: -x[1])[:3]
            kw_str = ", ".join([k for k, _ in top_kws])
            
            trending.append({
                "topic": cluster.get("label", f"Cluster {cluster.get('cluster_id')}"),
                "keywords": kw_str,
                "size": size,
                "frequency": f"{freq_pct:.1f}%",
                "positive_sentiment": f"{pos_pct:.0f}%",
                "negative_sentiment": f"{neg_pct:.0f}%",
                "demand_score": demand_score,
                "trend_score": round(trend_score, 1),
                "sample": (cluster.get("sample_comments") or [])[0] if cluster.get("sample_comments") else "",
            })
    
    # Sort by trend score
    trending = sorted(trending, key=lambda x: -x["trend_score"])[:10]
    return {"trending_topics": trending}


def extract_market_opportunities(clusters: List[Dict], comments: List[Dict]) -> Dict:
    """Extract market opportunities based on user demands and unmet needs."""
    opportunities = []
    skill_demand = Counter()
    monetization_interest = Counter()
    audience_segments = Counter()
    
    # Scan comments for opportunities
    for comment in comments:
        text = (comment.get("text_cleaned") or comment.get("text_original") or "").lower()
        
        # Track skill demand
        for skill in OPPORTUNITY_KEYWORDS["skill_demand"]:
            if skill in text:
                skill_demand[skill] += 1
        
        # Track monetization interest
        for phrase in ["earn", "make money", "income", "business", "freelance"]:
            if phrase in text:
                monetization_interest[phrase] += 1
        
        # Track audience segments
        for segment in ["student", "housewife", "unemployed", "beginner", "freelancer"]:
            if segment in text:
                audience_segments[segment] += 1
    
    # Create opportunity recommendations
    if skill_demand:
        top_skills = skill_demand.most_common(3)
        for skill, count in top_skills:
            opportunities.append({
                "type": "Skill Gap Opportunity",
                "opportunity": f"High demand for '{skill.title()}' training (mentioned {count} times)",
                "potential": "high",
            })
    
    if monetization_interest:
        opp_count = sum(monetization_interest.values())
        opportunities.append({
            "type": "Monetization Interest",
            "opportunity": f"{opp_count} users interested in earning/business opportunities",
            "potential": "high",
        })
    
    if audience_segments:
        segments = ", ".join([f"{seg.title()} ({cnt})" for seg, cnt in audience_segments.most_common(3)])
        opportunities.append({
            "type": "Audience Segment",
            "opportunity": f"Clear audience interest: {segments}",
            "potential": "medium",
        })
    
    # Check for service/engagement gaps
    unresponsive_complaints = sum(1 for c in comments 
                                  if "reply" in (c.get("text_cleaned") or "").lower() 
                                  or "respond" in (c.get("text_cleaned") or "").lower())
    if unresponsive_complaints > 5:
        opportunities.append({
            "type": "Service Gap",
            "opportunity": f"Community engagement opportunity ({unresponsive_complaints} users seeking direct contact/response)",
            "potential": "high",
        })
    
    return {
        "opportunities": opportunities,
        "skill_demand": dict(skill_demand.most_common(10)),
        "monetization_interest_count": sum(monetization_interest.values()),
        "audience_segments": dict(audience_segments.most_common(10)),
    }


def generate_ai_summary(job_result: Dict, clusters: List[Dict], comments: List[Dict]) -> Dict:
    """Generate comprehensive AI-powered analysis summary."""
    intents = analyze_user_intents(comments)
    trends = find_trending_topics(clusters)
    opportunities = extract_market_opportunities(clusters, comments)
    
    return {
        "summary": {
            "what_users_want": [
                f"{intent}: {count} mentions" 
                for intent, count in intents.get("top_intents", [])[:3]
            ],
            "key_trends": [
                t["topic"] for t in trends.get("trending_topics", [])[:3]
            ],
            "market_gaps": [
                opp["opportunity"] for opp in opportunities.get("opportunities", [])
            ],
        },
        "user_intents": intents,
        "trending_topics": trends,
        "market_opportunities": opportunities,
    }
