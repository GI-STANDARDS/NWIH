<?php
$jobId = $_GET['job_id'] ?? '';
?>
<div class="page-header-inline">
    <div>
        <h1>Live Processing</h1>
        <p>Real-time AI processing and debug logs.</p>
    </div>
</div>

<?php if ($jobId): ?>
<div class="glass-card" id="jobStatusCard">
    <div class="cluster-header" style="margin-bottom:16px;">
        <h3 id="jobTitle" style="font-size:1.1rem;font-weight:600;">Loading...</h3>
        <span class="badge" id="jobStatusBadge">pending</span>
        <span id="jobStage" style="font-size:0.75rem;color:var(--text-muted);margin-left:8px;">-</span>
    </div>

    <div class="progress-container progress-scan">
        <div class="progress-bar" id="progressBar" style="width:0%"></div>
    </div>
    <p class="progress-text" id="progressText">0%</p>

    <div class="stats-grid" style="grid-template-columns:repeat(4,1fr);margin-top:16px;margin-bottom:0;">
        <div class="stat-glass" style="padding:14px;">
            <div class="stat-value-gold" style="font-size:1.4rem;" id="statExtracted">0</div>
            <div class="stat-label">Extracted</div>
        </div>
        <div class="stat-glass" style="padding:14px;">
            <div class="stat-value-green" style="font-size:1.4rem;" id="statEmbedded">0</div>
            <div class="stat-label">Embedded</div>
        </div>
        <div class="stat-glass" style="padding:14px;">
            <div class="stat-value-blue" style="font-size:1.4rem;" id="statClusters">0</div>
            <div class="stat-label">Clusters</div>
        </div>
        <div class="stat-glass" style="padding:14px;">
            <div class="stat-value-purple" style="font-size:1.4rem;" id="statSpeed">0/s</div>
            <div class="stat-label">Speed</div>
        </div>
    </div>

    <div id="jobActions" style="display:none; margin-top:16px;">
        <a href="?page=results&job_id=<?= htmlspecialchars($jobId) ?>" class="btn btn-primary">
            View Results
        </a>
        <button onclick="location.reload()" class="btn">Refresh</button>
    </div>

    <div id="jobError" style="display:none;" class="alert error"></div>
</div>

<div class="glass-card" style="margin-top:16px;">
    <div class="glass-card-title">
        <span>🔍 Debug Log</span>
        <button onclick="clearDebugLog()" class="btn" style="font-size:0.7rem;padding:2px 8px;">Clear</button>
    </div>
    <div id="debugLog" style="font-family:'Courier New',monospace;font-size:0.75rem;max-height:300px;overflow-y:auto;padding:12px;background:rgba(0,0,0,0.3);border-radius:8px;">
        <div class="text-muted">Connecting to debug stream...</div>
    </div>
</div>
<?php else: ?>
<div class="glass-card">
    <div class="glass-card-title">All Jobs</div>
    <div id="allJobsList"><p class="text-muted">Loading...</p></div>
</div>
<?php endif; ?>

<script>
<?php if ($jobId): ?>
const JOB_ID = '<?= htmlspecialchars($jobId) ?>';
let eventSource = null;

function connectSSE() {
    const debugLog = document.getElementById('debugLog');
    debugLog.innerHTML = '<div class="text-muted">Connecting to live stream...</div>';
    
    eventSource = new EventSource('http://127.0.0.1:8000/stream/' + JOB_ID);
    
    eventSource.addEventListener('activity', function(e) {
        const data = JSON.parse(e.data);
        addDebugLog(data.emoji + ' ' + data.message, 'activity');
    });
    
    eventSource.addEventListener('progress', function(e) {
        const data = JSON.parse(e.data);
        document.getElementById('progressBar').style.width = data.progress + '%';
        document.getElementById('progressText').textContent = Math.round(data.progress) + '%';
    });
    
    eventSource.addEventListener('stage', function(e) {
        const data = JSON.parse(e.data);
        document.getElementById('jobStage').textContent = data.stage;
        addDebugLog('Stage: ' + data.stage, 'stage');
    });
    
    eventSource.addEventListener('counter', function(e) {
        const data = JSON.parse(e.data);
        if (data.name === 'comments_extracted') {
            document.getElementById('statExtracted').textContent = data.value.toLocaleString();
        } else if (data.name === 'comments_embedded') {
            document.getElementById('statEmbedded').textContent = data.value.toLocaleString();
        }
    });
    
    eventSource.addEventListener('metrics', function(e) {
        const data = JSON.parse(e.data);
        if (data.process_speed) {
            document.getElementById('statSpeed').textContent = Math.round(data.process_speed) + '/s';
        }
    });
    
    eventSource.addEventListener('done', function(e) {
        const data = JSON.parse(e.data);
        addDebugLog('Job ' + data.status + ': ' + data.job_id, data.status === 'completed' ? 'success' : 'error');
        eventSource.close();
        loadJobStatus();
    });
    
    eventSource.addEventListener('heartbeat', function(e) {
        // Keep connection alive
    });
    
    eventSource.onerror = function() {
        addDebugLog('Connection lost, retrying...', 'error');
        setTimeout(connectSSE, 3000);
    };
}

