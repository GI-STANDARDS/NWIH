<div class="page-header-inline">
    <div>
        <h1>Manager &amp; Tools</h1>
        <p>ML pipeline status (top) and optional AI/GUUF model management (bottom).</p>
    </div>
</div>

<div class="grid-2col">
    <div class="glass-card">
        <div class="glass-card-title">System Status</div>
        <div id="backendStatus"><p class="text-muted">Checking...</p></div>
    </div>
    <div class="glass-card">
        <div class="glass-card-title">GPU / CUDA</div>
        <div id="cudaStatus"><p class="text-muted">Checking...</p></div>
    </div>
</div>

<!-- ═══ ML Components (Required for analysis) ═══ -->
<div class="glass-card" style="margin-bottom:20px;">
    <div class="glass-card-title"> ML Pipeline Components</div>
    <p class="text-muted" style="font-size:0.85rem;margin-bottom:12px;">
        These enable embeddings, clustering, and vector search for comment analysis. <strong>No GGUF model required.</strong>
    </p>
    <div id="packageList"><p class="text-muted">Loading...</p></div>
</div>

<hr style="border:0;border-top:1px solid var(--glass-border);margin:24px 0;">

<h3 style="color:var(--text-gold);margin-bottom:12px;"> Optional AI Features (GGUF Required)</h3>
<p class="text-muted" style="font-size:0.85rem;margin-bottom:16px;">
    These features require a llama.cpp binary and GGUF model. Core ML analysis works without them.
</p>

<!-- ═══ llama.cpp Binary ═══ -->
<div class="glass-card" style="margin-bottom:20px;">
    <div class="glass-card-title"> llama.cpp Binary</div>
    <p class="text-muted" style="font-size:0.85rem;margin-bottom:12px;">
        llama.cpp is downloaded from GitHub releases. No pip package or external service needed.
    </p>
    <div id="llamaBinaryStatus"><p class="text-muted">Checking...</p></div>
    <div style="margin-top:10px;">
        <button class="btn" onclick="downloadLlamaBinary()"> Download llama.cpp Binary</button>
    </div>
</div>

<!-- ═══ AI Model Manager ═══ -->
<div class="glass-card" style="margin-bottom:20px;">
    <div class="glass-card-title"> AI Model Manager</div>
    <p class="text-muted" style="font-size:0.85rem;margin-bottom:12px;">
        Model only occupies RAM during active inference. Auto-unloads after idle timeout.
    </p>
    <div id="modelManagerStatus"><p class="text-muted">Checking...</p></div>
    <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
        <button class="btn btn-primary" onclick="modelAction('load')"> Load Model</button>
        <button class="btn" onclick="modelAction('unload')"> Unload Model</button>
        <button class="btn" onclick="modelAction('warm')"> Warm Up GPU</button>
        <label class="btn" style="cursor:pointer;">
            Browse .gguf File
            <input type="file" accept=".gguf" id="modelFileInput" style="display:none;" onchange="uploadModelFile(this)">
        </label>
    </div>
    <div id="fileUploadProgress" style="display:none;margin-top:10px;">
        <div class="progress-container">
            <div class="progress-bar" id="fileUploadBar" style="width:0%"></div>
        </div>
    </div>
    <div id="fileUploadStatus" style="margin-top:8px;font-size:0.82rem;color:var(--text-muted);"></div>
</div>

<!-- ═══ Model Debug Console ═══ -->
<div class="glass-card" style="margin-bottom:20px;">
    <div class="glass-card-title" style="display:flex;align-items:center;justify-content:space-between;">
        <span> Model Debug Console</span>
        <div style="display:flex;gap:6px;">
            <span id="modelDebugBadge" style="font-size:0.7rem;padding:2px 8px;border-radius:100px;background:rgba(255,255,255,0.05);color:var(--text-muted);">idle</span>
            <button class="btn" style="padding:2px 10px;font-size:0.7rem;" onclick="clearModelLogs()">Clear</button>
        </div>
    </div>
    <div id="modelDebugLog" style="background:rgba(0,0,0,0.35);padding:10px;border-radius:8px;font-family:monospace;font-size:0.78rem;max-height:200px;overflow-y:auto;margin-top:6px;color:var(--text-muted);">
        <div style="color:var(--text-muted);">Waiting for model events...</div>
    </div>
