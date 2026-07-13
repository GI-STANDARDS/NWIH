<div class="page-header-inline">
    <div>
        <h1> AI Control Center</h1>
        <p>Manage llama.cpp server, GGUF models, and live system diagnostics</p>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
        <span id="aiManagerOverviewBadge" class="ai-engine-status-badge offline">Checking...</span>
    </div>
</div>

<!-- ═══ ROW 1: LLAMA.CPP SERVER + CONFIG VALIDATION ═══ -->
<div class="grid-2col" style="margin-bottom:20px;">

    <!-- llama.cpp Server -->
    <div class="glass-card">
        <div class="glass-card-title" style="display:flex;justify-content:space-between;align-items:center;">
            <span> llama.cpp Server</span>
            <span id="serverStateBadge" class="status-badge status-offline">Unknown</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;font-size:0.85rem;margin-bottom:12px;">
            <span class="text-muted">Status:</span><span id="srvStatus" class="text-yellow">Checking...</span>
            <span class="text-muted">Loading State:</span><span id="srvLoadState">—</span>
            <span class="text-muted">Host:</span><span>127.0.0.1</span>
            <span class="text-muted">Port:</span><span id="srvPort">—</span>
            <span class="text-muted">Uptime:</span><span id="srvUptime">—</span>
            <span class="text-muted">Last Heartbeat:</span><span id="srvHeartbeat">—</span>
            <span class="text-muted">Binary:</span><span id="srvBinaryStatus">—</span>
        </div>
        <div id="srvErrorBox" style="display:none;background:rgba(232,104,104,0.1);padding:10px;border-radius:8px;margin-bottom:12px;border-left:3px solid var(--red);font-size:0.82rem;">
            <div style="font-weight:600;color:var(--red);" id="srvErrorTitle"></div>
            <div style="margin-top:4px;color:var(--text-muted);" id="srvErrorDetail"></div>
            <div style="margin-top:4px;color:var(--text-gold);font-style:italic;" id="srvErrorFix"></div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="btn btn-primary" onclick="serverAction('start')"> Start Server</button>
            <button class="btn" onclick="serverAction('stop')"> Stop Server</button>
            <button class="btn" onclick="serverAction('restart')"> Restart</button>
            <button class="btn" onclick="runHealthCheck()"> Health Check</button>
            <label style="display:flex;align-items:center;gap:4px;font-size:0.8rem;color:var(--text-muted);cursor:pointer;">
                <input type="checkbox" id="autoStartCb"> Auto Start
            </label>
        </div>
    </div>

    <!-- Config Validation -->
    <div class="glass-card">
        <div class="glass-card-title" style="display:flex;justify-content:space-between;align-items:center;">
            <span> Configuration Validation</span>
            <span id="configHealthBadge" class="status-badge status-offline">Checking...</span>
        </div>
        <div id="configChecksContainer" style="font-size:0.82rem;">
            <p class="text-muted">Loading...</p>
        </div>
        <div style="margin-top:10px;">
            <button class="btn" style="padding:3px 12px;font-size:0.78rem;" onclick="loadConfigValidation()"> Re-validate</button>
        </div>
    </div>
</div>

<!-- ═══ ROW 2: HEALTH CHECK (8-dim) + GPU DETAILS ═══ -->
<div class="grid-2col" style="margin-bottom:20px;">

    <!-- Health Check -->
    <div class="glass-card">
        <div class="glass-card-title" style="display:flex;justify-content:space-between;align-items:center;">
            <span> 8-Dimension Health Check</span>
            <span id="healthOverallBadge" class="status-badge status-offline">Unknown</span>
        </div>
        <div id="healthCheckContainer" style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;font-size:0.8rem;">
            <p class="text-muted" style="grid-column:1/-1;">Run a health check to see results</p>
        </div>
        <div style="margin-top:10px;">
            <button class="btn btn-primary" style="padding:3px 14px;font-size:0.78rem;" onclick="runHealthCheck()"> Run Full Health Check</button>
            <span id="healthTimestamp" style="font-size:0.72rem;color:var(--text-muted);margin-left:8px;"></span>
        </div>
    </div>

    <!-- GPU Details -->
    <div class="glass-card">
        <div class="glass-card-title"> GPU Details</div>
        <div id="gpuDetailContainer" style="font-size:0.85rem;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 20px;">
                <span class="text-muted">Vendor:</span><span id="gpuVendor"><span class="text-muted">—</span></span>
                <span class="text-muted">Model:</span><span id="gpuModel"><span class="text-muted">—</span></span>
                <span class="text-muted">Driver Version:</span><span id="gpuDriver"><span class="text-muted">—</span></span>
                <span class="text-muted">CUDA Version:</span><span id="gpuCuda"><span class="text-muted">—</span></span>
                <span class="text-muted">VRAM Total:</span><span id="gpuVramTotal"><span class="text-muted">—</span></span>
                <span class="text-muted">VRAM Free:</span><span id="gpuVramFree"><span class="text-muted">—</span></span>
                <span class="text-muted">VRAM Used:</span><span id="gpuVramUsed"><span class="text-muted">—</span></span>
                <span class="text-muted">Utilization:</span><span id="gpuUtil"><span class="text-muted">—</span></span>
                <span class="text-muted">Power:</span><span id="gpuPower"><span class="text-muted">—</span></span>
            </div>
            <hr style="border:0;border-top:1px solid var(--glass-border);margin:10px 0;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 20px;font-size:0.85rem;">
                <span class="text-muted">CPU:</span><span id="diagCpu"><span class="text-muted">—</span></span>
                <span class="text-muted">RAM:</span><span id="diagRam"><span class="text-muted">—</span></span>
                <span class="text-muted">Tokens/sec:</span><span id="diagTps"><span class="text-muted">—</span></span>
                <span class="text-muted">Active Requests:</span><span id="diagActiveReqs"><span class="text-muted">0</span></span>
                <span class="text-muted">Prompt Tokens:</span><span id="diagPromptTokens"><span class="text-muted">—</span></span>
                <span class="text-muted">Generated Tokens:</span><span id="diagGenTokens"><span class="text-muted">—</span></span>
                <span class="text-muted">Model Load Time:</span><span id="diagLoadTime"><span class="text-muted">—</span></span>
                <span class="text-muted">Context Usage:</span><span id="diagContext"><span class="text-muted">—</span></span>
            </div>
        </div>
    </div>
