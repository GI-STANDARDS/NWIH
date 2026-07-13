<div class="page-header-inline">
    <div>
        <h1 id="aiPageTitle">AI Analysis</h1>
        <p id="aiPageSubtitle">Loading...</p>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
        <a id="aiBackLink" href="?page=jobs" class="btn">← Back</a>
        <span id="aiPipelineBadge" style="font-size:0.75rem;padding:2px 10px;border-radius:8px;background:rgba(137,180,250,0.15);color:var(--text-muted);display:none;"></span>
        <button class="btn btn-primary" onclick="refreshAnalysis()">⟳ Refresh</button>
    </div>
</div>

<div id="aiError" class="glass-card" style="display:none;padding:30px;text-align:center;">
    <p class="text-red" id="aiErrorMessage"></p>
</div>

<div id="aiLoading" class="glass-card" style="padding:40px;text-align:center;">
    <p>Loading AI analysis...</p>
</div>

<div id="aiContent" style="display:none;">
    <!-- ===== REASONING VIEW (multi-agent pipeline) ===== -->
    <div id="reasoningView" style="display:none;">
        <!-- Executive Summary -->
        <div class="glass-card" style="margin-bottom:16px;border-left:4px solid var(--text-gold);">
            <h3 style="color:var(--text-gold);margin-bottom:12px;">Executive Summary</h3>
            <div id="execSummary" style="font-size:0.9rem;line-height:1.6;color:var(--text-muted);"></div>
        </div>

        <!-- Golden Insight -->
        <div class="glass-card" style="margin-bottom:16px;background:rgba(212,175,55,0.06);border-left:4px solid #d4af37;">
            <div id="execGoldenInsight" style="font-size:1rem;font-weight:500;color:#d4af37;text-align:center;padding:8px;"></div>
        </div>

        <!-- Action Plan -->
        <div class="glass-card" style="margin-bottom:16px;">
            <h3 style="color:var(--text-gold);margin-bottom:12px;">Action Plan</h3>
            <div id="execActionPlan" style="display:flex;flex-direction:column;gap:8px;"></div>
        </div>

        <!-- Hidden Motivations -->
        <div class="glass-card" style="margin-bottom:16px;">
            <h3 style="color:var(--text-gold);margin-bottom:12px;">Hidden Motivations</h3>
            <div id="execMotivations" style="display:flex;flex-wrap:wrap;gap:8px;"></div>
        </div>

        <!-- Agent Reports Grid -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:16px;margin-bottom:16px;" id="agentReports"></div>
    </div>

    <!-- ===== HEURISTIC VIEW (keyword-based fallback) ===== -->
    <div id="heuristicView" style="display:none;">
        <div class="glass-card" style="margin-bottom:16px;">
            <h3 style="color:var(--text-gold);margin-bottom:16px;">Summary</h3>
            <div id="aiSummaryCards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;"></div>
        </div>
        <div class="glass-card" style="margin-bottom:16px;">
            <h3 style="color:var(--text-gold);margin-bottom:12px;">User Intents</h3>
            <div id="aiIntents" style="display:flex;flex-direction:column;gap:8px;"></div>
        </div>
        <div class="glass-card" style="margin-bottom:16px;">
            <h3 style="color:var(--text-gold);margin-bottom:12px;">Trending Topics</h3>
            <div id="aiTrending" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;"></div>
        </div>
        <div class="glass-card" style="margin-bottom:16px;">
            <h3 style="color:var(--text-gold);margin-bottom:12px;">Market Opportunities</h3>
            <div id="aiOpportunities" style="display:flex;flex-direction:column;gap:8px;"></div>
        </div>
        <div class="glass-card" style="margin-bottom:16px;">
            <h3 style="color:var(--text-gold);margin-bottom:12px;">Skill Demand</h3>
            <div id="aiSkillDemand" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;"></div>
        </div>
    </div>
</div>

<script>
let AI_JOB_ID = null;