</div>

<!-- ═══ Download Model ═══ -->
<div class="glass-card" style="margin-bottom:20px;">
    <div class="glass-card-title"> Download AI Model (GGUF)</div>
    <p class="text-muted" style="font-size:0.85rem;margin-bottom:12px;">
        Download a quantized model from Hugging Face. Recommended: <strong>Llama 3.2 3B (Q4_K_M)</strong> — best balance of speed &amp; quality.
    </p>
    <div id="modelList"><p class="text-muted">Loading...</p></div>
    <div id="modelDownloadProgress" style="display:none;margin-top:12px;">
        <div class="progress-container">
            <div class="progress-bar" id="modelDlBar" style="width:0%"></div>
        </div>
        <div id="modelDlLog" style="background:rgba(0,0,0,0.3);padding:10px;border-radius:8px;font-family:monospace;font-size:0.8rem;max-height:150px;overflow-y:auto;margin-top:6px;"></div>
    </div>
</div>

<div id="installProgress" style="display:none;margin-top:16px;" class="glass-card">
    <div class="glass-card-title">Installation Progress</div>
    <div class="progress-container">
        <div class="progress-bar" id="installProgressBar" style="width:0%"></div>
    </div>
    <div id="installLog" style="background:rgba(0,0,0,0.3);padding:10px;border-radius:8px;font-family:monospace;font-size:0.8rem;max-height:200px;overflow-y:auto;margin-top:8px;"></div>
</div>

<script>
function loadTools() {
    fetch('api.php?action=health')
        .then(r => r.json())
        .then(data => {
            document.getElementById('backendStatus').innerHTML =
                `<span class="text-green"> Online</span> — ${data.service || 'API'} v${data.version || '?'}`;
        })
        .catch(() => {
            document.getElementById('backendStatus').innerHTML = '<span class="text-red"> Offline</span>';
        });

    fetch('api.php?action=setup_cuda')
        .then(r => r.json())
        .then(data => {
            document.getElementById('cudaStatus').innerHTML = data.available && data.gpus.length
                ? data.gpus.map(g => `<span class="text-green"> GPU</span> ${g.name} (${g.memory})`).join('<br>')
                : '<span class="text-yellow"> No GPU detected</span> — CPU mode';
        })
        .catch(() => {
            document.getElementById('cudaStatus').innerHTML = '<span class="text-yellow"> Unknown</span>';
        });

    // llama.cpp binary + models
    loadLlamaStatus();
    loadModels();
    loadPackages();
}

function loadLlamaStatus() {
    fetch('api.php?action=setup_status')
        .then(r => r.json())
        .then(data => {
            const lc = data.llama_cpp || {};
            const binAvail = lc.binary_available;
            document.getElementById('llamaBinaryStatus').innerHTML = binAvail
                ? `<span class="text-green"> Binary downloaded</span> — ready to serve`
                : `<span class="text-yellow"> Not downloaded</span> — click below to download`;
        });
}

