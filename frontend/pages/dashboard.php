<!-- ═══════════════════════════════════════════════════════════════════════════
     Futuristic AI Intelligence Dashboard
     ═══════════════════════════════════════════════════════════════════════════ -->

<div class="page-header-inline">
    <div>
        <h1>Intelligence Dashboard</h1>
        <p>Real-time market intelligence from YouTube comments</p>
    </div>
</div>

<!-- ═══ STATUS BADGES ROW ═══ -->
<div class="stats-grid" style="grid-template-columns:1fr 1fr;margin-bottom:20px;">
    <!-- ML Pipeline Status -->
    <div class="glass-card" style="padding:16px 20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div class="glass-card-title" style="margin:0;font-size:0.95rem;">ML Analysis Pipeline</div>
            <span id="mlPipelineBadge" class="ai-engine-status-badge online">Ready</span>
        </div>
        <div style="display:flex;gap:12px;font-size:0.8rem;flex-wrap:wrap;">
            <span id="mlStatusExtraction"><span class="text-green">&#10003;</span> Extraction</span>
            <span id="mlStatusEmbeddings"><span class="text-green">&#10003;</span> Embeddings (sentence-transformers)</span>
            <span id="mlStatusClustering"><span class="text-green">&#10003;</span> Clustering (HDBSCAN)</span>
            <span id="mlStatusVector"><span class="text-green">&#10003;</span> Vector Search (FAISS)</span>
        </div>
        <div style="margin-top:6px;font-size:0.78rem;color:var(--text-muted);">
            <span id="mlPipelineMessage">No GGUF required — works immediately</span>
        </div>
    </div>

    <!-- AI Model Status (Optional) -->
    <div class="glass-card" style="padding:16px 20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div class="glass-card-title" style="margin:0;font-size:0.95rem;">AI Model Status</div>
            <span id="aiEngineBadge" class="ai-engine-status-badge offline">Offline</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;font-size:0.8rem;">
            <span>Model:</span><span id="aiMetricModel">None</span>
            <span>Backend:</span><span id="aiMetricBackend">—</span>
            <span>Status:</span><span id="aiMetricStatus">No GGUF model</span>
        </div>
        <div style="margin-top:6px;font-size:0.78rem;color:var(--text-gold);">
            <span id="aiPipelineMessage">Optional — load a GGUF model in Tools for AI summaries &amp; chat</span>
        </div>
    </div>
</div>

<!-- ═══ WORKFLOW GUIDE ═══ -->
<div class="glass-card" style="padding:14px 20px;margin-bottom:20px;">
    <div style="font-size:0.8rem;font-weight:600;color:var(--text-gold);margin-bottom:8px;"> Workflow</div>
    <div class="workflow-steps">
        <div class="workflow-step" data-wf="1"><span class="step-num">1</span> Extract Comments</div>
        <span class="workflow-arrow">→</span>
        <div class="workflow-step" data-wf="2"><span class="step-num">2</span> Run ML Analysis</div>
        <span class="workflow-arrow">→</span>
        <div class="workflow-step" data-wf="3"><span class="step-num">3</span> Review Analytics</div>
        <span class="workflow-arrow">→</span>
        <div class="workflow-step optional" data-wf="4"><span class="step-num" style="opacity:0.5;">4</span> Start llama.cpp Server</div>
        <span class="workflow-arrow" style="opacity:0.2;">→</span>
        <div class="workflow-step optional" data-wf="5"><span class="step-num" style="opacity:0.5;">5</span> Load GGUF Model</div>
        <span class="workflow-arrow" style="opacity:0.2;">→</span>
        <div class="workflow-step optional" data-wf="6"><span class="step-num" style="opacity:0.5;">6</span> Use AI Features</div>
    </div>
    <div style="margin-top:6px;font-size:0.72rem;color:var(--text-muted);">
        Steps 1–3 (ML) work without any setup. Steps 4–6 (AI) require a GGUF model.
        <a href="?page=ai_manager" style="color:var(--text-gold);margin-left:8px;">Open AI Control Center →</a>
    </div>
</div>

