<div class="page-header-inline">
    <div>
        <h1>Analyze YouTube Content</h1>
        <p>Extract and analyze up to 1M comments from any YouTube video, playlist, or channel.</p>
    </div>
</div>

<div id="analysisForm" class="glass-card" style="max-width:800px; margin:0 auto;">
    <form id="analyzeForm">
        <div class="form-group">
            <label for="youtubeUrl">YouTube URL</label>
            <input type="text" id="youtubeUrl" name="youtube_url"
                   placeholder="https://www.youtube.com/watch?v=... or playlist/channel URL"
                   required class="input-main" style="width:100%;">
        </div>

        <div class="form-row">
            <div class="form-group">
                <label for="sourceType">Source Type</label>
                <select id="sourceType" name="source_type" class="input-main">
                    <option value="video">Single Video</option>
                    <option value="playlist">Playlist</option>
                    <option value="channel">Channel</option>
                </select>
            </div>
            <div class="form-group">
                <label for="maxComments">Max Comments</label>
                <select id="maxComments" name="max_comments" class="input-main">
                    <option value="10000">10,000</option>
                    <option value="50000" selected>50,000</option>
                    <option value="100000">100,000</option>
                    <option value="500000">500,000</option>
                    <option value="1000000">1,000,000</option>
                </select>
            </div>
        </div>

        <div class="form-group">
            <label>Or enter multiple URLs (one per line):</label>
            <textarea id="batchUrls" rows="4" class="input-main" style="width:100%;"
                      placeholder="https://youtube.com/watch?v=...&#10;https://youtube.com/watch?v=..."></textarea>
        </div>

        <button type="submit" class="btn btn-primary" style="width:100%;">
            Start Analysis
        </button>
    </form>
    <div id="analyzeResult" style="margin-top:16px;"></div>
</div>

<!-- Live Processing Dashboard (hidden initially) -->
<div id="liveDashboard" class="glass-card" style="max-width:900px; margin:20px auto; display:none;">
    <!-- Header -->
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div>
            <h2 id="jobTitle" style="margin:0;">Processing...</h2>
            <small id="jobIdDisplay" style="color:var(--text-muted);"></small>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button id="cancelBtn" class="btn btn-danger" onclick="cancelJob()" style="display:none;">Cancel</button>
            <a id="viewResultsBtn" href="#" class="btn btn-primary" style="display:none;">View Results</a>
            <a id="aiAnalyzeLink" href="#" class="btn" style="display:none;background:linear-gradient(135deg,#89b4fa,#74c7ec);color:#1e1e2e;border:none;font-weight:600;">🤖 AI Analysis →</a>
        </div>
    </div>

    <!-- Progress Bar -->
    <div style="margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; font-size:13px; margin-bottom:4px;">
            <span id="stageLabel" style="color:var(--text-gold);">Initializing...</span>
            <span id="progressPct">0%</span>
        </div>
        <div class="progress-bar-track">
            <div id="progressBarFill" class="progress-bar-fill" style="width:0%;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; margin-top:4px;">
            <span id="elapsedTime" style="color:var(--text-muted);">Elapsed: 0s</span>
            <span id="etaDisplay" style="color:var(--text-muted);">ETA: --</span>
        </div>
    </div>

    <!-- Live Counters -->
    <div class="counter-grid">
        <div class="counter-card">
            <div class="counter-value" id="counterDownloaded">0</div>
            <div class="counter-label">Downloaded</div>
        </div>
        <div class="counter-card">
            <div class="counter-value" id="counterProcessed">0</div>
            <div class="counter-label">Processed</div>
        </div>
        <div class="counter-card">
            <div class="counter-value" id="counterAnalyzed">0</div>
            <div class="counter-label">Analyzed</div>
        </div>
        <div class="counter-card">
            <div class="counter-value" id="counterFailed" style="color:#e74c3c;">0</div>
            <div class="counter-label">Failed</div>
        </div>
        <div class="counter-card">
            <div class="counter-value" id="counterSkipped" style="color:#f39c12;">0</div>
            <div class="counter-label">Skipped</div>
        </div>
        <div class="counter-card">
            <div class="counter-value" id="counterRemaining">0</div>
            <div class="counter-label">Remaining</div>
        </div>
    </div>

    <!-- Metrics + Activity -->
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px;">
        <!-- Metrics Panel -->
        <div class="metrics-panel" style="background:var(--bg-secondary); border-radius:8px; padding:12px;">
            <h4 style="margin:0 0 8px; font-size:14px;">Performance Metrics</h4>
            <table style="width:100%; font-size:13px;">
                <tr>
                    <td style="padding:3px 0; color:var(--text-muted);">Download Speed</td>
                    <td style="text-align:right;" id="metricDownloadSpeed">--</td>
                </tr>
                <tr>
                    <td style="padding:3px 0; color:var(--text-muted);">Process Speed</td>
                    <td style="text-align:right;" id="metricProcessSpeed">--</td>
                </tr>
                <tr>
                    <td style="padding:3px 0; color:var(--text-muted);">Memory</td>
                    <td style="text-align:right;" id="metricMemory">--</td>
                </tr>
                <tr>
                    <td style="padding:3px 0; color:var(--text-muted);">CPU</td>
                    <td style="text-align:right;" id="metricCpu">--</td>
                </tr>
            </table>
        </div>

        <!-- Activity Feed -->
        <div class="activity-panel" style="background:var(--bg-secondary); border-radius:8px; padding:12px; max-height:200px; overflow-y:auto;">
            <h4 style="margin:0 0 8px; font-size:14px;">Activity Log</h4>
            <div id="activityFeed" style="font-size:12px;"></div>
        </div>
    </div>