function downloadLlamaBinary() {
    const log = document.getElementById('installLog');
    const progress = document.getElementById('installProgress');
    const bar = document.getElementById('installProgressBar');
    progress.style.display = 'block';
    bar.style.width = '5%';
    log.innerHTML = '<div>Downloading llama.cpp binary...</div>';

    fetch('http://127.0.0.1:8000/llama/binary/download', {
        method: 'GET',
    })
    .then(r => r.body.getReader())
    .then(reader => {
        const decoder = new TextDecoder();
        function read() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    bar.style.width = '100%';
                    log.innerHTML += '<div class="text-green">Binary ready!</div>';
                    setTimeout(loadLlamaStatus, 1000);
                    return;
                }
                const text = decoder.decode(value);
                for (const line of text.split('\n')) {
                    if (line.startsWith('data: ')) {
                        try {
                            const evt = JSON.parse(line.slice(6));
                            if (evt.progress !== undefined) bar.style.width = Math.min(evt.progress, 100) + '%';
                            if (evt.message) { log.innerHTML += '<div>' + esc(evt.message) + '</div>'; log.scrollTop = log.scrollHeight; }
                            if (evt.error) { log.innerHTML += '<div style="color:var(--red);">ERROR: ' + esc(evt.error) + '</div>'; }
                        } catch(e) {}
                    }
                }
                read();
            });
        }
        read();
    })
    .catch(err => {
        log.innerHTML += '<div style="color:var(--red);">Error: ' + err.message + '</div>';
    });
}

function loadModels() {
    fetch('api.php?action=llama_list_models')
        .then(r => r.json())
        .then(data => {
            const downloaded = data.downloaded || [];
            const recommended = data.recommended || [];
            let html = '';

            if (downloaded.length) {
                html += '<div style="margin-bottom:10px;"><strong style="color:var(--text-gold);">Downloaded Models:</strong>';
                downloaded.forEach(m => {
                    const size = m.size_bytes ? ' (' + Math.round(m.size_bytes / 1024 / 1024) + 'MB)' : '';
                    html += `<div class="feature-item" style="margin:4px 0;padding:6px 10px;">
                        <span>${esc(m.name || m.filename)}${size}</span>
                        ${m.default ? '<span class="badge badge-medium" style="font-size:0.7rem;">default</span>' : ''}
                    </div>`;
                });
                html += '</div>';
            }

            html += '<strong style="color:var(--text-gold);">Available for Download:</strong>';
            recommended.forEach(m => {
                html += `<div class="feature-item" style="margin:4px 0;padding:8px 12px;">
                    <div style="flex:1;">
                        <strong>${esc(m.name)}</strong>
                        <div style="font-size:0.78rem;color:var(--text-muted);">${esc(m.description)} — ~${m.size_gb}GB</div>
                    </div>
                    <button class="btn" style="padding:4px 14px;font-size:0.8rem;" onclick="downloadModel('${esc(m.id)}')">Download</button>
                </div>`;
            });

            document.getElementById('modelList').innerHTML = html;
        })
        .catch(() => {
            document.getElementById('modelList').innerHTML = '<span class="text-red"> Could not reach backend</span>';
        });
}

function downloadModel(modelId) {
    const div = document.getElementById('modelDownloadProgress');
    const bar = document.getElementById('modelDlBar');
    const log = document.getElementById('modelDlLog');
    div.style.display = 'block';
    bar.style.width = '0%';
    log.innerHTML = '<div>Starting download...</div>';

    fetch('http://127.0.0.1:8000/llama/model/download', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ model_id: modelId })
    })
    .then(r => r.body.getReader())
    .then(reader => {
        const decoder = new TextDecoder();
        function read() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    bar.style.width = '100%';
                    log.innerHTML += '<div class="text-green">Download complete!</div>';
                    setTimeout(loadModels, 2000);
                    return;
                }
                const text = decoder.decode(value);
                for (const line of text.split('\n')) {
                    if (line.startsWith('data: ')) {
                        try {
                            const evt = JSON.parse(line.slice(6));
                            if (evt.progress !== undefined) bar.style.width = Math.min(evt.progress, 100) + '%';
                            if (evt.message) { log.innerHTML += '<div>' + esc(evt.message) + '</div>'; log.scrollTop = log.scrollHeight; }
                            if (evt.error) { log.innerHTML += '<div style="color:var(--red);">ERROR: ' + esc(evt.error) + '</div>'; }
                        } catch(e) {}
                    }
                }
                read();
            });
        }
        read();
    })
    .catch(err => {
        log.innerHTML += '<div style="color:var(--red);">Error: ' + err.message + '</div>';
    });
}

