"""
Multi-agent semantic reasoning engine.
Each agent answers ONE question about the audience.
The executive agent synthesizes all outputs into strategy.
"""
import json
import random
from typing import List, Dict, Optional

SYSTEM_PROMPT = """You are an audience psychologist, market researcher, and business strategist.
Your goal is NOT to summarize comments.
Your goal is to understand the people behind the comments.
Infer hidden motivations, emotional drivers, unmet needs, buying intent, objections, opportunities.
Never report keyword frequencies unless they support an insight.
Every conclusion must answer: What does this mean? Why does it matter?
Return ONLY valid JSON with no extra text."""

def _sample_comments(comments: List[Dict], max_count: int = 200) -> List[Dict]:
    if len(comments) <= max_count:
        return comments
    return random.sample(comments, max_count)

def _format_comments(comments: List[Dict], sample_size: int = 150) -> str:
    sampled = _sample_comments(comments, sample_size)
    lines = []
    for i, c in enumerate(sampled):
        text = c.get("text_cleaned") or c.get("text_original") or ""
        if len(text) > 300:
            text = text[:300] + "..."
        lines.append(f"{i+1}. {text}")
    return "\n".join(lines)

def _llm_json(model_manager, prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 2048) -> dict:
    raw = model_manager.generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start:end+1])
    except (json.JSONDecodeError, ValueError):
        pass
    return {"error": "LLM parse failed", "raw": raw[:200]}

def run_intent_agent(model_manager, comments: List[Dict]) -> Dict:
    """
    Identify top user intents, grouped and ranked by importance.
    Never reports keyword frequencies — explains WHY users want something.
    """
    sample_text = _format_comments(comments, 150)
    prompt = f"""Read all {len(comments)} comments below.

Identify the TOP user intents. Group similar intents together. Rank by importance.

For each intent explain:
- What the intent is
- Evidence (refer to comments, not keyword counts)
- Why users have this intent (the hidden motivation)
- How strong is this intent (low/medium/high)

Comments:
{sample_text}

Return JSON:
{{
  "intents": [
    {{
      "intent": "learn_skills",
      "label": "Learn New Skills",
      "evidence": "Many users explicitly ask about learning specific skills like editing, freelancing, AI...",
      "why": "Users feel their current skills are insufficient for career growth",
      "strength": "high",
      "estimated_percentage": 65
    }}
  ],
  "summary": "One paragraph explaining the dominant user intent and its root cause."
}}"""
    return _llm_json(model_manager, prompt)

def run_pain_agent(model_manager, comments: List[Dict]) -> Dict:
    """
    Find what problems people are facing.
    Merge similar problems, rank by severity, explain WHY it's a problem.
    """
    sample_text = _format_comments(comments, 150)
    prompt = f"""Read all {len(comments)} comments below.

Find the TOP problems people are facing. Don't repeat similar comments — merge them.
Rank each problem by severity (low/medium/high/critical).
Explain WHY it's a problem — what's the underlying issue.

Comments:
{sample_text}

Return JSON:
{{
  "problems": [
    {{
      "problem": "No clear career roadmap",
      "evidence": "Users repeatedly ask which skill to learn first and in what order",
      "severity": "high",
      "why": "Without a roadmap users feel paralyzed and may give up or choose wrong path",
      "affected_percentage": 45
    }}
  ],
  "biggest_pain": "One sentence summarizing the #1 pain point"
}}"""
    return _llm_json(model_manager, prompt)

def run_emotion_agent(model_manager, comments: List[Dict]) -> Dict:
    """
    Determine emotional state: Hope, Fear, Confusion, Trust, Frustration, Excitement, Curiosity, Urgency.
    """
    sample_text = _format_comments(comments, 100)
    prompt = f"""Read these {len(comments)} comments.

Determine the emotional state of this audience. For each emotion detected:
- How strong (0-100)
- Evidence from comments
- Why this emotion exists

Comments:
{sample_text}

Return JSON:
{{
  "emotions": [
    {{
      "emotion": "Hope",
      "score": 85,
      "evidence": "Many comments express optimism about learning and earning",
      "why": "Users see creators as proof that skill-based income is achievable"
    }}
  ],
  "dominant_emotion": "Hope",
  "emotional_tone": "Optimistic but uncertain — users want direction",
  "trust_level": "medium",
  "urgency_level": "medium"
}}"""
    return _llm_json(model_manager, prompt)