</div>

<!-- ═══ ROW 3: DEPENDENCIES + MODEL MANAGER ═══ -->
<div class="grid-2col" style="margin-bottom:20px;">

    <!-- Dependencies -->
    <div class="glass-card">
        <div class="glass-card-title">
            <span> Python Dependencies</span>
            <span id="depRefreshTime" style="font-size:0.72rem;color:var(--text-muted);font-weight:normal;"></span>
        </div>
        <div id="depContainer" style="font-size:0.82rem;">
            <p class="text-muted">Loading...</p>
        </div>
        <div style="margin-top:8px;">
            <button class="btn" style="padding:3px 12px;font-size:0.78rem;" onclick="loadDependencies()"> Refresh</button>
        </div>
    </div>

    <!-- Model Manager -->
    <div class="glass-card">
        <div class="glass-card-title" style="display:flex;justify-content:space-between;align-items:center;">
            <span> GGUF Model Manager</span>
            <div style="display:flex;gap:8px;align-items:center;">
                <span id="modelStateBadge" class="status-badge status-offline">No Model</span>
                <button class="btn" style="padding:3px 12px;font-size:0.78rem;" onclick="scanModels()"> Scan Folder</button>
                <button class="btn" style="padding:3px 12px;font-size:0.78rem;" onclick="refreshModels()"> Refresh</button>
            </div>
        </div>
        <div class="grid-2col" style="gap:12px;">
            <div id="modelListContainer" style="max-height:260px;overflow-y:auto;">
                <p class="text-muted" style="padding:10px 0;">Scanning for models...</p>
            </div>
            <div>
                <div id="modelDetailPanel" style="background:var(--bg-glass);border-radius:var(--radius-sm);padding:12px;">
                    <div style="font-weight:600;margin-bottom:6px;color:var(--text-gold);font-size:0.85rem;" id="detailTitle">No model selected</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px 12px;font-size:0.8rem;">
                        <span class="text-muted">Size:</span><span id="detailSize">—</span>
                        <span class="text-muted">Architecture:</span><span id="detailArch">—</span>
                        <span class="text-muted">Quantization:</span><span id="detailQuant">—</span>
                        <span class="text-muted">Status:</span><span id="detailStatus">Not loaded</span>
                    </div>
                    <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
                        <button class="btn btn-primary" style="padding:3px 14px;font-size:0.8rem;" onclick="loadSelectedModel()"> Load</button>
                        <button class="btn" style="padding:3px 14px;font-size:0.8rem;" onclick="unloadModel()"> Unload</button>
                        <button class="btn" style="padding:3px 14px;font-size:0.8rem;" onclick="reloadModel()"> Reload</button>
                        <button class="btn" style="padding:3px 14px;font-size:0.8rem;color:var(--red);" onclick="deleteModel()"> Delete</button>
                        <label class="btn" style="padding:3px 14px;font-size:0.8rem;cursor:pointer;">
                            Import .gguf
                            <input type="file" accept=".gguf" style="display:none;" onchange="uploadModelFile(this)">
                        </label>
                    </div>
                    <div id="modelActionFeedback" style="margin-top:6px;font-size:0.78rem;color:var(--text-muted);"></div>
                </div>
                <div id="modelLoadProgress" style="display:none;margin-top:8px;">
                    <div class="progress-container">
                        <div class="progress-bar" id="modelLoadProgressBar" style="width:0%"></div>
                    </div>
                    <div id="modelLoadStateLabel" style="font-size:0.78rem;margin-top:3px;color:var(--text-muted);"></div>
                </div>
                <div id="fileUploadProgress" style="display:none;margin-top:8px;">
                    <div class="progress-container">
                        <div class="progress-bar" id="fileUploadBar" style="width:0%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- ═══ ROW 4: STARTUP LOGS + SYSTEM STATUS ═══ -->