function loadPackages() {
    fetch('api.php?action=setup_status')
        .then(r => r.json())
        .then(data => {
            const pkgs = data.packages || {};
            const allInstalled = data.all_heavy_installed || false;
            const groups = {
                'Core Embeddings': ['sentence-transformers'],
                'Clustering': ['hdbscan', 'umap-learn'],
                'Vector DB': ['faiss-cpu'],
            };

            let html = '';
            for (const [groupName, pkgsList] of Object.entries(groups)) {
                const all = pkgsList.every(p => pkgs[p]?.installed);
                const any = pkgsList.some(p => pkgs[p]?.installed);
                html += `<div class="feature-item" style="margin-bottom:6px;padding:8px 12px;">
                    <strong style="min-width:130px;">${groupName}</strong>
                    <span style="flex:1;font-size:0.82rem;color:var(--text-muted);">${pkgsList.join(', ')}</span>
                    <span style="color:${all ? 'var(--green)' : (any ? 'var(--yellow)' : 'var(--red)')};font-weight:600;font-size:0.82rem;">
                        ${all ? 'Installed' : (any ? 'Partial' : 'Missing')}
                    </span>
                    ${!all ? `<button class="btn" style="padding:3px 12px;font-size:0.78rem;" onclick="installGroup('${pkgsList[0] === 'sentence-transformers' ? 'embeddings' : (pkgsList[0] === 'hdbscan' ? 'clustering' : 'vector_db')}')">Install</button>` : ''}
                </div>`;
            }

            if (!allInstalled) {
                html += `<button class="btn btn-primary" onclick="installGroup('all')" style="width:100%;margin-top:8px;">Install All ML Components</button>`;
            } else {
                html += `<div style="margin-top:8px;"><span class="text-green" style="font-weight:600;"> All ML components installed</span></div>`;
            }

            document.getElementById('packageList').innerHTML = html;
        })
        .catch(() => {
            document.getElementById('packageList').innerHTML = '<span class="text-red"> Backend unreachable</span>';
        });
}

function installGroup(group) {
    const progressDiv = document.getElementById('installProgress');
    const bar = document.getElementById('installProgressBar');
    const log = document.getElementById('installLog');
    progressDiv.style.display = 'block';
    bar.style.width = '0%';
    log.innerHTML = '';

    fetch('http://127.0.0.1:8000/setup/install', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ group: group })
    })
    .then(r => r.body.getReader())
    .then(reader => {
        const decoder = new TextDecoder();
        function read() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    bar.style.width = '100%';
                    log.innerHTML += '<div class="text-green">Complete!</div>';
                    setTimeout(() => loadPackages(), 2000);
                    return;
                }
                const text = decoder.decode(value);
                for (const line of text.split('\n')) {
                    if (line.startsWith('data: ')) {
                        try {
                            const evt = JSON.parse(line.slice(6));
                            if (evt.progress !== undefined) bar.style.width = Math.min(evt.progress, 100) + '%';
                            if (evt.message) { log.innerHTML += '<div>' + esc(evt.message) + '</div>'; log.scrollTop = log.scrollHeight; }
                            if (evt.error) { log.innerHTML += '<div style="color:var(--red);">ERROR: ' + esc(evt.error) + '</div>'; }
                        } catch(e) {}
                    }
                }
                read();
            });
        }
        read();
    })
    .catch(err => {
        log.innerHTML += '<div style="color:var(--red);">Error: ' + err.message + '</div>';
    });
}