<!-- ═══ A. HERO ANALYSIS CARD ═══ -->
<div class="hero-card">
    <h2 class="hero-title"> Command Center</h2>
    <p class="hero-subtitle">Enter any YouTube URL to extract, cluster, and analyze up to 1,000,000 comments with ML (no AI model required)</p>

    <form id="heroForm">
        <div class="hero-input-row">
            <input type="text" id="heroUrl" placeholder="https://www.youtube.com/watch?v=..." class="hero-input" autofocus>
            <button type="submit" class="btn-launch">Launch Analysis</button>
        </div>
        <div class="hero-options">
            <select id="heroDepth" class="hero-select">
                <option value="10000"> Normal — 10K comments</option>
                <option value="50000" selected> Deep — 50K comments</option>
                <option value="500000"> Extreme — 500K comments</option>
                <option value="1000000"> ⚡ Ultra — 1M+ comments</option>
            </select>
            <select id="heroType" class="hero-select">
                <option value="video"> Video</option>
                <option value="playlist"> Playlist</option>
                <option value="channel"> Channel</option>
            </select>
        </div>
    </form>
</div>

<!-- ═══ B. ANALYTICS OVERVIEW PANEL ═══ -->
<div class="stats-grid" id="statsGrid">
    <div class="stat-glass-glow float-slow">
        <div class="stat-value-gold" id="statComments">0</div>
        <div class="stat-label">Total Comments</div>
    </div>
    <div class="stat-glass-glow float-slow" style="animation-delay:0.5s;">
        <div class="stat-value-green" id="statProcessed">0</div>
        <div class="stat-label">Processed</div>
    </div>
    <div class="stat-glass-glow float-slow" style="animation-delay:1s;">
        <div class="stat-value-blue" id="statClusters">0</div>
        <div class="stat-label">Clusters Found</div>
    </div>
    <div class="stat-glass-glow float-slow" style="animation-delay:1.5s;">
        <div class="stat-value-cyan" id="statJobs">0</div>
        <div class="stat-label">Analyses Run</div>
    </div>
    <div class="stat-glass-glow float-slow" style="animation-delay:2s;">
        <div class="stat-value-gold" id="statAnalysisTime">—</div>
        <div class="stat-label">Analysis Time</div>
    </div>
</div>

<!-- Pipeline Progress -->
<div class="glass-card" style="padding:20px 24px; margin-bottom:24px;">
    <div class="glass-card-title">Pipeline Status</div>
    <div class="progress-container progress-scan">
        <div class="progress-bar" id="pipelineBar" style="width:0%"></div>
    </div>
    <div class="pipeline-steps" id="pipelineSteps">
        <div class="pipeline-step" data-step="0">
            <div class="pipeline-dot"></div>
            <div class="pipeline-label">Extraction</div>
        </div>
        <div class="pipeline-step" data-step="1">
            <div class="pipeline-dot"></div>
            <div class="pipeline-label">Cleaning</div>
        </div>
        <div class="pipeline-step" data-step="2">
            <div class="pipeline-dot"></div>
            <div class="pipeline-label">Embeddings</div>
        </div>
        <div class="pipeline-step" data-step="3">
            <div class="pipeline-dot"></div>
            <div class="pipeline-label">Clustering</div>
        </div>
        <div class="pipeline-step" data-step="4" style="opacity:0.7;">
            <div class="pipeline-dot"></div>
            <div class="pipeline-label">AI <span style="font-size:0.65rem;opacity:0.6;">(opt.)</span></div>
        </div>
        <div class="pipeline-step" data-step="5">
            <div class="pipeline-dot"></div>
            <div class="pipeline-label">Report</div>
        </div>
    </div>
    <div class="progress-text" id="pipelineText">Idle — Submit a URL to begin</div>
</div>