<div class="grid-2col" style="margin-bottom:20px;">

    <!-- Startup Logs -->
    <div class="glass-card">
        <div class="glass-card-title" style="display:flex;justify-content:space-between;align-items:center;">
            <span> Server Startup Log</span>
            <span id="startupLogCount" style="font-size:0.72rem;color:var(--text-muted);font-weight:normal;"></span>
        </div>
        <div id="startupLogContainer" style="background:rgba(0,0,0,0.35);padding:8px;border-radius:8px;font-family:monospace;font-size:0.7rem;max-height:200px;overflow-y:auto;margin-top:4px;">
            <div class="text-muted" style="padding:10px;text-align:center;">Server not started yet</div>
        </div>
    </div>

    <!-- System Status -->
    <div class="glass-card">
        <div class="glass-card-title">System Status</div>
        <div class="status-grid" id="statusGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;">
            <div class="status-item" data-component="api"><span class="status-indicator status-online"></span> API Connection</div>
            <div class="status-item" data-component="database"><span class="status-indicator status-online"></span> Database</div>
            <div class="status-item" data-component="worker"><span class="status-indicator status-online"></span> Background Worker</div>
            <div class="status-item" data-component="comment_extractor"><span class="status-indicator status-online"></span> Comment Extractor</div>
            <div class="status-item" data-component="embedding_engine"><span class="status-indicator status-offline"></span> Embedding Engine</div>
            <div class="status-item" data-component="vector_database"><span class="status-indicator status-offline"></span> Vector Database</div>
            <div class="status-item" data-component="analytics_engine"><span class="status-indicator status-offline"></span> Analytics Engine</div>
            <div class="status-item" data-component="llama_server"><span class="status-indicator status-offline"></span> llama.cpp Server</div>
            <div class="status-item" data-component="gguf_model"><span class="status-indicator status-offline"></span> GGUF Model</div>
            <div class="status-item" data-component="ai_chat"><span class="status-indicator status-offline"></span> AI Chat</div>
        </div>
    </div>
</div>

<!-- ═══ ROW 5: GENERAL LOGS ═══ -->
<div class="glass-card" style="margin-bottom:20px;">
    <div class="glass-card-title" style="display:flex;justify-content:space-between;align-items:center;">
        <span> Server Logs</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <select id="logChannelFilter" style="background:var(--bg-glass);border:1px solid var(--glass-border);color:var(--text);padding:2px 8px;border-radius:6px;font-size:0.78rem;">
                <option value="">All Channels</option>
            </select>
            <select id="logSeverityFilter" style="background:var(--bg-glass);border:1px solid var(--glass-border);color:var(--text);padding:2px 8px;border-radius:6px;font-size:0.78rem;">
                <option value="0">All Levels</option>
                <option value="1">Info+</option>
                <option value="2">Warn+</option>
                <option value="3">Error only</option>
            </select>
            <input type="text" id="logSearchInput" placeholder="Search logs..." style="background:var(--bg-glass);border:1px solid var(--glass-border);color:var(--text);padding:2px 8px;border-radius:6px;font-size:0.78rem;width:120px;">
            <button class="btn" style="padding:2px 10px;font-size:0.7rem;" onclick="refreshLogs()"> Refresh</button>
            <button class="btn" style="padding:2px 10px;font-size:0.7rem;" onclick="clearLogs()"> Clear</button>
            <button class="btn" style="padding:2px 10px;font-size:0.7rem;" onclick="exportLogs()"> Export</button>
        </div>
    </div>
    <div id="logContainer" style="background:rgba(0,0,0,0.35);padding:8px;border-radius:8px;font-family:monospace;font-size:0.72rem;max-height:260px;overflow-y:auto;margin-top:4px;">
        <div class="text-muted" style="padding:15px;text-align:center;">Loading logs...</div>
    </div>
</div>

<script>
let selectedModelFile = null;
let diagInterval = null;
let logInterval = null;
let healthInterval = null;

// ── Initialization ──

function loadAIManager() {
    loadServerStatus();
    loadSystemStatus();
    loadConfigValidation();
    loadDependencies();
    scanModels();
    refreshLogs();
    startDiagPolling();
    startLogPolling();
    startAutoRefresh();
}

// ── Server Management ──