</div>

<!-- Pipeline Stages (static guide) -->
<div id="pipelineGuide" class="section" style="max-width:800px; margin:20px auto;">
    <h2>Pipeline Stages</h2>
    <div class="steps">
        <div class="step"><strong>1</strong> Extract — Batched comment download (500/batch)</div>
        <div class="step"><strong>2</strong> Clean — Spam removal, language detection, normalization</div>
        <div class="step"><strong>3</strong> Embed — BGE sentence embeddings via FAISS vector store</div>
        <div class="step"><strong>4</strong> Cluster — HDBSCAN groups similar comments</div>
        <div class="step" style="opacity:0.6;"><strong style="color:var(--text-gold);">AI</strong> LLM Analyze — <em>Optional:</em> llama.cpp AI summaries (requires GGUF)</div>
        <div class="step"><strong>5</strong> Report — Demand scores, topics, and opportunities (ML-based)</div>
    </div>
</div>

<style>
.progress-bar-track {
    width:100%; height:20px; background:var(--bg-secondary); border-radius:10px; overflow:hidden;
}
.progress-bar-fill {
    height:100%; background: linear-gradient(90deg, #3498db, #2ecc71); border-radius:10px;
    transition: width 0.5s ease;
}
.counter-grid {
    display:grid; grid-template-columns: repeat(6, 1fr); gap:8px; margin-top:12px;
}
.counter-card {
    background:var(--bg-secondary); border-radius:8px; padding:10px; text-align:center;
}
.counter-value {
    font-size:24px; font-weight:700; color:var(--text-gold);
}
.counter-label {
    font-size:11px; color:var(--text-muted); margin-top:2px;
}
.activity-entry {
    padding:3px 0; border-bottom:1px solid rgba(255,255,255,0.05);
    display:flex; gap:6px; align-items:flex-start;
}
.activity-entry .act-icon { flex-shrink:0; }
.activity-entry .act-msg { word-break:break-word; }
.activity-entry .act-time { color:var(--text-muted); font-size:10px; white-space:nowrap; }
</style>

<script>
// SSE EventSource wrapper for live streaming
let eventSource = null;
let currentJobId = null;
let lastSeq = 0;
let reconnectTimer = null;
let startTime = null;

function connectSSE(jobId) {
    if (eventSource) {
        eventSource.close();
    }
    currentJobId = jobId;
    startTime = Date.now();
    lastSeq = 0;

    // Show dashboard
    document.getElementById('analysisForm').style.display = 'none';
    document.getElementById('pipelineGuide').style.display = 'none';
    document.getElementById('liveDashboard').style.display = 'block';
    document.getElementById('cancelBtn').style.display = 'inline-block';
    document.getElementById('viewResultsBtn').style.display = 'none';
    document.getElementById('jobIdDisplay').textContent = 'Job: ' + jobId;
    document.getElementById('stageLabel').textContent = 'Connecting...';
    document.getElementById('progressBarFill').style.width = '0%';
    document.getElementById('progressPct').textContent = '0%';

    const url = 'http://127.0.0.1:8000/stream/' + jobId;
    eventSource = new EventSource(url);

    eventSource.addEventListener('stage', function(e) {
        const data = JSON.parse(e.data);
        document.getElementById('stageLabel').textContent = data.stage_label || data.stage;
    });

    eventSource.addEventListener('progress', function(e) {
        const data = JSON.parse(e.data);
        const pct = Math.round(data.progress);
        document.getElementById('progressBarFill').style.width = pct + '%';
        document.getElementById('progressPct').textContent = pct + '%';
    });

    eventSource.addEventListener('counter', function(e) {
        const data = JSON.parse(e.data);
        if (data.comments_downloaded !== undefined)
            updateCounter('counterDownloaded', data.comments_downloaded);
        if (data.comments_processed !== undefined)
            updateCounter('counterProcessed', data.comments_processed);
        if (data.comments_analyzed !== undefined)
            updateCounter('counterAnalyzed', data.comments_analyzed);
        if (data.comments_failed !== undefined)
            updateCounter('counterFailed', data.comments_failed);
        if (data.comments_skipped !== undefined)
            updateCounter('counterSkipped', data.comments_skipped);
        if (data.comments_remaining !== undefined)
            updateCounter('counterRemaining', data.comments_remaining);
    });

    eventSource.addEventListener('metrics', function(e) {
        const data = JSON.parse(e.data);
        if (data.download_speed) document.getElementById('metricDownloadSpeed').textContent = data.download_speed + '/s';
        if (data.process_speed) document.getElementById('metricProcessSpeed').textContent = data.process_speed + '/s';
        if (data.memory_mb) document.getElementById('metricMemory').textContent = data.memory_mb + ' MB';
        if (data.cpu_percent) document.getElementById('metricCpu').textContent = data.cpu_percent + '%';
    });

    eventSource.addEventListener('activity', function(e) {
        const data = JSON.parse(e.data);
        addActivity(data.icon || '•', data.message, data.timestamp);
    });

    eventSource.addEventListener('status', function(e) {
        const data = JSON.parse(e.data);
        if (data.status === 'completed') {
            document.getElementById('stageLabel').textContent = '✅ Completed!';
            document.getElementById('progressBarFill').style.width = '100%';
            document.getElementById('progressPct').textContent = '100%';
            document.getElementById('cancelBtn').style.display = 'none';
        } else if (data.status === 'error') {
            document.getElementById('stageLabel').textContent = '❌ Error';
            document.getElementById('cancelBtn').style.display = 'none';
        }
    });

    eventSource.addEventListener('error', function(e) {
        const data = JSON.parse(e.data);
        document.getElementById('stageLabel').textContent = '❌ Error: ' + (data.error || 'Unknown error');
        document.getElementById('cancelBtn').style.display = 'none';
        addActivity('❌', 'Error: ' + (data.error || 'Unknown error'));
    });

    eventSource.addEventListener('result', function(e) {
        const data = JSON.parse(e.data);
        document.getElementById('viewResultsBtn').href = '?page=results&job_id=' + data.job_id;
        document.getElementById('viewResultsBtn').style.display = 'inline-block';
        document.getElementById('aiAnalyzeLink').href = '?page=ai_analysis&job_id=' + encodeURIComponent(data.job_id);
        document.getElementById('aiAnalyzeLink').style.display = 'inline-block';
        document.getElementById('cancelBtn').style.display = 'none';
        document.getElementById('stageLabel').textContent = '✅ Completed!';
        document.getElementById('progressBarFill').style.width = '100%';
        document.getElementById('progressPct').textContent = '100%';
        addActivity('🎉', 'Report ready! Click "View Results" to see the analysis.');
    });

    eventSource.addEventListener('done', function(e) {
        eventSource.close();
    });

    eventSource.addEventListener('heartbeat', function(e) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        document.getElementById('elapsedTime').textContent = 'Elapsed: ' + formatTime(elapsed);
        if (eventSource.readyState === EventSource.CLOSED) {
            // Try to reconnect
            scheduleReconnect(jobId);
        }
    });

    eventSource.onerror = function() {
        // Will attempt to reconnect via heartbeat timeout
    };
}