<!-- ═══ CHARTS ROW ═══ -->
<div class="grid-3col" style="margin-bottom:20px;">

    <!-- C. User Requests -->
    <div class="glass-card">
        <div class="glass-card-title">Top Requests</div>
        <div id="featureBars">
            <div class="empty-state">
                <div class="empty-state-icon">▣</div>
                <p>No data yet — run an analysis</p>
            </div>
        </div>
    </div>

    <!-- D. Sentiment Wheel + E. Purchase Intent Gauge -->
    <div class="glass-card">
        <div class="glass-card-title">Sentiment Distribution</div>
        <div class="sentiment-wrapper">
            <div id="sentimentChart" style="height:220px;width:100%;"></div>
            <div class="sentiment-center-text">
                <div class="sentiment-center-value" id="sentimentCenterValue">—</div>
                <div class="sentiment-center-label" id="sentimentCenterLabel">Sentiment</div>
            </div>
        </div>

        <div style="margin-top:12px; padding-top:16px; border-top:1px solid var(--glass-border);">
            <div class="glass-card-title" style="margin-bottom:8px;">Purchase Intent</div>
            <div class="gauge-container">
                <svg class="gauge-svg" viewBox="0 0 180 100">
                    <defs>
                        <linearGradient id="gaugeGold" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#D4AF37" />
                            <stop offset="100%" stop-color="#F5D27A" />
                        </linearGradient>
                    </defs>
                    <path d="M 20 85 A 70 70 0 0 1 160 85" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="12" stroke-linecap="round"/>
                    <path d="M 20 85 A 70 70 0 0 1 160 85" fill="none" stroke="url(#gaugeGold)" stroke-width="12" stroke-linecap="round"
                          stroke-dasharray="310" stroke-dashoffset="160" id="gaugeArc"/>
                    <line class="gauge-needle" id="gaugeNeedle" x1="90" y1="85" x2="90" y2="25"
                          stroke="#F5D27A" stroke-width="2.5" stroke-linecap="round"
                          style="transform: rotate(0deg); box-shadow: 0 0 10px rgba(245,210,122,0.5);"/>
                    <circle cx="90" cy="85" r="4" fill="#F5D27A" opacity="0.8"/>
                </svg>
                <div class="gauge-value" id="gaugeValue">—</div>
                <div class="gauge-label" id="gaugeLabel">Purchase Intent</div>
            </div>
        </div>
    </div>

    <!-- F. Trending Terms -->
    <div class="glass-card">
        <div class="glass-card-title">Trending Terms</div>
        <div id="competitorList">
            <div class="empty-state">
                <div class="empty-state-icon">⊡</div>
                <p>No trending terms detected yet</p>
            </div>
        </div>
    </div>

</div>

<!-- ═══ G. INSIGHTS PANELS (BOTTOM GRID) ═══ -->
<div class="grid-4col" style="margin-bottom:20px;">

    <div class="insight-card">
        <span class="insight-icon">◈</span>
        <div class="insight-title">Pain Points</div>
        <ul class="insight-list" id="insightPainPoints">
            <li style="color:var(--text-muted); font-size:0.8rem;">No data — run an analysis</li>
        </ul>
    </div>

    <div class="insight-card">
        <span class="insight-icon">◇</span>
        <div class="insight-title">Top Requests</div>
        <ul class="insight-list" id="insightFeatures">
            <li style="color:var(--text-muted); font-size:0.8rem;">No data — run an analysis</li>
        </ul>
    </div>

    <div class="insight-card">
        <span class="insight-icon">▣</span>
        <div class="insight-title">Opportunities</div>
        <ul class="insight-list" id="insightOpportunities">
            <li style="color:var(--text-muted); font-size:0.8rem;">No data — run an analysis</li>
        </ul>
    </div>

    <div class="insight-card">
        <span class="insight-icon">⊟</span>
        <div class="insight-title">Emerging Themes</div>
        <ul class="insight-list" id="insightVideos">
            <li style="color:var(--text-muted); font-size:0.8rem;">No data — run an analysis</li>
        </ul>
    </div>

</div>

<!-- ═══ H. RECENT JOBS ═══ -->
<div class="glass-card">
    <div class="glass-card-title">Recent Analyses</div>
    <div id="recentJobsList"><p class="text-muted">Loading...</p></div>
</div>

<script>
// ── Format time ──
function fmtTime(seconds) {
    if (seconds < 60) return seconds + 's';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ' + (seconds % 60) + 's';
    return Math.floor(seconds / 3600) + 'h ' + Math.floor((seconds % 3600) / 60) + 'm';
}