function loadServerStatus() {
    apiGet('model_status').then(data => {
        const running = data.server_running;
        const srvState = data.loading_state || 'unloaded';

        document.getElementById('serverStateBadge').className = 'status-badge ' +
            (running ? 'status-online' : (srvState === 'failed' ? 'status-error' : 'status-offline'));
        document.getElementById('serverStateBadge').textContent = running ? 'Running' :
            (srvState === 'failed' ? 'Error' : 'Stopped');

        document.getElementById('srvStatus').innerHTML = running
            ? '<span class="text-green"> Running</span>'
            : (srvState === 'failed' ? '<span class="text-red"> Error</span>' : '<span class="text-yellow"> Stopped</span>');

        const stateLabels = {'initializing':'Initializing','loading_tokenizer':'Tokenizer','allocating_memory':'Memory',
            'loading_weights':'Weights','building_kv_cache':'KV Cache','ready':'Ready','failed':'Failed','unloaded':'Unloaded'};
        document.getElementById('srvLoadState').textContent = stateLabels[srvState] || srvState;
        document.getElementById('srvPort').textContent = data.server_port || '—';

        document.getElementById('srvBinaryStatus').innerHTML = data.binary_available
            ? '<span class="text-green">Available</span>'
            : '<span class="text-red">Not found</span>';

        if (data.uptime_seconds > 0) {
            const u = data.uptime_seconds;
            document.getElementById('srvUptime').textContent = Math.floor(u/3600)+'h '+Math.floor((u%3600)/60)+'m '+Math.floor(u%60)+'s';
        } else {
            document.getElementById('srvUptime').textContent = '—';
        }
        document.getElementById('srvHeartbeat').textContent = data.last_heartbeat > 0
            ? Math.floor((Date.now()/1000 - data.last_heartbeat)) + 's ago' : '—';

        // Error box
        const errBox = document.getElementById('srvErrorBox');
        if (data.loading_error && data.loading_error.reason) {
            errBox.style.display = 'block';
            document.getElementById('srvErrorTitle').textContent = data.loading_error.reason;
            document.getElementById('srvErrorDetail').textContent = data.loading_error.detail || '';
            document.getElementById('srvErrorFix').textContent = data.loading_error.fix ? 'Fix: ' + data.loading_error.fix : '';
        } else {
            errBox.style.display = 'none';
        }

        // Server metrics
        const m = data.server_metrics || {};
        document.getElementById('diagTps').innerHTML = (m.tokens_per_sec || 0) > 0
            ? '<span class="text-green">' + m.tokens_per_sec + '</span>'
            : '<span class="text-muted">—</span>';
        document.getElementById('diagPromptTokens').textContent = m.prompt_tokens || '—';
        document.getElementById('diagGenTokens').textContent = m.generated_tokens || '—';
        document.getElementById('diagActiveReqs').textContent = m.active_requests || '0';

        // Context usage
        if (m.n_ctx_max && m.cache_size) {
            const pct = Math.round((m.cache_size / m.n_ctx_max) * 100);
            document.getElementById('diagContext').innerHTML = pct + '% (' + m.cache_size + '/' + m.n_ctx_max + ')';
        } else {
            document.getElementById('diagContext').textContent = '—';
        }

        // Model load time
        document.getElementById('diagLoadTime').textContent = data.loading_duration_seconds
            ? data.loading_duration_seconds.toFixed(1) + 's'
            : (data.uptime_seconds ? '—' : '—');

        // Startup logs
        const startupLogs = data.startup_logs || [];
        const startupContainer = document.getElementById('startupLogContainer');
        document.getElementById('startupLogCount').textContent = startupLogs.length + ' lines';
        if (startupLogs.length > 0) {
            startupContainer.innerHTML = startupLogs.map(entry => {
                const msg = typeof entry === 'string' ? entry : (entry.message || JSON.stringify(entry));
                const time = entry.time ? new Date(entry.time * 1000).toLocaleTimeString() : '';
                return '<div style="padding:1px 0;display:flex;gap:6px;">' +
                    (time ? '<span style="color:var(--text-muted);min-width:65px;">' + esc(time) + '</span>' : '') +
                    '<span>' + esc(msg) + '</span></div>';
            }).join('');
            startupContainer.scrollTop = startupContainer.scrollHeight;
        } else if (running) {
            startupContainer.innerHTML = '<div class="text-muted" style="padding:10px;text-align:center;">No startup log captured</div>';
        }

        // Model badge
        updateModelBadge(data);
        updateDetailFromStatus(data);
    }).catch(() => {
        document.getElementById('serverStateBadge').className = 'status-badge status-error';
        document.getElementById('serverStateBadge').textContent = 'Unreachable';
        document.getElementById('srvStatus').innerHTML = '<span class="text-red"> Backend unreachable</span>';
    });
}

function serverAction(action) {
    const feedback = document.getElementById('modelActionFeedback');
    if (action === 'start') {
        apiGet('model_status').then(data => {
            if (data.model_available) {
                apiPost('model_load', {}).then(() => {
                    feedback.innerHTML = '<span class="text-green">Server started</span>';
                    setTimeout(loadServerStatus, 2000);
                }).catch(e => feedback.innerHTML = '<span class="text-red">' + e + '</span>');
            } else {
                feedback.innerHTML = '<span class="text-yellow">No GGUF model available. Upload one first.</span>';
            }
        });
    } else if (action === 'stop') {
        apiPost('model_unload', {}).then(() => {
            feedback.innerHTML = '<span class="text-green">Server stopped</span>';
            setTimeout(loadServerStatus, 1000);
        });
    } else if (action === 'restart') {
        apiPost('model_unload', {}).then(() => {
            setTimeout(() => {
                apiPost('model_load', {}).then(() => {
                    feedback.innerHTML = '<span class="text-green">Server restarted</span>';
                    setTimeout(loadServerStatus, 2000);
                });
            }, 1000);
        });
    }
}