(function() {
    const params = new URLSearchParams(window.location.search);
    AI_JOB_ID = params.get('job_id');
    if (AI_JOB_ID) {
        refreshAnalysis();
    } else {
        document.getElementById('aiLoading').style.display = 'none';
        document.getElementById('aiError').style.display = 'block';
        document.getElementById('aiErrorMessage').textContent = 'No job_id specified. Pass ?job_id=xxx in the URL.';
    }
})();

function refreshAnalysis() {
    if (!AI_JOB_ID) return;
    document.getElementById('aiLoading').style.display = 'block';
    document.getElementById('aiContent').style.display = 'none';
    document.getElementById('aiError').style.display = 'none';

    fetch('api.php?action=ai_analysis&job_id=' + encodeURIComponent(AI_JOB_ID))
        .then(r => { if (!r.ok) throw r.statusText; return r.json(); })
        .then(data => {
            document.getElementById('aiLoading').style.display = 'none';
            if (!data.analysis) {
                document.getElementById('aiError').style.display = 'block';
                document.getElementById('aiErrorMessage').textContent = data.error || 'Failed to generate AI analysis.';
                return;
            }
            const title = data.video_title || 'Analysis';
            document.getElementById('aiPageTitle').textContent = 'AI Analysis — ' + title;
            document.getElementById('aiPageSubtitle').textContent = 'Job: ' + data.job_id;
            document.getElementById('aiBackLink').href = '?page=jobs';

            const analysis = data.analysis || {};
            const reasoning = analysis._reasoning;

            if (reasoning && reasoning.executive) {
                renderReasoningView(reasoning);
            } else {
                renderHeuristicView(analysis);
            }
            document.getElementById('aiContent').style.display = 'block';
        })
        .catch(err => {
            document.getElementById('aiLoading').style.display = 'none';
            document.getElementById('aiError').style.display = 'block';
            document.getElementById('aiErrorMessage').textContent = 'Error: ' + err.toString();
        });
}

function renderReasoningView(reasoning) {
    document.getElementById('reasoningView').style.display = 'block';
    document.getElementById('heuristicView').style.display = 'none';
    document.getElementById('aiPipelineBadge').style.display = 'inline-block';
    document.getElementById('aiPipelineBadge').textContent = 'Multi-Agent Reasoning';

    const exec = reasoning.executive || {};

    // Executive summary
    document.getElementById('execSummary').textContent = exec.executive_summary || 'No executive summary available.';

    // Golden insight
    const gi = document.getElementById('execGoldenInsight');
    const insight = exec.golden_insight;
    gi.textContent = insight ? '"' + insight + '"' : '';
    gi.style.display = insight ? 'block' : 'none';

    // Action plan
    const planEl = document.getElementById('execActionPlan');
    const plan = exec.action_plan || [];
    planEl.innerHTML = plan.map(p =>
        '<div style="display:flex;gap:12px;padding:10px 14px;background:rgba(137,180,250,0.06);border-radius:6px;border-left:3px solid #89b4fa;">' +
        '<span style="font-size:1.2rem;font-weight:700;color:#89b4fa;min-width:24px;">' + (p.step || '') + '</span>' +
        '<div><strong style="font-size:0.85rem;">' + esc(p.action || '') + '</strong>' +
        '<div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">' + esc(p.why || '') + '</div>' +
        (p.timeframe ? '<div style="font-size:0.75rem;color:var(--text-gold);margin-top:4px;">' + esc(p.timeframe) + '</div>' : '') +
        '</div></div>'
    ).join('');

    // Hidden motivations
    const motEl = document.getElementById('execMotivations');
    const motifs = exec.hidden_motivations || [];
    motEl.innerHTML = motifs.map(m =>
        '<span style="padding:6px 14px;background:rgba(203,166,247,0.1);border-radius:16px;font-size:0.85rem;border:1px solid rgba(203,166,247,0.2);">' + esc(m) + '</span>'
    ).join('');

    // Agent reports
    const agents = reasoning.agents || {};
    const agentCards = [
        { key: 'intent_analysis', icon: '🎯', title: 'User Intents' },
        { key: 'pain_analysis', icon: '🩹', title: 'Pain Points' },
        { key: 'emotion_analysis', icon: '💭', title: 'Emotions' },
        { key: 'persona_analysis', icon: '👥', title: 'Personas' },
        { key: 'demand_analysis', icon: '📈', title: 'Demand' },
        { key: 'opportunity_analysis', icon: '💡', title: 'Opportunities' },
        { key: 'video_ideas', icon: '🎬', title: 'Video Ideas' },
    ];

    const container = document.getElementById('agentReports');
    container.innerHTML = agentCards.map(ac => {
        const agent = agents[ac.key] || {};
        if (agent.error) return '';
        return '<div class="glass-card" style="padding:14px;">' +
            '<h4 style="color:var(--text-gold);margin:0 0 10px 0;font-size:0.9rem;">' + ac.icon + ' ' + ac.title + '</h4>' +
            renderAgentContent(ac.key, agent) +
            '</div>';
    }).join('');
}