// ── ML Pipeline Status (no GGUF required) ──
function loadMLPipelineStatus() {
    fetch('api.php?action=ml_status')
        .then(r => r.json())
        .then(data => {
            const badge = document.getElementById('mlPipelineBadge');
            const msg = document.getElementById('mlPipelineMessage');
            if (badge) {
                badge.className = 'ai-engine-status-badge ' + (data.pipeline_ready ? 'online' : 'offline');
                badge.textContent = data.pipeline_ready ? 'Ready' : 'Missing Packages';
            }
            if (msg) msg.textContent = data.pipeline_ready
                ? 'No GGUF required — ML analysis works immediately'
                : 'Install required packages in Tools > ML Setup';

            const setStatus = (id, ok) => {
                const el = document.getElementById(id);
                if (el) el.innerHTML = ok ? '<span class="text-green">&#10003;</span>' : '<span class="text-red">&#10007;</span>';
            };
            if (data.extraction) setStatus('mlStatusExtraction');
            if (data.sentence_transformers) setStatus('mlStatusEmbeddings');
            if (data.hdbscan) setStatus('mlStatusClustering');
            if (data.faiss) setStatus('mlStatusVector');
        })
        .catch(() => {});
}

// ── AI Model Status (Optional, GGUF required) ──
function loadAIEngineStatus() {
    apiGet('model_status')
        .then(data => {
            const badge = document.getElementById('aiEngineBadge');
            if (badge) {
                const loaded = data.loaded || data.server_running;
                badge.className = 'ai-engine-status-badge ' + (data.loaded ? 'online' : data.server_running ? 'idle' : 'offline');
                badge.textContent = data.loaded ? 'Active' : data.server_running ? 'Server Idle' : 'Offline';
            }
            document.getElementById('aiMetricModel').textContent = data.model_name || 'None';
            document.getElementById('aiMetricBackend').textContent = data.backend || '—';
            const statusEl = document.getElementById('aiMetricStatus');
            if (statusEl) {
                if (data.loaded) statusEl.textContent = 'Loaded (' + data.model_name + ')';
                else if (data.server_running) statusEl.textContent = 'Server running, no model';
                else if (data.binary_available && data.model_available) statusEl.textContent = 'Ready to load';
                else if (!data.binary_available) statusEl.textContent = 'llama.cpp binary missing';
                else if (!data.model_available) statusEl.textContent = 'No GGUF model';
                else statusEl.textContent = 'Not available';
            }
        })
        .catch(() => {
            const badge = document.getElementById('aiEngineBadge');
            if (badge) badge.className = 'ai-engine-status-badge offline';
            document.getElementById('aiMetricStatus').textContent = 'Unreachable';
        });
}

// ── Hero Form ──
document.getElementById('heroForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const url = document.getElementById('heroUrl').value;
    if (!url) return;
    const depth = parseInt(document.getElementById('heroDepth').value);
    const type = document.getElementById('heroType').value;

    fetch('api.php?action=analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ youtube_url: url, max_comments: depth, source_type: type })
    })
    .then(r => r.json())
    .then(data => {
        if (data.job_id) {
            window.location.href = '?page=status&job_id=' + data.job_id;
        } else {
            alert('Error: ' + (data.detail || JSON.stringify(data)));
        }
    })
    .catch(err => alert('Connection error: ' + err.message));
});

// ── Dashboard Data Loading ──
function loadDashboard() {
    apiGet('jobs')
        .then(jobs => {
            const total = jobs.length;
            const completed = jobs.filter(j => j.status === 'completed');
            const running = jobs.filter(j => j.status === 'processing' || j.status === 'extracting' || j.status === 'embedding' || j.status === 'clustering' || j.status === 'analyzing');
            const comments = jobs.reduce((s, j) => s + (j.comments_extracted || 0), 0);
            const clusters = jobs.reduce((s, j) => s + (j.clusters_found || 0), 0);
            const totalTime = jobs.reduce((s, j) => s + (j.analysis_time_seconds || 0), 0);

            document.getElementById('statJobs').textContent = total;
            document.getElementById('statProcessed').textContent = completed.length;
            document.getElementById('statComments').textContent = fmt(comments);
            document.getElementById('statClusters').textContent = clusters;
            document.getElementById('statAnalysisTime').textContent = totalTime > 0 ? fmtTime(totalTime) : '—';

            // Pipeline status
            updatePipeline(running.length > 0 ? running[0] : null);

            // Recent jobs
            const list = document.getElementById('recentJobsList');
            if (jobs.length === 0) {
                list.innerHTML = '<div class="empty-state"><p>No analyses yet. Enter a YouTube URL above.</p></div>';
            } else {
                list.innerHTML = jobs.slice(0, 8).map(j => `
                    <a href="?page=status&job_id=${j.job_id}" class="job-item">
                        <span class="job-title" style="flex:1;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${esc(j.video_title || 'Untitled')}</span>
                        <span style="font-size:0.8rem;padding:2px 10px;border-radius:100px;background:rgba(255,255,255,0.05);">${j.status}</span>
                        <span style="font-size:0.82rem;color:var(--text-muted);">${Math.round(j.progress || 0)}%</span>
                    </a>
                `).join('');
            }

            // Load latest completed result for charts
            if (completed.length > 0) {
                const latest = completed[0];
                loadResultCharts(latest.job_id);
            }
        });
}