// ── Health Check (8-dimension) ──

function runHealthCheck() {
    const container = document.getElementById('healthCheckContainer');
    const badge = document.getElementById('healthOverallBadge');
    container.innerHTML = '<p class="text-muted" style="grid-column:1/-1;">Running health check...</p>';
    badge.className = 'status-badge status-warning';
    badge.textContent = 'Running...';

    apiGet('model_health').then(data => {
        const checks = data.checks || {};
        const healthy = data.healthy;
        const dims = [
            ['process_running', 'Process Running'],
            ['port_reachable', 'Port Reachable'],
            ['api_reachable', 'API Reachable'],
            ['model_loaded', 'Model Loaded'],
            ['context_initialized', 'Context Initialized'],
            ['disk_accessible', 'Disk Accessible'],
            ['binary_exists', 'Binary Exists'],
            ['configuration_valid', 'Configuration Valid']
        ];

        let passCount = 0, failCount = 0;
        const rows = dims.map(([key, label]) => {
            const check = checks[key] || {status: 'info', detail: 'No data'};
            if (check.status === 'pass') passCount++;
            else if (check.status === 'fail') failCount++;
            const icon = check.status === 'pass' ? '✅' : check.status === 'fail' ? '❌' : '⚠️';
            const color = check.status === 'pass' ? 'var(--green)' : check.status === 'fail' ? 'var(--red)' : 'var(--text-muted)';
            return '<div style="display:flex;align-items:center;gap:6px;padding:3px 0;">' +
                '<span>' + icon + '</span>' +
                '<span style="font-weight:500;">' + label + ':</span>' +
                '<span style="color:' + color + ';font-size:0.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + esc(check.detail || '') + '">' +
                esc(check.detail || check.status) + '</span></div>';
        }).join('');

        container.innerHTML = rows;

        badge.className = 'status-badge ' + (failCount === 0 && passCount > 0 ? 'status-online' : failCount > 0 ? 'status-error' : 'status-warning');
        badge.textContent = passCount + '/' + (passCount + failCount) + ' pass';

        document.getElementById('healthTimestamp').textContent = 'Updated: ' + new Date().toLocaleTimeString();

        // Also update server status
        loadServerStatus();
    }).catch(err => {
        container.innerHTML = '<p class="text-red" style="grid-column:1/-1;">Health check failed: ' + esc(err) + '</p>';
        badge.className = 'status-badge status-error';
        badge.textContent = 'Error';
    });
}

// ── Config Validation ──

function loadConfigValidation() {
    apiGet('system_config-validate').then(data => {
        const checks = data.checks || {};
        const healthy = data.healthy;
        const issues = data.issues || [];

        const badge = document.getElementById('configHealthBadge');
        badge.className = 'status-badge ' + (healthy ? 'status-online' : 'status-error');
        badge.textContent = healthy ? 'All Good' : issues.length + ' Issues';

        const container = document.getElementById('configChecksContainer');
        const rows = Object.entries(checks).map(([key, check]) => {
            const statusIcons = {pass: '✅', fail: '❌', warn: '⚠️', info: 'ℹ️'};
            const colors = {pass: 'var(--green)', fail: 'var(--red)', warn: 'var(--yellow)', info: 'var(--text-muted)'};
            return '<div style="display:flex;align-items:center;gap:6px;padding:2px 0;">' +
                '<span style="font-size:0.85rem;">' + (statusIcons[check.status] || 'ℹ️') + '</span>' +
                '<span style="font-weight:500;min-width:110px;">' + key.replace(/_/g,' ') + ':</span>' +
                '<span style="color:' + (colors[check.status] || 'var(--text)') + ';font-size:0.78rem;">' + esc(check.detail || '') + '</span></div>';
        }).join('');

        if (issues.length > 0) {
            container.innerHTML = rows + '<div style="margin-top:8px;padding:6px 8px;background:rgba(232,104,104,0.1);border-radius:6px;border-left:3px solid var(--red);">' +
                '<div style="font-weight:600;font-size:0.78rem;color:var(--red);margin-bottom:2px;">Issues to resolve:</div>' +
                issues.map(i => '<div style="font-size:0.75rem;color:var(--text-muted);padding:1px 0;">• ' + esc(i) + '</div>').join('') +
                '</div>';
        } else {
            container.innerHTML = rows;
        }
    }).catch(() => {
        document.getElementById('configChecksContainer').innerHTML = '<p class="text-red">Failed to load config validation</p>';
        document.getElementById('configHealthBadge').className = 'status-badge status-error';
        document.getElementById('configHealthBadge').textContent = 'Error';
    });
}

// ── Dependencies Panel ──