function renderAgentContent(key, agent) {
    switch (key) {
        case 'intent_analysis': {
            const intents = agent.intents || [];
            return intents.map(i =>
                '<div style="margin-bottom:8px;padding:8px;background:rgba(137,180,250,0.06);border-radius:6px;">' +
                '<div style="font-weight:600;font-size:0.85rem;">' + esc(i.label || i.intent) +
                ' <span style="color:var(--text-gold);font-weight:400;">(' + (i.estimated_percentage || 0) + '%)</span></div>' +
                '<div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">' + esc(i.why || '') + '</div>' +
                (i.evidence ? '<div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;font-style:italic;">' + esc(i.evidence).slice(0, 150) + '</div>' : '') +
                '</div>'
            ).join('');
        }
        case 'pain_analysis': {
            const problems = agent.problems || [];
            return problems.map(p =>
                '<div style="margin-bottom:8px;padding:8px;background:rgba(232,104,104,0.06);border-radius:6px;border-left:2px solid ' +
                (p.severity === 'critical' ? '#e86868' : p.severity === 'high' ? '#f9e2af' : '#89b4fa') + ';">' +
                '<div style="font-weight:600;font-size:0.85rem;">' + esc(p.problem || '') +
                ' <span style="color:var(--text-muted);font-weight:400;">(' + (p.affected_percentage || 0) + '%)</span></div>' +
                '<div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">' + esc(p.why || '') + '</div>' +
                '<div style="font-size:0.7rem;color:' + (p.severity === 'critical' ? '#e86868' : 'var(--text-muted)') + ';margin-top:4px;">Severity: ' + (p.severity || 'unknown') + '</div>' +
                '</div>'
            ).join('');
        }
        case 'emotion_analysis': {
            const emotions = agent.emotions || [];
            const maxScore = Math.max(...emotions.map(e => e.score || 0), 1);
            return emotions.map(e =>
                '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">' +
                '<span style="min-width:80px;font-size:0.85rem;font-weight:500;">' + esc(e.emotion || '') + '</span>' +
                '<div style="flex:1;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;">' +
                '<div style="height:100%;width:' + ((e.score || 0) / maxScore * 100) + '%;background:#89b4fa;border-radius:3px;"></div></div>' +
                '<span style="font-size:0.75rem;color:var(--text-muted);min-width:30px;text-align:right;">' + (e.score || 0) + '</span>' +
                '</div>'
            ).join('') +
            (agent.dominant_emotion ? '<div style="margin-top:8px;font-size:0.8rem;color:var(--text-muted);">Dominant: <strong style="color:var(--text-gold);">' + esc(agent.dominant_emotion) + '</strong></div>' : '') +
            (agent.trust_level ? '<div style="font-size:0.8rem;color:var(--text-muted);">Trust: ' + esc(agent.trust_level) + ' · Urgency: ' + esc(agent.urgency_level || '') + '</div>' : '');
        }
        case 'persona_analysis': {
            const personas = agent.personas || [];
            return personas.map(p =>
                '<div style="margin-bottom:10px;padding:8px;background:rgba(203,166,247,0.06);border-radius:6px;">' +
                '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">' +
                '<strong style="font-size:0.85rem;">' + esc(p.persona || '') + '</strong>' +
                '<span style="color:var(--text-gold);font-size:0.8rem;">' + (p.percentage || 0) + '%</span></div>' +
                '<div style="font-size:0.8rem;color:var(--text-muted);">Goal: ' + esc(p.goal || '') + '</div>' +
                '<div style="font-size:0.8rem;color:var(--text-muted);">Pain: ' + esc(p.pain || '') + '</div>' +
                '<div style="font-size:0.78rem;color:var(--text-muted);margin-top:4px;">Buying: ' + esc(p.buying_power || '') + ' · Skill: ' + esc(p.skill_level || '') + '</div>' +
                '</div>'
            ).join('');
        }
        case 'demand_analysis': {
            const demands = agent.demands || [];
            return demands.map(d =>
                '<div style="margin-bottom:8px;padding:8px;background:rgba(80,220,120,0.06);border-radius:6px;border-left:2px solid #50dc78;">' +
                '<div style="font-weight:600;font-size:0.85rem;">' + esc(d.demand || '') +
                ' <span style="color:var(--text-gold);font-weight:400;">(' + (d.strength || 0) + '/100)</span></div>' +
                '<div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">' + esc(d.why || '') + '</div>' +
                (d.best_format ? '<div style="font-size:0.78rem;color:var(--text-muted);margin-top:4px;">Format: ' + esc(d.best_format) + ' · Intent: ' + esc(d.buying_intent || '') + '</div>' : '') +
                '</div>'
            ).join('');
        }
        case 'opportunity_analysis': {
            const opps = agent.opportunities || [];
            return opps.map(o =>
                '<div style="margin-bottom:8px;padding:8px;background:rgba(249,226,175,0.06);border-radius:6px;border-left:2px solid #f9e2af;">' +
                '<div style="font-weight:600;font-size:0.85rem;">' + esc(o.opportunity || '') + '</div>' +
                '<div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">' + esc(o.why || '') + '</div>' +
                (o.price_point ? '<div style="font-size:0.75rem;color:var(--text-gold);margin-top:4px;">$' + esc(o.price_point) + ' · Potential: ' + esc(o.conversion_potential || '') + '</div>' : '') +
                '</div>'
            ).join('');
        }
        case 'video_ideas': {
            const videos = agent.videos || [];
            return videos.map(v =>
                '<div style="margin-bottom:8px;padding:8px;background:rgba(137,180,250,0.06);border-radius:6px;">' +
                '<div style="font-weight:600;font-size:0.85rem;">' + esc(v.title || '') + '</div>' +
                '<div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">' + esc(v.why || '') + '</div>' +
                (v.hook ? '<div style="font-size:0.78rem;color:var(--text-gold);margin-top:4px;">Hook: "' + esc(v.hook) + '"</div>' : '') +
                '<div style="font-size:0.75rem;color:var(--text-muted);margin-top:2px;">Demand: ' + (v.demand || 0) + '/100 · CTR: ' + esc(v.ctr_potential || '') + ' · Format: ' + esc(v.format || '') + '</div>' +
                '</div>'
            ).join('');
        }
        default:
            return '<pre style="font-size:0.75rem;color:var(--text-muted);white-space:pre-wrap;">' + esc(JSON.stringify(agent, null, 2).slice(0, 500)) + '</pre>';
    }
}

