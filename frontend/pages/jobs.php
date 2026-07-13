<div class="page-header-inline">
    <div>
        <h1> Jobs History</h1>
        <p>Manage, pause, delete, or restart analysis jobs</p>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn btn-primary" onclick="loadJobs()"> Refresh</button>
        <span id="jobsCount" style="font-size:0.82rem;color:var(--text-muted);"></span>
    </div>
</div>

<div class="glass-card">
    <div id="jobsContainer" style="min-height:200px;">
        <p class="text-muted" style="padding:30px;text-align:center;">Loading jobs...</p>
    </div>
</div>

<div id="confirmModal" class="modal-overlay" style="display:none;">
    <div class="modal-box">
        <h3 id="modalTitle">Confirm</h3>
        <p id="modalMessage" style="margin:12px 0;font-size:0.9rem;"></p>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
            <button class="btn" onclick="closeModal()">Cancel</button>
            <button class="btn btn-danger" id="modalConfirmBtn" onclick="">Confirm</button>
        </div>
    </div>
</div>

<style>
.job-row { display:flex; align-items:center; padding:12px 14px; border-bottom:1px solid var(--glass-border); gap:12px; transition:background 0.2s; }
.job-row:hover { background:rgba(255,255,255,0.03); }
.job-row:last-child { border-bottom:none; }
.job-status-badge { display:inline-block; padding:2px 10px; border-radius:10px; font-size:0.7rem; font-weight:600; text-transform:uppercase; min-width:80px; text-align:center; }
.job-status-badge.queued, .job-status-badge.pending { background:rgba(100,140,255,0.15); color:#6490ff; }
.job-status-badge.processing, .job-status-badge.extracting, .job-status-badge.embedding, .job-status-badge.clustering, .job-status-badge.finalizing { background:rgba(255,200,50,0.15); color:#ffc832; }
.job-status-badge.completed { background:rgba(80,220,120,0.15); color:#50dc78; }
.job-status-badge.error { background:rgba(232,104,104,0.15); color:#e86868; }
.job-status-badge.cancelled { background:rgba(160,160,160,0.15); color:#a0a0a0; }
.job-status-badge.paused { background:rgba(255,160,60,0.15); color:#ffa03c; }
.job-title { flex:1; min-width:0; }
.job-title strong { font-size:0.85rem; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.job-title small { font-size:0.7rem; color:var(--text-muted); }
.job-progress { width:100px; }
.job-progress .progress-container { height:4px; background:rgba(255,255,255,0.08); border-radius:2px; overflow:hidden; }
.job-progress .progress-bar { height:100%; border-radius:2px; transition:width 0.5s; }
.job-actions { display:flex; gap:4px; flex-shrink:0; }
.job-actions .btn { padding:2px 10px; font-size:0.7rem; }
.job-time { font-size:0.68rem; color:var(--text-muted); min-width:100px; text-align:right; }
.modal-overlay { position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.6); z-index:1000; display:flex; align-items:center; justify-content:center; }
.modal-box { background:var(--bg-card); border:1px solid var(--glass-border); border-radius:12px; padding:24px; max-width:400px; width:90%; }
.btn-danger { background:rgba(232,104,104,0.2); color:#e86868; border-color:rgba(232,104,104,0.3); }
.btn-danger:hover { background:rgba(232,104,104,0.35); }
.btn-danger:active { background:rgba(232,104,104,0.4); }

</style>

<script>
let jobsData = [];
let modalCallback = null;

function loadJobs() {
    const container = document.getElementById('jobsContainer');
    container.innerHTML = '<p class="text-muted" style="padding:30px;text-align:center;">Loading jobs...</p>';

    apiGet('jobs').then(data => {
        jobsData = Array.isArray(data) ? data : [];
        document.getElementById('jobsCount').textContent = jobsData.length + ' jobs';
        renderJobs(jobsData);
    }).catch(() => {
        container.innerHTML = '<p class="text-red" style="padding:30px;text-align:center;">Failed to load jobs. Is the backend running?</p>';
    });
}

function renderJobs(jobs) {
    const container = document.getElementById('jobsContainer');
    if (jobs.length === 0) {
        container.innerHTML = '<p class="text-muted" style="padding:30px;text-align:center;">No jobs yet. <a href="?page=analyze" style="color:var(--text-gold);">Analyze a video</a> to get started.</p>';
        return;
    }

    const statusColors = {
        queued: '#6490ff', pending: '#6490ff',
        processing: '#ffc832', extracting: '#ffc832', embedding: '#ffc832',
        clustering: '#ffc832', finalizing: '#ffc832',
        completed: '#50dc78',
        error: '#e86868',
        cancelled: '#a0a0a0',
        paused: '#ffa03c'
    };

    container.innerHTML = jobs.map((j, idx) => {
        const status = j.status || 'unknown';
        const color = statusColors[status] || '#a0a0a0';
        const progress = j.progress || 0;
        const time = j.created_at ? j.created_at.replace('T', ' ').split('.')[0].slice(0, 19) : '—';
        const title = j.video_title || j.video_url || 'Unknown video';
        const comments = j.comments_extracted || 0;
        const clusters = j.clusters_found || 0;

        const canPause = ['queued', 'pending', 'processing', 'extracting', 'embedding', 'clustering'].includes(status);
        const canResume = status === 'paused';
        const canProcess = status === 'paused' && comments > 0;
        const canRestart = ['completed', 'error', 'cancelled'].includes(status);
        const canDelete = true;
        const canViewResults = status === 'completed';

        return `<div class="job-row" data-job-id="${esc(j.job_id)}">
            <div class="job-title">
                <strong>${esc(title)}</strong>
                <small>${esc(j.video_url || '')} ${j.channel ? '· ' + esc(j.channel) : ''}</small>
            </div>
            <div class="job-status-badge ${status}">${status}</div>
            <div class="job-progress">
                <div class="progress-container">
                    <div class="progress-bar" style="width:${progress}%;background:${color};"></div>
                </div>
                <div style="font-size:0.65rem;color:var(--text-muted);margin-top:2px;">${comments} comments${clusters ? ' · ' + clusters + ' clusters' : ''}</div>
            </div>
            <div class="job-time">${esc(time)}</div>
            <div class="job-actions">
                ${canViewResults ? `<a href="?page=results&job_id=${esc(j.job_id)}" class="btn" style="padding:2px 10px;font-size:0.7rem;color:var(--green);">Results</a>` : ''}
                ${canViewResults ? `<a href="?page=ai_analysis&job_id=${esc(j.job_id)}" class="btn" style="padding:2px 10px;font-size:0.7rem;color:var(--text-gold);">AI Analysis</a>` : ''}
                ${canViewResults ? `<button class="btn" style="padding:2px 10px;font-size:0.7rem;" onclick="exportText('${esc(j.job_id)}')">Export</button>` : ''}
                ${canPause ? `<button class="btn" onclick="pauseJob('${esc(j.job_id)}')">Pause</button>` : ''}
                ${canProcess ? `<button class="btn btn-primary" onclick="processJob('${esc(j.job_id)}')">Process</button>` : ''}
                ${canResume ? `<button class="btn" onclick="resumeJob('${esc(j.job_id)}')">Resume</button>` : ''}
                ${canRestart ? `<button class="btn" onclick="restartJob('${esc(j.job_id)}')">Restart</button>` : ''}
                ${canDelete ? `<button class="btn" style="color:var(--red);" onclick="deleteJob('${esc(j.job_id)}')">Delete</button>` : ''}
            </div>
        </div>`;
    }).join('');
}

function pauseJob(jobId) {
    showModal('Pause Job', 'Pause this job? It can be resumed later.', () => {
        apiGet('pause_job', { job_id: jobId }).then(() => loadJobs());
        closeModal();
    });
}

function processJob(jobId) {
    apiPost('process_job', { job_id: jobId }).then(() => loadJobs());
}

function resumeJob(jobId) {
    apiGet('resume_job', { job_id: jobId }).then(() => loadJobs());
}

function restartJob(jobId) {
    showModal('Restart Job', 'This will delete all extracted comments and clusters for this job and re-queue it. Continue?', () => {
        apiGet('restart_job', { job_id: jobId }).then(() => loadJobs());
        closeModal();
    });
}

function deleteJob(jobId) {
    showModal('Delete Job', 'Permanently delete this job and all its data? This cannot be undone.', () => {
        apiGet('delete_job', { job_id: jobId }).then(() => loadJobs());
        closeModal();
    });
}

function exportText(jobId) {
    apiGet('export_text', { job_id: jobId }).then(r => {
        showModal('Export Complete', 'Text files saved to RAW_text/ folder.', () => closeModal());
    }).catch(e => {
        showModal('Export Failed', e.toString(), () => closeModal());
    });
}

function showModal(title, message, callback) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalMessage').textContent = message;
    document.getElementById('confirmModal').style.display = 'flex';
    modalCallback = callback;
    document.getElementById('modalConfirmBtn').onclick = callback;
}

function closeModal() {
    document.getElementById('confirmModal').style.display = 'none';
    modalCallback = null;
}

function apiGet(action, params) {
    let url = 'api.php?action=' + action;
    if (params) for (const k in params) url += '&' + k + '=' + encodeURIComponent(params[k]);
    return fetch(url).then(r => { if (!r.ok) throw r.statusText; return r.json(); });
}

function apiPost(action, params) {
    let url = 'api.php?action=' + action;
    return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    }).then(r => { if (!r.ok) throw r.statusText; return r.json(); });
}

function esc(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

loadJobs();
setInterval(loadJobs, 5000);
</script>