function loadDependencies() {
    apiGet('system_dependency-status').then(data => {
        document.getElementById('depRefreshTime').textContent = 'Updated: ' + new Date().toLocaleTimeString();
        const container = document.getElementById('depContainer');
        if (Object.keys(data).length === 0) {
            container.innerHTML = '<p class="text-muted">No dependencies tracked</p>';
            return;
        }
        container.innerHTML = Object.entries(data).map(([name, dep]) => {
            const installed = dep.installed;
            return '<div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--glass-border);">' +
                '<div style="display:flex;align-items:center;gap:8px;">' +
                    '<span>' + (installed ? '✅' : '⬜') + '</span>' +
                    '<div><div style="font-weight:500;font-size:0.82rem;">' + esc(name) + '</div>' +
                    '<div style="font-size:0.7rem;color:var(--text-muted);">' + esc(dep.feature || '') + '</div></div></div>' +
                '<div style="display:flex;align-items:center;gap:6px;">' +
                    (installed
                        ? '<span style="font-size:0.7rem;color:var(--green);">v' + esc(dep.version || '?') + '</span>'
                        : (dep.install_cmd
                            ? '<button class="btn" style="padding:2px 10px;font-size:0.7rem;" onclick="installDep(\'' + esc(name) + '\')"> Install</button>'
                            : '<span class="text-muted" style="font-size:0.7rem;">Not available</span>')
                    ) +
                '</div></div>';
        }).join('');
    }).catch(() => {
        document.getElementById('depContainer').innerHTML = '<p class="text-red">Failed to load dependencies</p>';
    });
}

function installDep(name) {
    const container = document.getElementById('depContainer');
    container.innerHTML = '<p class="text-yellow">Installing ' + esc(name) + '...</p>';
    fetch('api.php?action=install_dependency&name=' + encodeURIComponent(name), {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                setTimeout(loadDependencies, 2000);
            } else {
                container.innerHTML = '<p class="text-red">Install failed: ' + esc(data.error || 'Unknown') + '</p>';
            }
        })
        .catch(err => {
            container.innerHTML = '<p class="text-red">Install error: ' + esc(err) + '</p>';
        });
}

// ── Model Management ──

function scanModels() {
    apiGet('model_scan').then(data => {
        const models = data.models || [];
        const container = document.getElementById('modelListContainer');
        if (models.length === 0) {
            container.innerHTML = '<p class="text-muted" style="padding:15px;text-align:center;">No GGUF models found. Upload one or download from the list below.</p>';
            return;
        }
        container.innerHTML = models.map((m, i) =>
            `<div class="model-list-item ${i === 0 ? 'selected' : ''}" data-path="${esc(m.path)}" data-name="${esc(m.filename)}"
                 data-size="${m.size_gb || 0}" data-arch="${esc(m.architecture || 'Unknown')}" data-quant="${esc(m.quantization || 'Unknown')}"
                 onclick="selectModel(this)">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong style="font-size:0.82rem;">${esc(m.filename)}</strong>
                    <span style="font-size:0.72rem;color:var(--text-muted);">${m.size_gb || m.size_mb || '?'} GB</span>
                </div>
                <div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px;">
                    ${esc(m.architecture || '?')} · ${esc(m.quantization || '?')}
                </div>
            </div>`
        ).join('');

        const first = container.querySelector('.model-list-item');
        if (first) selectModel(first);
    }).catch(() => {
        document.getElementById('modelListContainer').innerHTML = '<p class="text-red">Failed to scan models folder</p>';
    });
}

function refreshModels() {
    scanModels();
    loadServerStatus();
}

function selectModel(el) {
    document.querySelectorAll('.model-list-item').forEach(e => e.classList.remove('selected'));
    el.classList.add('selected');
    selectedModelFile = el.dataset.path;
    document.getElementById('detailTitle').textContent = el.dataset.name;
    document.getElementById('detailSize').textContent = el.dataset.size + ' GB';
    document.getElementById('detailArch').textContent = el.dataset.arch;
    document.getElementById('detailQuant').textContent = el.dataset.quant;
    document.getElementById('detailStatus').textContent = 'Selected';
    document.getElementById('modelActionFeedback').innerHTML = '';
}

function updateModelBadge(data) {
    const badge = document.getElementById('modelStateBadge');
    if (data.loaded) {
        badge.className = 'status-badge status-online';
        badge.textContent = 'Loaded';
    } else if (data.server_running) {
        badge.className = 'status-badge status-warning';
        badge.textContent = 'Server Idle';
    } else {
        badge.className = 'status-badge status-offline';
        badge.textContent = 'No Model';
    }
}

function updateDetailFromStatus(data) {
    if (data.loaded && data.model_name) {
        document.getElementById('detailTitle').textContent = data.model_name;
        document.getElementById('detailStatus').textContent = 'Loaded';
    }
}