function loadModelStatus() {
    fetch('api.php?action=model_status')
        .then(r => r.json())
        .then(data => {
            const status = data.server_running
                ? `<span class="text-green"> Server running</span> (port ${data.server_port})`
                : `<span class="text-yellow"> Server stopped</span>`;
            const modelInfo = data.model_name
                ? `<br>Model: <code>${esc(data.model_name)}</code>`
                : '';
            const idle = data.idle_remaining > 0
                ? `<br>Idle timeout: ${data.idle_remaining}s remaining</span>`
                : '';
            document.getElementById('modelManagerStatus').innerHTML =
                `<div>Backend: <code>${data.backend}</code> | ${status}${modelInfo}${idle}</div>` +
                (data.binary_available ? '' : '<div class="text-yellow" style="margin-top:4px;">llama.cpp binary not downloaded</div>') +
                (!data.model_available ? '<div class="text-yellow" style="margin-top:4px;">No model downloaded. Download one below.</div>' : '');

            const badge = document.getElementById('modelDebugBadge');
            if (badge) {
                badge.textContent = data.server_running ? (data.loaded ? 'loaded' : 'active') : 'idle';
                badge.style.background = data.loaded ? 'rgba(108,212,160,0.15)' : data.server_running ? 'rgba(249,226,175,0.15)' : 'rgba(255,255,255,0.05)';
                badge.style.color = data.loaded ? 'var(--green)' : data.server_running ? 'var(--yellow)' : 'var(--text-muted)';
            }
        })
        .catch(() => {
            document.getElementById('modelManagerStatus').innerHTML = '<span class="text-red"> Unreachable</span>';
        });
}

function modelAction(action) {
    const actionMap = { load: 'model_load', unload: 'model_unload', warm: 'model_warm' };
    fetch(`api.php?action=${actionMap[action]}`, { method: 'POST' })
        .then(r => r.json())
        .then(() => setTimeout(loadModelStatus, 1000))
        .catch(err => console.error(err));
}

function uploadModelFile(input) {
    const file = input.files[0];
    if (!file) return;
    const status = document.getElementById('fileUploadStatus');
    const progressDiv = document.getElementById('fileUploadProgress');
    const bar = document.getElementById('fileUploadBar');
    progressDiv.style.display = 'block';
    bar.style.width = '10%';
    status.innerHTML = 'Uploading ' + file.name + '...';

    const formData = new FormData();
    formData.append('file', file);
    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            bar.style.width = Math.min(90, Math.round(e.loaded / e.total * 80) + 10) + '%';
        }
    };
    xhr.onload = function() {
        if (xhr.status === 200) {
            bar.style.width = '100%';
            const data = JSON.parse(xhr.responseText);
            status.innerHTML = '<span class="text-green">Loaded: ' + esc(data.model) + '</span>';
            setTimeout(loadModelStatus, 1000);
        } else {
            try {
                const err = JSON.parse(xhr.responseText);
                status.innerHTML = '<span class="text-red">Error: ' + esc(err.detail || 'Unknown') + '</span>';
            } catch(e) {
                status.innerHTML = '<span class="text-red">Error: ' + xhr.status + '</span>';
            }
        }
        input.value = '';
    };
    xhr.onerror = function() {
        status.innerHTML = '<span class="text-red">Upload failed</span>';
        input.value = '';
    };
    xhr.open('POST', 'http://127.0.0.1:8000/model/load_file', true);
    xhr.send(formData);
}

function loadModelLogs() {
    const logDiv = document.getElementById('modelDebugLog');
    if (!logDiv) return;
    fetch('http://127.0.0.1:8000/model/logs?count=50')
        .then(r => r.json())
        .then(data => {
            if (data.logs && data.logs.length) {
                logDiv.innerHTML = data.logs.map(l => '<div>' + esc(l) + '</div>').join('');
                logDiv.scrollTop = logDiv.scrollHeight;
            }
        })
        .catch(() => {});
}

function clearModelLogs() {
    document.getElementById('modelDebugLog').innerHTML = '<div style="color:var(--text-muted);">Logs cleared.</div>';
    fetch('http://127.0.0.1:8000/model/logs?count=0', { method: 'GET' }).catch(() => {});
}

function esc(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

loadTools();
setInterval(loadModelStatus, 10000);
loadModelStatus();
loadModelLogs();
setInterval(loadModelLogs, 3000);
</script>