def run_persona_agent(model_manager, comments: List[Dict]) -> Dict:
    """
    Identify audience groups — estimate percentage, describe goals, pain, buying power, skill level.
    """
    sample_text = _format_comments(comments, 150)
    prompt = f"""Read these {len(comments)} comments.

Identify distinct audience PERSONAS. For each persona:
- Name/label
- Estimated percentage of audience
- Their main goal
- Their main pain
- Buying power (low/medium/high)
- Skill level (beginner/intermediate/advanced)
- Content they prefer (tutorials, case studies, motivation, etc.)

Comments:
{sample_text}

Return JSON:
{{
  "personas": [
    {{
      "persona": "The Beginner Student",
      "percentage": 40,
      "goal": "Learn a profitable skill from zero",
      "pain": "No clear starting point, overwhelmed by options",
      "buying_power": "low",
      "skill_level": "beginner",
      "content_preference": "Step-by-step tutorials, free resources"
    }}
  ],
  "primary_persona": "The Beginner Student",
  "market_readiness": "early",
  "recommended_approach": "Start with free educational content to build trust"
}}"""
    return _llm_json(model_manager, prompt)

def run_demand_agent(model_manager, comments: List[Dict]) -> Dict:
    """
    What skills/products/services are in demand. Based on what people ask for.
    """
    sample_text = _format_comments(comments, 150)
    prompt = f"""Read these {len(comments)} comments.

Identify what skills, products, or services users are actively seeking or asking about.
For each demand:
- What is being demanded
- How strong (0-100)
- Why users want this specifically
- Would they pay for it (low/medium/high intent)
- What format would work (course, template, tool, service, community)

Comments:
{sample_text}

Return JSON:
{{
  "demands": [
    {{
      "demand": "AI skills training",
      "strength": 90,
      "why": "Users believe AI is the future of high-income careers",
      "buying_intent": "high",
      "best_format": "Beginner-friendly AI course with practical projects"
    }}
  ],
  "top_demand": "AI skills training",
  "monetization_readiness": "high",
  "price_sensitivity": "medium"
}}"""
    return _llm_json(model_manager, prompt)

def run_opportunity_agent(model_manager, comments: List[Dict]) -> Dict:
    """
    How to make money from this audience — products, courses, memberships, services, etc.
    """
    sample_text = _format_comments(comments, 120)
    prompt = f"""You are a business consultant reviewing {len(comments)} comments from a creator's audience.

If you had to generate revenue from THIS specific audience, what would you build?
Consider: products, courses, memberships, lead magnets, services, community, coaching, affiliate.

For each opportunity:
- What it is
- Why THIS audience needs it
- Estimated conversion potential (low/medium/high)
- Price point suggestion
- Implementation complexity (easy/medium/hard)

Comments:
{sample_text}

Return JSON:
{{
  "opportunities": [
    {{
      "opportunity": "Beginner-to-Freelancer Course Bundle",
      "why": "Audience is beginner-heavy and wants clear earning path",
      "conversion_potential": "high",
      "price_point": "$50-100 one-time or $20/month",
      "complexity": "medium",
      "estimated_demand": 70
    }}
  ],
  "quick_win": "The easiest thing to sell RIGHT NOW",
  "long_term_play": "What to build over 6-12 months",
  "monetization_strategy": "High-level strategy paragraph"
}}"""
    return _llm_json(model_manager, prompt)