function loadSelectedModel() {
    if (!selectedModelFile) {
        document.getElementById('modelActionFeedback').innerHTML = '<span class="text-yellow">Select a model first</span>';
        return;
    }
    const feedback = document.getElementById('modelActionFeedback');
    const progress = document.getElementById('modelLoadProgress');
    const bar = document.getElementById('modelLoadProgressBar');
    const stateLabel = document.getElementById('modelLoadStateLabel');
    progress.style.display = 'block';
    bar.style.width = '10%';
    stateLabel.textContent = 'Loading...';
    feedback.innerHTML = '';

    apiPost('model_load', { model_name: selectedModelFile }).then(data => {
        progress.style.display = 'none';
        feedback.innerHTML = '<span class="text-green">Loaded: ' + esc(data.model) + '</span>';
        setTimeout(loadServerStatus, 1000);
    }).catch(err => {
        progress.style.display = 'none';
        try {
            const detail = JSON.parse(err);
            feedback.innerHTML = '<span class="text-red">' + esc(detail.reason || detail.detail || 'Failed') + '</span>';
        } catch(e) {
            feedback.innerHTML = '<span class="text-red">' + esc(err) + '</span>';
        }
        setTimeout(loadServerStatus, 1000);
    });

    let pollCount = 0;
    const pollInterval = setInterval(() => {
        pollCount++;
        apiGet('model_status').then(data => {
            const s = data.loading_state || '';
            const labels = {'initializing':'Initializing...','loading_tokenizer':'Loading tokenizer...',
                'allocating_memory':'Allocating memory...','loading_weights':'Loading weights...',
                'building_kv_cache':'Building KV cache...','ready':'Ready!','failed':'Failed'};
            stateLabel.textContent = labels[s] || s;
            if (s === 'ready' || s === 'failed' || pollCount > 30) {
                clearInterval(pollInterval);
            }
        }).catch(() => {});
    }, 1000);
}

function unloadModel() {
    apiPost('model_unload', {}).then(() => {
        document.getElementById('modelActionFeedback').innerHTML = '<span class="text-green">Model unloaded</span>';
        setTimeout(loadServerStatus, 1000);
    });
}

function reloadModel() {
    unloadModel();
    setTimeout(() => loadSelectedModel(), 1500);
}

function deleteModel() {
    if (!selectedModelFile || !confirm('Delete ' + selectedModelFile.split('/').pop().split('\\').pop() + '?')) return;
    const filename = selectedModelFile.split('/').pop().split('\\').pop();
    fetch('api.php?action=model_delete&filename=' + encodeURIComponent(filename))
        .then(r => r.json())
        .then(() => {
            document.getElementById('modelActionFeedback').innerHTML = '<span class="text-green">Deleted</span>';
            scanModels();
        })
        .catch(err => {
            document.getElementById('modelActionFeedback').innerHTML = '<span class="text-red">' + err + '</span>';
        });
}

function uploadModelFile(input) {
    const file = input.files[0];
    if (!file) return;
    const feedback = document.getElementById('modelActionFeedback');
    const progress = document.getElementById('fileUploadProgress');
    const bar = document.getElementById('fileUploadBar');
    progress.style.display = 'block';
    bar.style.width = '10%';
    feedback.innerHTML = 'Uploading ' + file.name + '...';

    const formData = new FormData();
    formData.append('file', file);
    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) bar.style.width = Math.min(90, Math.round(e.loaded / e.total * 80) + 10) + '%';
    };
    xhr.onload = function() {
        progress.style.display = 'none';
        if (xhr.status === 200) {
            feedback.innerHTML = '<span class="text-green">Uploaded & loaded: ' + esc(file.name) + '</span>';
            scanModels();
            setTimeout(loadServerStatus, 1000);
        } else {
            try { const d = JSON.parse(xhr.responseText);
                feedback.innerHTML = '<span class="text-red">' + esc(d.detail || 'Upload failed') + '</span>';
            } catch(e) { feedback.innerHTML = '<span class="text-red">Upload failed</span>'; }
        }
        input.value = '';
    };
    xhr.onerror = function() { feedback.innerHTML = '<span class="text-red">Upload failed</span>'; input.value = ''; };
    xhr.open('POST', 'http://127.0.0.1:8000/model/load_file', true);
    xhr.send(formData);
}

// ── System Diagnostics ──

function loadSystemStatus() {
    apiGet('system_diagnostics').then(data => {
        const cpu = data.cpu || {};
        const ram = data.ram || {};
        const gpu = data.gpu || {};

        document.getElementById('diagCpu').innerHTML = cpu.percent !== undefined
            ? cpu.percent + '% (' + cpu.count + ' cores)'
            : '<span class="text-muted">N/A (install psutil)</span>';
        document.getElementById('diagRam').innerHTML = ram.used_mb !== undefined
            ? Math.round(ram.used_mb / 1024) + 'GB / ' + Math.round(ram.total_mb / 1024) + 'GB (' + ram.percent + '%)'
            : '<span class="text-muted">N/A</span>';

        // GPU details
        document.getElementById('gpuVendor').textContent = gpu.vendor || '—';
        document.getElementById('gpuModel').textContent = gpu.name || '—';
        document.getElementById('gpuDriver').textContent = gpu.driver_version || '—';
        document.getElementById('gpuCuda').textContent = gpu.cuda_version || '—';
        document.getElementById('gpuVramTotal').textContent = gpu.memory_total_mb
            ? Math.round(gpu.memory_total_mb / 1024) + ' GB' : '—';
        document.getElementById('gpuVramFree').textContent = gpu.memory_free_mb
            ? Math.round(gpu.memory_free_mb / 1024) + ' GB' : '—';
        document.getElementById('gpuVramUsed').textContent = gpu.memory_used_mb
            ? Math.round(gpu.memory_used_mb / 1024) + ' GB' : '—';
        document.getElementById('gpuUtil').textContent = gpu.utilization_percent !== undefined
            ? gpu.utilization_percent + '%' : '—';
        document.getElementById('gpuPower').textContent = gpu.power_watts
            ? gpu.power_watts + ' W' : '—';
    }).catch(() => {});

    // System status indicators
    apiGet('system_status').then(data => {
        document.querySelectorAll('.status-item').forEach(el => {
            const comp = el.dataset.component;
            const info = data[comp];
            if (info) {
                const dot = el.querySelector('.status-indicator');
                dot.className = 'status-indicator status-' + (info.online ? 'online' : 'offline');
                el.title = info.status || '';
            }
        });
    }).catch(() => {});
}