function loadJobStatus() {
    fetch('api.php?action=status&job_id=' + JOB_ID)
        .then(r => r.json())
        .then(job => {
            document.getElementById('jobTitle').textContent = job.video_title || 'Untitled';
            document.getElementById('jobStatusBadge').textContent = job.status;
            document.getElementById('jobStatusBadge').className = 'badge ' + job.status;

            const progress = Math.round(job.progress || 0);
            document.getElementById('progressBar').style.width = progress + '%';
            document.getElementById('progressText').textContent = progress + '%';

            document.getElementById('statExtracted').textContent = (job.comments_extracted || 0).toLocaleString();
            document.getElementById('statEmbedded').textContent = (job.comments_embedded || 0).toLocaleString();
            document.getElementById('statClusters').textContent = (job.clusters_found || 0).toLocaleString();

            if (job.status === 'completed') {
                document.getElementById('jobActions').style.display = 'block';
                document.getElementById('progressText').textContent = 'Complete!';
                return;
            }

            if (job.status === 'error') {
                document.getElementById('jobError').style.display = 'block';
                document.getElementById('jobError').textContent = 'Error: ' + (job.error || 'Unknown error');
                return;
            }
        });
}

function addDebugLog(message, type = 'info') {
    const debugLog = document.getElementById('debugLog');
    const time = new Date().toLocaleTimeString();
    const colors = {
        'activity': 'var(--text-gold)',
        'stage': 'var(--text-blue)',
        'success': 'var(--green)',
        'error': 'var(--red)',
        'info': 'var(--text-muted)'
    };
    
    const entry = document.createElement('div');
    entry.style.color = colors[type] || colors.info;
    entry.innerHTML = `<span style="color:var(--text-muted)">[${time}]</span> ${message}`;
    debugLog.appendChild(entry);
    debugLog.scrollTop = debugLog.scrollHeight;
    
    // Keep last 100 entries
    while (debugLog.children.length > 100) {
        debugLog.removeChild(debugLog.firstChild);
    }
}

function clearDebugLog() {
    document.getElementById('debugLog').innerHTML = '<div class="text-muted">Log cleared</div>';
}

// Start SSE connection
connectSSE();
loadJobStatus();
<?php endif; ?>

function loadAllJobs() {
    fetch('api.php?action=jobs')
        .then(r => r.json())
        .then(jobs => {
            const list = document.getElementById('allJobsList');
            if (!list) return;
            if (jobs.length === 0) {
                list.innerHTML = '<p class="muted">No jobs yet. <a href="?page=analyze">Analyze a video</a></p>';
            } else {
                list.innerHTML = jobs.map(j => `
                    <a href="?page=status&job_id=${j.job_id}" class="job-item ${j.status}">
                        <span class="job-title">${escapeHtml(j.video_title || 'Untitled')}</span>
                        <span class="job-status">${j.status}</span>
                        <span class="job-progress">${Math.round(j.progress || 0)}%</span>
                        <span class="job-comments">${(j.comments_extracted || 0).toLocaleString()} comments</span>
                    </a>
                `).join('');
            }
        });
}

if (!JOB_ID) loadAllJobs();

function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}
</script>