function updatePipeline(runningJob) {
    const bar = document.getElementById('pipelineBar');
    const text = document.getElementById('pipelineText');
    const steps = document.querySelectorAll('.pipeline-step');

    if (!runningJob) {
        bar.style.width = '0%';
        text.textContent = 'Idle — Submit a URL to begin';
        steps.forEach(s => s.classList.remove('completed', 'active'));
        return;
    }

    const statusMap = {
        'queued': 0, 'pending': 0, 'extracting': 1,
        'embedding': 2, 'clustering': 3, 'analyzing': 4,
        'finalizing': 5, 'completed': 5
    };
    const idx = statusMap[runningJob.status] ?? 0;

    bar.style.width = Math.round((idx / 5) * 100) + '%';
    text.textContent = `Processing — ${runningJob.video_title || 'Untitled'} (${runningJob.status})`;

    steps.forEach((s, i) => {
        s.classList.remove('completed', 'active');
        if (i < idx) s.classList.add('completed');
        else if (i === idx) s.classList.add('active');
    });
}

function loadResultCharts(jobId) {
    apiGet('result', { job_id: jobId })
        .then(data => {
            const r = data.result || data;
            const clusters = r.clusters || [];
            const features = r.top_features || [];
            const competitors = r.top_terms || r.competitors || [];
            const purchaseIntent = r.purchase_intent || {};
            const painPoints = r.pain_points || [];
            const opportunities = r.business_opportunities || [];
            const videoIdeas = r.future_video_ideas || [];

            // ── Feature Bars ──
            if (features.length) {
                const maxMentions = Math.max(...features.map(f => f.mentions), 1);
                document.getElementById('featureBars').innerHTML = features.slice(0, 6).map(f => `
                    <div class="feature-bar-row">
                        <span class="feature-bar-label">${esc(f.feature)}</span>
                        <div class="feature-bar-track">
                            <div class="feature-bar-fill" style="width:${(f.mentions / maxMentions * 100).toFixed(0)}%"></div>
                        </div>
                        <span class="feature-bar-count">${f.mentions}</span>
                    </div>
                `).join('');
            }

            // ── Sentiment Chart ──
            const totalSize = clusters.reduce((s, c) => s + (c.size || 0), 0) || 1;
            const avgPos = clusters.reduce((s, c) => s + (c.sentiment_positive_pct || 0) * (c.size || 0), 0) / totalSize;
            const avgNeg = clusters.reduce((s, c) => s + (c.sentiment_negative_pct || 0) * (c.size || 0), 0) / totalSize;
            const avgNeu = 100 - avgPos - avgNeg;

            // Center text
            const centerVal = document.getElementById('sentimentCenterValue');
            const centerLabel = document.getElementById('sentimentCenterLabel');
            if (centerVal) centerVal.textContent = Math.round(avgPos) + '%';
            if (centerLabel) centerLabel.textContent = 'Positive';

            const sentChart = echarts.init(document.getElementById('sentimentChart'));
            sentChart.setOption({
                tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
                series: [{
                    type: 'pie',
                    radius: ['55%', '80%'],
                    avoidLabelOverlap: true,
                    center: ['50%', '55%'],
                    label: { show: false },
                    emphasis: { scale: false },
                    data: [
                        { name: 'Positive', value: Math.round(avgPos), itemStyle: { color: '#6CD4A0' } },
                        { name: 'Negative', value: Math.round(avgNeg), itemStyle: { color: '#E86868' } },
                        { name: 'Neutral', value: Math.round(avgNeu), itemStyle: { color: 'rgba(255,255,255,0.1)' } },
                    ],
                }],
                backgroundColor: 'transparent',
            });

            // ── Purchase Intent Gauge ──
            const score = purchaseIntent.level === 'high' ? 85 : purchaseIntent.level === 'medium' ? 55 : 20;
            const gaugeVal = document.getElementById('gaugeValue');
            const gaugeLabel = document.getElementById('gaugeLabel');
            const gaugeNeedle = document.getElementById('gaugeNeedle');
            const gaugeArc = document.getElementById('gaugeArc');

            if (gaugeVal) gaugeVal.textContent = purchaseIntent.count || '—';
            if (gaugeLabel) gaugeLabel.textContent = `Purchase Intent: ${purchaseIntent.level || 'N/A'}`;
            if (gaugeNeedle) {
                const rot = -90 + (score / 100) * 180;
                gaugeNeedle.style.transform = `rotate(${rot}deg)`;
            }
            if (gaugeArc) {
                const offset = 310 - (score / 100) * 220;
                gaugeArc.setAttribute('stroke-dashoffset', offset);
            }

            // ── Trending Terms ──
            if (competitors.length) {
                const maxComp = Math.max(...competitors.map(c => c.mentions), 1);
                document.getElementById('competitorList').innerHTML = competitors.slice(0, 6).map(c => `
                    <div class="competitor-item">
                        <div class="competitor-logo">${esc(c.name.charAt(0))}</div>
                        <span class="competitor-name">${esc(c.name)}</span>
                        <div class="competitor-bar">
                            <div class="competitor-bar-fill" style="width:${(c.mentions / maxComp * 100).toFixed(0)}%"></div>
                        </div>
                        <span class="competitor-count">${c.mentions}</span>
                    </div>
                `).join('');
            }

            // ── Insight Cards with ML fallback ──
            const aiHint = '<span style="color:var(--text-gold);font-size:0.7rem;display:block;margin-top:2px;">Enable AI for deeper analysis</span>';
            if (painPoints.length) {
                document.getElementById('insightPainPoints').innerHTML = painPoints.slice(0, 5).map((p, i) =>
                    `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${esc(p.pain)}</li>`
                ).join('') + (painPoints[0] && !painPoints[0].pain.includes('sentiment') ? '' : '') + /* show AI hint only on ML-derived */ '';
            } else {
                document.getElementById('insightPainPoints').innerHTML = '<li style="color:var(--text-muted);font-size:0.78rem;">No pain points detected' + aiHint + '</li>';
            }
            if (features.length) {
                document.getElementById('insightFeatures').innerHTML = features.slice(0, 5).map((f, i) =>
                    `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${esc(f.feature)} <span style="color:var(--text-muted);font-size:0.75rem;">(${f.mentions})</span></li>`
                ).join('');
            }
            if (opportunities.length) {
                document.getElementById('insightOpportunities').innerHTML = opportunities.slice(0, 5).map((o, i) =>
                    `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${esc(o.opportunity)}</li>`
                ).join('') + (opportunities[0] && !opportunities[0].opportunity.includes('cluster') ? '' : '') + '';
            } else {
                document.getElementById('insightOpportunities').innerHTML = '<li style="color:var(--text-muted);font-size:0.78rem;">No opportunities detected' + aiHint + '</li>';
            }
            if (videoIdeas.length) {
                document.getElementById('insightVideos').innerHTML = videoIdeas.slice(0, 5).map((v, i) =>
                    `<li class="${i === 0 ? 'gold-accent' : ''}"><span class="insight-bullet"></span>${esc(v.idea)} <span style="color:var(--text-gold);font-size:0.75rem;font-weight:600;">${v.demand_score}</span></li>`
                ).join('');
            } else {
                document.getElementById('insightVideos').innerHTML = '<li style="color:var(--text-muted);font-size:0.78rem;">No video ideas yet' + aiHint + '</li>';
            }
        })
        .catch(() => {});
}

// ── Init ──
loadDashboard();
loadMLPipelineStatus();
loadAIEngineStatus();
setInterval(loadMLPipelineStatus, 30000);
setInterval(loadAIEngineStatus, 15000);
</script>