function startDiagPolling() {
    if (diagInterval) clearInterval(diagInterval);
    diagInterval = setInterval(loadSystemStatus, 5000);
}

// ── Auto Refresh ──

function startAutoRefresh() {
    if (healthInterval) clearInterval(healthInterval);
    healthInterval = setInterval(() => {
        loadServerStatus();
        loadSystemStatus();
        loadConfigValidation();
        loadDependencies();
    }, 3000);
}

// ── Logging ──

function refreshLogs() {
    const channel = document.getElementById('logChannelFilter').value;
    const severity = document.getElementById('logSeverityFilter').value;
    const search = document.getElementById('logSearchInput').value;
    let url = 'api.php?action=logs&count=100';
    if (channel) url += '&channel=' + encodeURIComponent(channel);
    if (severity) url += '&severity=' + severity;
    if (search) url += '&search=' + encodeURIComponent(search);

    fetch(url)
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('logContainer');
            const logs = data.logs || [];
            const channels = data.channels || {};

            const filter = document.getElementById('logChannelFilter');
            const currentVal = filter.value;
            filter.innerHTML = '<option value="">All Channels</option>' +
                Object.keys(channels).map(c =>
                    '<option value="' + esc(c) + '">' + esc(c) + ' (' + channels[c] + ')</option>'
                ).join('');
            filter.value = currentVal;

            if (logs.length === 0) {
                container.innerHTML = '<div class="text-muted" style="padding:15px;text-align:center;">No log entries</div>';
                return;
            }

            container.innerHTML = logs.map(l => {
                const sevColor = l.severity >= 3 ? 'var(--red)' : l.severity >= 2 ? 'var(--yellow)' : l.severity >= 1 ? 'var(--green)' : 'var(--text-muted)';
                const sevLabel = l.severity_label || '?';
                const time = l.timestamp ? l.timestamp.split('.')[0].replace('T', ' ') : '?';
                return '<div style="padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.03);display:flex;gap:8px;">' +
                    '<span style="color:var(--text-muted);min-width:55px;font-size:0.68rem;">' + esc(time.slice(11, 19)) + '</span>' +
                    '<span style="color:' + sevColor + ';min-width:35px;font-weight:600;font-size:0.7rem;">' + sevLabel + '</span>' +
                    '<span style="color:var(--text-muted);min-width:70px;font-size:0.68rem;">' + esc(l.channel) + '</span>' +
                    '<span style="flex:1;font-size:0.7rem;">' + esc(l.message) + '</span></div>';
            }).join('');
            container.scrollTop = container.scrollHeight;
        })
        .catch(() => {
            document.getElementById('logContainer').innerHTML = '<div class="text-red" style="padding:15px;text-align:center;">Failed to load logs</div>';
        });
}

function startLogPolling() {
    if (logInterval) clearInterval(logInterval);
    logInterval = setInterval(refreshLogs, 3000);
}

function clearLogs() {
    const channel = document.getElementById('logChannelFilter').value;
    const url = 'api.php?action=logs_clear' + (channel ? '&channel=' + encodeURIComponent(channel) : '');
    fetch(url, { method: 'POST' }).then(() => refreshLogs());
}

function exportLogs() {
    fetch('api.php?action=logs&count=500')
        .then(r => r.json())
        .then(data => {
            const logs = data.logs || [];
            const text = logs.map(l => '[' + l.timestamp + '] [' + l.severity_label + '] [' + l.channel + '] ' + l.message).join('\n');
            const blob = new Blob([text], {type: 'text/plain'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'system_logs_' + new Date().toISOString().slice(0, 10) + '.txt';
            a.click();
        });
}

// ── Utility ──

function apiGet(action, params) {
    let url = 'api.php?action=' + action;
    if (params) for (const k in params) url += '&' + k + '=' + encodeURIComponent(params[k]);
    return fetch(url).then(r => { if (!r.ok) throw r.statusText; return r.json(); });
}

function apiPost(action, data) {
    return fetch('api.php?action=' + action, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data || {})
    }).then(r => { if (!r.ok) return r.text().then(t => { throw t; }); return r.json(); });
}

function esc(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

// ── Init ──
loadAIManager();
setInterval(loadServerStatus, 5000);
</script>
