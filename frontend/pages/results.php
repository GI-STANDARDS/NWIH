<?php
$jobId = $_GET['job_id'] ?? '';
?>
<div class="page-header-inline">
    <div>
        <h1>Analysis Results</h1>
        <p>AI-powered market intelligence from YouTube comments.</p>
    </div>
</div>

<?php if ($jobId): ?>
<div id="resultView">
    <div class="text-center"><div class="spinner"></div><p class="text-muted">Loading results...</p></div>
</div>
<?php else: ?>
<div class="glass-card">
    <div class="glass-card-title">Completed Analyses</div>
    <div id="completedJobsList"><p class="text-muted">Loading...</p></div>
</div>
<?php endif; ?>

<script>
<?php if ($jobId): ?>
const RESULT_JOB_ID = '<?= htmlspecialchars($jobId) ?>';

function loadResult() {
    const view = document.getElementById('resultView');
    fetch('api.php?action=result&job_id=' + RESULT_JOB_ID)
        .then(r => r.json())
        .then(data => {
            if (data.detail || data.error) {
                view.innerHTML = `<div class="alert error">${data.detail || JSON.stringify(data)}</div>`;
                return;
            }
            renderResult(data, view);
        })
        .catch(err => {
            view.innerHTML = `<div class="alert error">Failed to load: ${err.message}</div>`;
        });
}