function scheduleReconnect(jobId) {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(function() {
        connectSSE(jobId);
    }, 2000);
}

function updateCounter(id, value) {
    const el = document.getElementById(id);
    if (el) {
        // Animate counting up
        const current = parseInt(el.textContent.replace(/,/g, '')) || 0;
        if (value > current) {
            animateNumber(el, current, value);
        } else {
            el.textContent = formatNumber(value);
        }
    }
}

function animateNumber(el, from, to) {
    const duration = 300;
    const start = performance.now();
    function step(now) {
        const pct = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - pct, 3);
        const val = Math.round(from + (to - from) * eased);
        el.textContent = formatNumber(val);
        if (pct < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function addActivity(icon, message, timestamp) {
    const feed = document.getElementById('activityFeed');
    const entry = document.createElement('div');
    entry.className = 'activity-entry';
    const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
    entry.innerHTML = '<span class="act-time">' + timeStr + '</span>' +
        '<span class="act-icon">' + icon + '</span>' +
        '<span class="act-msg">' + escapeHtml(message) + '</span>';
    feed.appendChild(entry);
    feed.scrollTop = feed.scrollHeight;
    // Keep max 200 entries
    while (feed.children.length > 200) {
        feed.removeChild(feed.firstChild);
    }
}

function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
}

function formatTime(seconds) {
    if (seconds < 60) return seconds + 's';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m + 'm ' + s + 's';
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function cancelJob() {
    if (!currentJobId || !confirm('Cancel this analysis?')) return;
    fetch('api.php?action=cancel_job&job_id=' + currentJobId)
        .then(r => r.json())
        .then(data => {
            addActivity('⏹', 'Cancellation requested. Cleaning up...');
            document.getElementById('cancelBtn').disabled = true;
            document.getElementById('cancelBtn').textContent = 'Cancelling...';
        })
        .catch(err => {
            addActivity('❌', 'Failed to cancel: ' + err.message);
        });
}

// ─── Form Submission ──────────────────────────────────────────────────────
document.getElementById('analyzeForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const resultDiv = document.getElementById('analyzeResult');
    const url = document.getElementById('youtubeUrl').value;
    const batchUrls = document.getElementById('batchUrls').value.trim();
    const sourceType = document.getElementById('sourceType').value;
    const maxComments = document.getElementById('maxComments').value;

    resultDiv.innerHTML = '<div class="spinner"></div> Starting analysis...';

    if (batchUrls) {
        const urls = batchUrls.split('\n').filter(u => u.trim());
        fetch('api.php?action=analyze_batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ urls: urls, max_comments_per_video: parseInt(maxComments) })
        })
        .then(r => r.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                resultDiv.innerHTML = '<div class="alert success">' + data.results.length + ' batch jobs created.<br>View progress for each job:</div>';
                data.results.forEach(function(r) {
                    if (r.job_id) {
                        const link = document.createElement('a');
                        link.href = '#';
                        link.textContent = r.job_id.slice(0, 8) + '... (' + (r.video_id || r.url) + ')';
                        link.onclick = function(ev) { ev.preventDefault(); connectSSE(r.job_id); };
                        resultDiv.appendChild(document.createElement('br'));
                        resultDiv.appendChild(link);
                    }
                });
            } else {
                resultDiv.innerHTML = '<div class="alert error">Error: ' + JSON.stringify(data) + '</div>';
            }
        });
    } else {
        let endpoint = 'analyze';
        let payload = { youtube_url: url, max_comments: parseInt(maxComments), source_type: sourceType };

        if (sourceType === 'channel') {
            endpoint = 'analyze_channel';
            payload = { channel_url: url, max_videos: 10, max_comments_per_video: parseInt(maxComments) };
        } else if (sourceType === 'playlist') {
            endpoint = 'analyze_playlist';
            payload = { playlist_url: url, max_videos: 10, max_comments_per_video: parseInt(maxComments) };
        }

        fetch('api.php?action=' + endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(data => {
            if (data.job_id) {
                // Single job - connect SSE immediately
                connectSSE(data.job_id);
                if (data.video_title) {
                    document.getElementById('jobTitle').textContent = data.video_title;
                }
                addActivity('🔗', 'Connected to analysis pipeline');
            } else if (data.jobs) {
                // Multiple jobs - show list
                resultDiv.innerHTML = '<div class="alert success">' + data.jobs.length + ' jobs created.<br>Select one to view progress:</div>';
                data.jobs.forEach(function(j) {
                    const link = document.createElement('a');
                    link.href = '#';
                    link.textContent = (j.title || j.video_id || 'Unknown') + ' (' + j.job_id.slice(0, 8) + '...)';
                    link.style.display = 'block';
                    link.style.margin = '4px 0';
                    link.onclick = function(ev) { ev.preventDefault(); connectSSE(j.job_id); };
                    resultDiv.appendChild(link);
                });
            } else {
                resultDiv.innerHTML = '<div class="alert error">Error: ' + JSON.stringify(data) + '</div>';
            }
        })
        .catch(err => {
            resultDiv.innerHTML = '<div class="alert error">Connection error: ' + err.message + '</div>';
        });
    }
});