function renderHeuristicView(analysis) {
    document.getElementById('reasoningView').style.display = 'none';
    document.getElementById('heuristicView').style.display = 'block';
    document.getElementById('aiPipelineBadge').style.display = 'inline-block';
    document.getElementById('aiPipelineBadge').textContent = 'Keyword Analysis';

    const summary = analysis.summary || {};
    const intents = analysis.user_intents || {};
    const trends = analysis.trending_topics || {};
    const opps = analysis.market_opportunities || {};

    const summaryCards = document.getElementById('aiSummaryCards');
    summaryCards.innerHTML = '';
    const summarySections = [
        { title: 'What Users Want', items: summary.what_users_want || [], color: '#89b4fa' },
        { title: 'Key Trends', items: summary.key_trends || [], color: '#50dc78' },
        { title: 'Market Gaps', items: summary.market_gaps || [], color: '#f9e2af' },
    ];
    summarySections.forEach(s => {
        const card = document.createElement('div');
        card.style.cssText = 'padding:14px;background:rgba(255,255,255,0.03);border-radius:8px;border-left:3px solid ' + s.color + ';';
        card.innerHTML = '<h4 style="color:' + s.color + ';margin:0 0 10px 0;font-size:0.9rem;">' + s.title + '</h4>' +
            s.items.map(item => '<div style="padding:6px 10px;margin:4px 0;background:rgba(255,255,255,0.04);border-radius:4px;font-size:0.85rem;">' + esc(item) + '</div>').join('');
        summaryCards.appendChild(card);
    });

    const intentsEl = document.getElementById('aiIntents');
    intentsEl.innerHTML = (intents.top_intents || []).slice(0, 10).map(([intent, count]) => {
        const maxCount = Math.max(...(intents.top_intents || []).map(i => i[1]), 1);
        const pct = (count / maxCount * 100).toFixed(0);
        return '<div style="display:flex;align-items:center;gap:12px;padding:8px 12px;background:rgba(137,180,250,0.08);border-radius:6px;">' +
            '<span style="flex:1;font-size:0.85rem;font-weight:500;">' + esc(intent).replace(/_/g, ' ').toUpperCase() + '</span>' +
            '<span style="font-size:0.8rem;color:var(--text-muted);min-width:40px;text-align:right;">' + count + '</span>' +
            '<div style="width:100px;height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">' +
            '<div style="height:100%;width:' + pct + '%;background:#89b4fa;border-radius:3px;"></div></div></div>';
    }).join('');

    document.getElementById('aiTrending').innerHTML = (trends.trending_topics || []).slice(0, 6).map(t =>
        '<div style="padding:14px;background:rgba(80,220,120,0.06);border-radius:8px;border-left:3px solid #50dc78;">' +
        '<div style="display:flex;justify-content:space-between;margin-bottom:8px;">' +
        '<strong style="font-size:0.85rem;">' + esc(t.topic || '') + '</strong>' +
        '<span style="color:var(--text-gold);font-size:0.8rem;">Score: ' + (t.trend_score || '') + '</span></div>' +
        '<div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:4px;">' +
        (t.size || 0) + ' comments · ' + esc(t.frequency || '') + ' · ' + esc(t.positive_sentiment || '') + ' positive</div>' +
        (t.keywords ? '<div style="font-size:0.78rem;color:var(--text-muted);">Keywords: ' + esc(t.keywords) + '</div>' : '') +
        '</div>'
    ).join('');

    document.getElementById('aiOpportunities').innerHTML = (opps.opportunities || []).map(o =>
        '<div style="padding:10px 14px;background:rgba(249,226,175,0.06);border-radius:6px;border-left:3px solid #f9e2af;">' +
        '<strong style="font-size:0.85rem;color:#f9e2af;">' + esc(o.type || '') + '</strong>' +
        '<br><span style="font-size:0.85rem;color:var(--text-muted);">' + esc(o.opportunity || '') + '</span></div>'
    ).join('');

    const skillEl = document.getElementById('aiSkillDemand');
    const skills = opps.skill_demand || {};
    const skillEntries = Object.entries(skills).slice(0, 10);
    const maxSkill = Math.max(...Object.values(skills), 1);
    skillEl.innerHTML = skillEntries.map(([skill, count]) => {
        const pct = (count / maxSkill * 100).toFixed(0);
        return '<div style="padding:10px;background:rgba(203,166,247,0.06);border-radius:6px;border-left:3px solid #cba6f7;">' +
            '<div style="font-size:0.82rem;font-weight:600;margin-bottom:4px;">' + esc(skill).toUpperCase() + '</div>' +
            '<div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;">' + count + ' mentions</div>' +
            '<div style="height:4px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;">' +
            '<div style="height:100%;width:' + pct + '%;background:#cba6f7;border-radius:2px;"></div></div></div>';
    }).join('');
}

function esc(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}
</script>