function renderResult(data, container) {
    const r = data.result || data;
    const video = r.video || 'Unknown';
    const totalComments = r.total_comments || r.comments_extracted || 0;
    const features = r.top_features || [];
    const painPoints = r.pain_points || [];
    const competitors = r.top_terms || r.competitors || [];
    const purchaseIntent = r.purchase_intent || {};
    const demandScores = r.demand_scores || {};
    const clusters = r.clusters || [];
    const opportunities = r.business_opportunities || [];
    const videoIdeas = r.future_video_ideas || [];
    
    // Extract new insight fields
    const questions = r.questions || [];
    const suggestions = r.suggestions || [];
    const emerging_themes = r.emerging_themes || [];

    const clusterLabels = Object.keys(demandScores);
    const clusterValues = Object.values(demandScores);

    container.innerHTML = `
        <div class="hero-card" style="margin-bottom:24px;">
            <h2 class="hero-title" style="font-size:1.3rem;">${escapeHtml(video)}</h2>
            <p class="hero-subtitle">${totalComments.toLocaleString()} comments analyzed across ${clusters.length} clusters</p>
        </div>

        <div class="stats-grid" style="grid-template-columns:repeat(5,1fr);">
            <div class="stat-glass-glow">
                <div class="stat-value-gold" style="font-size:1.8rem;">${totalComments.toLocaleString()}</div>
                <div class="stat-label">Comments</div>
            </div>
            <div class="stat-glass-glow">
                <div class="stat-value-blue" style="font-size:1.8rem;">${clusters.length}</div>
                <div class="stat-label">Clusters</div>
            </div>
            <div class="stat-glass-glow">
                <div class="stat-value-green" style="font-size:1.8rem;">${purchaseIntent.level || 'N/A'}</div>
                <div class="stat-label">Purchase Intent</div>
            </div>
            <div class="stat-glass-glow">
                <div class="stat-value-cyan" style="font-size:1.8rem;">${competitors.length}</div>
                <div class="stat-label">Top Terms</div>
            </div>
            <div class="stat-glass-glow">
                <div class="stat-value-gold" style="font-size:1.8rem;">${r.opportunity_score || 0}%</div>
                <div class="stat-label">Opportunity Score</div>
            </div>
        </div>

        <div class="grid-2col" style="margin-bottom:20px;">
            <div class="glass-card">
                <div class="glass-card-title">Demand Scores</div>
                <div id="demandChartResult" style="height:300px;"></div>
            </div>
            <div class="glass-card">
                <div class="glass-card-title">Top Terms</div>
                <div id="competitorChart" style="height:300px;"></div>
            </div>
        </div>

        ${features.length ? `
        <div class="glass-card" style="margin-bottom:20px;">
            <div class="glass-card-title">Top Requests</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">${features.slice(0, 10).map(f =>
                `<div class="feature-item" style="padding:8px 12px;background:var(--bg-glass);border-radius:var(--radius-sm);">
                    <strong>${escapeHtml(f.feature)}</strong>
                    <span style="color:var(--text-gold);font-weight:600;">${f.mentions}</span>
                </div>`
            ).join('')}</div>
        </div>` : ''}

        ${painPoints.length ? `
        <div class="glass-card" style="margin-bottom:20px;">
            <div class="glass-card-title">Pain Points</div>
            <ul class="insight-list">${painPoints.map((p, i) =>
                `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${escapeHtml(p.pain)} <span style="color:var(--text-muted);font-size:0.75rem;">(${p.frequency})</span></li>`
            ).join('')}</ul>
        </div>` : '<div class="glass-card" style="margin-bottom:20px;"><div class="glass-card-title">Pain Points</div><p class="text-muted">No pain points detected. Load a GGUF model for AI-powered analysis.</p></div>'}

        ${questions.length ? `
        <div class="glass-card" style="margin-bottom:20px;">
            <div class="glass-card-title">Top Questions</div>
            <ul class="insight-list">${questions.map((q, i) =>
                `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${escapeHtml(q.question)}</li>`
            ).join('')}</ul>
        </div>` : '<div class="glass-card" style="margin-bottom:20px;"><div class="glass-card-title">Top Questions</div><p class="text-muted">No high-value questions detected yet.</p></div>'}

        ${suggestions.length ? `
        <div class="glass-card" style="margin-bottom:20px;">
            <div class="glass-card-title">Suggestions</div>
            <ul class="insight-list">${suggestions.map((s, i) =>
                `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${escapeHtml(s.suggestion)}</li>`
            ).join('')}</ul>
        </div>` : '<div class="glass-card" style="margin-bottom:20px;"><div class="glass-card-title">Suggestions</div><p class="text-muted">No suggestions detected yet.</p></div>'}

        ${opportunities.length ? `
        <div class="glass-card" style="margin-bottom:20px;">
            <div class="glass-card-title">Opportunities</div>
            <ul class="insight-list">${opportunities.map((o, i) =>
                `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${escapeHtml(o.opportunity)} <span style="color:var(--text-gold);font-weight:600;">${o.demand_score}</span></li>`
            ).join('')}</ul>
        </div>` : '<div class="glass-card" style="margin-bottom:20px;"><div class="glass-card-title">Opportunities</div><p class="text-muted">No opportunities were detected in this dataset.</p></div>'}

        ${emerging_themes.length ? `
        <div class="glass-card" style="margin-bottom:20px;">
            <div class="glass-card-title">Emerging Themes</div>
            <ul class="insight-list">${emerging_themes.map((v, i) =>
                `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${escapeHtml(v.idea || v.theme)} <span style="color:var(--text-gold);font-weight:600;">${v.demand_score || v.score}</span></li>`
            ).join('')}</ul>
        </div>` : '<div class="glass-card" style="margin-bottom:20px;"><div class="glass-card-title">Emerging Themes</div><p class="text-muted">No emerging themes were detected in this dataset.</p></div>'}

        <div class="section">
            <h3>🤖 AI-Powered Insights <a href="?page=ai_analysis&job_id=<?= htmlspecialchars($_GET['job_id'] ?? '') ?>" class="btn-small" style="margin-left:20px;padding:6px 16px;background:linear-gradient(135deg,#89b4fa,#74c7ec);color:#1e1e2e;border:none;border-radius:4px;cursor:pointer;font-weight:600;font-size:0.85rem;text-decoration:none;">Open AI Analysis →</a></h3>
        </div>

        <div class="section">
            <div id="clusterList">${clusters.slice(0, 20).map(c => `
                <div class="cluster-card">
                    <div class="cluster-header">
                        <strong>${escapeHtml(c.label || 'Unnamed')}</strong>
                        <span class="badge ${c.urgency === 'high' ? 'badge-high' : c.urgency === 'medium' ? 'badge-medium' : 'badge-low'}">${c.urgency || 'low'}</span>
                        <span class="demand-badge">${c.demand_score || 0}/100</span>
                    </div>
                    <div class="cluster-meta">
                        <span>${c.size} comments (${(c.frequency_pct || 0).toFixed(1)}%)</span>
                        <span class="text-green">${(c.sentiment_positive_pct || 0).toFixed(0)}% pos</span>
                        <span class="text-red">${(c.sentiment_negative_pct || 0).toFixed(0)}% neg</span>
                    </div>
                    ${c.sample_comments && c.sample_comments.length ? `
                    <div style="margin-top:8px;font-size:0.82rem;color:var(--text-muted);font-style:italic;">
                        ${c.sample_comments.slice(0, 2).map(s =>
                            `"${escapeHtml(s)}"`
                        ).join('<br>')}
                    </div>` : ''}
                    ${c.llm_analysis && c.llm_analysis.pain_point ? `
                    <div style="margin-top:8px;padding:8px 12px;background:rgba(212,175,55,0.05);border-radius:var(--radius-sm);font-size:0.82rem;border-left:2px solid var(--gold);">
                        AI: ${escapeHtml(c.llm_analysis.pain_point)}
                    </div>` : `
                    <div style="margin-top:8px;font-size:0.75rem;color:var(--text-muted);font-style:italic;">
                        Load a GGUF model for AI-powered cluster analysis
                    </div>`}
                </div>
            `).join('')}</div>
        </div>
    `;

    // Demand chart
    if (clusterLabels.length) {
        const demandChart = echarts.init(document.getElementById('demandChartResult'));
        demandChart.setOption({
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
            xAxis: { type: 'category', data: clusterLabels.slice(0, 15).map(l => l.substring(0, 20)),
                     axisLabel: { color: '#a6adc8', rotate: 45, fontSize: 10 } },
            yAxis: { type: 'value', max: 100, axisLabel: { color: '#a6adc8' } },
            series: [{ type: 'bar', data: clusterValues.slice(0, 15),
                       itemStyle: { color: '#89b4fa' } }],
            backgroundColor: 'transparent',
        });
    }

    // Competitor chart
    if (competitors.length) {
        const compChart = echarts.init(document.getElementById('competitorChart'));
        compChart.setOption({
            tooltip: { trigger: 'item' },
            series: [{
                type: 'pie',
                data: competitors.map(c => ({ name: c.name, value: c.mentions })),
                label: { color: '#cdd6f4', fontSize: 11 },
            }],
            backgroundColor: 'transparent',
        });
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

loadResult();
<?php endif; ?>

function loadCompletedJobs() {
    fetch('api.php?action=jobs')
        .then(r => r.json())
        .then(jobs => {
            const list = document.getElementById('completedJobsList');
            if (!list) return;
            const completed = jobs.filter(j => j.status === 'completed');
            if (completed.length === 0) {
                list.innerHTML = '<p class="muted">No completed analyses yet.</p>';
            } else {
                list.innerHTML = completed.map(j =>
                    `<a href="?page=results&job_id=${j.job_id}" class="job-item completed">
                        <span class="job-title">${escapeHtml(j.video_title || 'Untitled')}</span>
                        <span class="job-comments">${(j.comments_extracted || 0).toLocaleString()} comments</span>
                        <span class="job-clusters">${j.clusters_found || 0} clusters</span>
                    </a>`
                ).join('');
            }
        });
}

if (!RESULT_JOB_ID) loadCompletedJobs();
</script>