def run_video_agent(model_manager, comments: List[Dict]) -> Dict:
    """
    Generate video ideas based ONLY on demand from comments.
    """
    sample_text = _format_comments(comments, 150)
    prompt = f"""Read these {len(comments)} comments.

Generate 10 video ideas based ONLY on actual demand expressed in the comments.

For each idea:
- Title
- Why this will work (what demand it meets)
- Estimated demand level (0-100)
- Estimated CTR potential (low/medium/high)
- Competition level (low/medium/high)
- Best format (tutorial, case study, rant, interview, etc.)
- A specific hook line

Comments:
{sample_text}

Return JSON:
{{
  "videos": [
    {{
      "title": "Which AI Skill Actually Pays in 2026?",
      "why": "Many users ask about AI but don't know which skill to learn",
      "demand": 95,
      "ctr_potential": "high",
      "competition": "medium",
      "format": "Comparison / Guide",
      "hook": "Stop guessing — here's the AI skill employers are actually hiring for"
    }}
  ],
  "content_strategy": "Overall content strategy paragraph based on audience needs",
  "recommended_series": "A series idea that addresses the top pain point"
}}"""
    return _llm_json(model_manager, prompt)

def run_executive_agent(model_manager, agent_reports: Dict) -> Dict:
    """
    Executive summary agent. Takes all agent outputs and generates final strategy.
    Does NOT summarize — interprets and recommends.
    """
    reports_json = json.dumps(agent_reports, indent=2)
    system = SYSTEM_PROMPT
    prompt = f"""You are a YouTube growth strategist, audience psychologist, and product consultant.

Below are reports from 6 different analysis agents analyzing the same audience.

Your job: DO NOT summarize the reports. Instead, interpret what this means for the creator.

Answer:
1. What do users ACTUALLY want? (hidden motivations)
2. What is the #1 business opportunity?
3. What is the #1 content strategy?
4. What is the creator doing wrong or missing?
5. What is the recommended action plan (3 steps)?
6. What is the one-sentence golden insight?

Agent Reports:
{reports_json}

Return JSON:
{{
  "executive_summary": "2-3 paragraph executive summary as if talking to the creator",
  "hidden_motivations": ["motivation1", "motivation2", "motivation3"],
  "blind_spots": ["what creator is missing", "what creator should stop doing"],
  "business_opportunity": {{
    "opportunity": "name of the top opportunity",
    "why": "why it works for this audience",
    "revenue_potential": "low/medium/high",
    "time_to_revenue": "estimated timeline"
  }},
  "content_strategy": {{
    "advice": "specific content strategy advice",
    "recommended_series": "a video series idea",
    "content_gap": "what's missing from current content"
  }},
  "action_plan": [
    {{"step": 1, "action": "specific action", "why": "why this matters", "timeframe": "1-2 weeks"}}
  ],
  "golden_insight": "One sentence that captures the entire audience's needs"
}}"""
    return _llm_json(model_manager, prompt, system=system, temperature=0.4, max_tokens=3072)

def run_multi_agent_pipeline(model_manager, comments: List[Dict]) -> Dict:
    """
    Run all agents and synthesize results.
    Falls back gracefully if any agent fails.
    """
    if not model_manager or not model_manager.is_ready():
        return {"error": "LLM not available", "pipeline": "heuristic_fallback"}

    agents = {
        "intent_analysis": ("User Intents", run_intent_agent),
        "pain_analysis": ("Pain Points", run_pain_agent),
        "emotion_analysis": ("Emotions", run_emotion_agent),
        "persona_analysis": ("Personas", run_persona_agent),
        "demand_analysis": ("Demand", run_demand_agent),
        "opportunity_analysis": ("Opportunities", run_opportunity_agent),
        "video_ideas": ("Video Ideas", run_video_agent),
    }

    agent_reports = {}
    for key, (label, agent_fn) in agents.items():
        try:
            result = agent_fn(model_manager, comments)
            if "error" in result and result.get("raw"):
                agent_reports[key] = {"error": "parse_failed", "label": label}
            else:
                agent_reports[key] = result
        except Exception as e:
            agent_reports[key] = {"error": str(e), "label": label}

    exec_result = {}
    try:
        exec_result = run_executive_agent(model_manager, agent_reports)
        if "error" in exec_result:
            exec_result = {"executive_summary": "Executive synthesis failed — see individual agent reports.",
                           "individual_reports": agent_reports}
    except Exception as e:
        exec_result = {"executive_summary": f"Executive agent error: {e}",
                       "individual_reports": agent_reports}

    return {
        "pipeline": "multi_agent_reasoning",
        "agents": agent_reports,
        "executive": exec_result,
    }