// Check URL params for auto-connect
(function() {
    const params = new URLSearchParams(window.location.search);
    const jobId = params.get('job_id');
    if (jobId) {
        // Fetch job info
        fetch('api.php?action=status&job_id=' + jobId)
            .then(r => r.json())
            .then(data => {
                if (data.status === 'completed') {
                    document.getElementById('analysisForm').style.display = 'none';
                    document.getElementById('pipelineGuide').style.display = 'none';
                    document.getElementById('liveDashboard').style.display = 'block';
                    document.getElementById('cancelBtn').style.display = 'none';
                    document.getElementById('viewResultsBtn').href = '?page=results&job_id=' + jobId;
                    document.getElementById('viewResultsBtn').style.display = 'inline-block';
                    document.getElementById('aiAnalyzeLink').href = '?page=ai_analysis&job_id=' + encodeURIComponent(jobId);
                    document.getElementById('aiAnalyzeLink').style.display = 'inline-block';
                    document.getElementById('stageLabel').textContent = '✅ Completed!';
                    document.getElementById('progressBarFill').style.width = '100%';
                    document.getElementById('progressPct').textContent = '100%';
                    document.getElementById('jobIdDisplay').textContent = 'Job: ' + jobId;
                    if (data.video_title) {
                        document.getElementById('jobTitle').textContent = data.video_title;
                    }
                    return;
                }
                if (data.status !== 'error' && data.status !== 'completed') {
                    connectSSE(jobId);
                    if (data.video_title) {
                        document.getElementById('jobTitle').textContent = data.video_title;
                    }
                }
            })
            .catch(function() {});
    }
})();
</script>
