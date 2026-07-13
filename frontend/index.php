<?php
/**
 * YT Comment Intelligence — PHP Frontend Router
 * Glassmorphism + Gold Theme | Sci-Fi Dashboard
 */

$page = $_GET['page'] ?? 'dashboard';
$allowed = ['dashboard', 'analyze', 'status', 'results', 'tools', 'ai_manager', 'jobs', 'ai_analysis', 'api'];

if (!in_array($page, $allowed)) {
    $page = 'dashboard';
}

if ($page === 'api') {
    require __DIR__ . '/api.php';
    exit;
}

$pageTitle = ucfirst($page);
$navItems = [
    'dashboard' => ['icon' => '◈', 'label' => 'Dashboard', 'section' => 'core'],
    'analyze'   => ['icon' => '⊕', 'label' => 'New Analysis', 'section' => 'core'],
    'status'    => ['icon' => '⚙', 'label' => 'Jobs', 'section' => 'core'],
    'results'   => ['icon' => '◆', 'label' => 'Results', 'section' => 'core'],
    'jobs'      => ['icon' => '▤', 'label' => 'Jobs History', 'section' => 'core'],
];
$navTools = [
    'ai_manager' => ['icon' => '⬡', 'label' => 'AI Control Center', 'badge' => 'New'],
    'tools'      => ['icon' => '⚙', 'label' => 'Server Tools'],
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YT Comment Intelligence</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

<div class="app-layout">

    <!-- ═══ SIDEBAR ═══ -->
    <aside class="sidebar">
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">AI</div>
            <span class="sidebar-brand-text">CommentIntel</span>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-section-label">Core</div>
            <?php foreach ($navItems as $key => $item): ?>
            <a href="?page=<?= $key ?>"
               class="sidebar-link <?= $page === $key ? 'active' : '' ?>">
                <span class="icon"><?= $item['icon'] ?></span>
                <span><?= $item['label'] ?></span>
            </a>
            <?php endforeach; ?>
            <div class="nav-section-label" style="margin-top:8px;">AI Engine</div>
            <?php foreach ($navTools as $key => $item): ?>
            <a href="?page=<?= $key ?>"
               class="sidebar-link <?= $page === $key ? 'active' : '' ?>">
                <span class="icon"><?= $item['icon'] ?></span>
                <span><?= $item['label'] ?></span>
                <?php if (!empty($item['badge'])): ?>
                <span class="nav-badge"><?= $item['badge'] ?></span>
                <?php endif; ?>
            </a>
            <?php endforeach; ?>
        </nav>
        <div class="sidebar-footer">
            <div class="ai-status-card">
                <div class="ai-status-header">
                    <span class="ai-status-dot unloaded" id="aiStatusDot"></span>
                    <span>AI Engine</span>
                </div>
                <div class="ai-status-model" id="aiStatusName">Checking...</div>
            </div>
        </div>
    </aside>

    <!-- ═══ MAIN ═══ -->
    <div class="main-area">

        <!-- Top Header -->
        <header class="top-header">
            <div class="header-status">
                <span class="header-status-dot" id="headerStatusDot"></span>
                <span id="headerStatusLabel">Checking...</span>
            </div>
            <div class="header-llm-status" id="headerLLMStatus" title="AI Engine Status">
                <span class="header-llm-dot unloaded" id="headerLLMDot"></span>
                <span id="headerLLMLabel">Model: idle</span>
            </div>
            <div class="header-search">
                <input type="text" placeholder="Search analyses, jobs, clusters..." />
            </div>
            <div class="header-actions">
                <a href="?page=analyze" class="btn-gold">+ New Analysis</a>
            </div>
        </header>

        <!-- Page Content -->
        <main class="page-content">
            <?php require __DIR__ . "/pages/{$page}.php"; ?>
        </main>

        <?php if ($page === 'dashboard'): ?>
        <!-- ═══ AI ENGINE STATUS PANEL ═══ -->
        <div class="ai-engine-panel">
            <div class="ai-engine-header">
                <div class="ai-engine-title">
                    <span>⚡ AI Engine Status</span>
                </div>
                <div class="ai-engine-status-badge offline" id="aiEngineBadge">
                    <span class="header-status-dot" id="aiEngineDot" style="width:6px;height:6px;animation:none;"></span>
                    <span id="aiEngineLabel">Checking...</span>
                </div>
            </div>
            <div class="ai-engine-metrics" id="aiEngineMetrics">
                <div class="ai-metric">
                    <div class="ai-metric-value" id="aiMetricModel">—</div>
                    <div class="ai-metric-label">Model</div>
                </div>
                <div class="ai-metric">
                    <div class="ai-metric-value" id="aiMetricBackend">—</div>
                    <div class="ai-metric-label">Backend</div>
                </div>
                <div class="ai-metric">
                    <div class="ai-metric-value" id="aiMetricPort">—</div>
                    <div class="ai-metric-label">Server Port</div>
                </div>
                <div class="ai-metric">
                    <div class="ai-metric-value" id="aiMetricIdle">—</div>
                    <div class="ai-metric-label">Idle Timeout</div>
                </div>
                <div class="ai-metric">
                    <div class="ai-metric-value" id="aiMetricBinary">—</div>
                    <div class="ai-metric-label">llama.cpp</div>
                </div>
            </div>
            <div class="ai-engine-actions">
                <button class="btn-ai load" onclick="modelActionFromDash('load')">⬡ Load Model</button>
                <button class="btn-ai" onclick="modelActionFromDash('unload')">⏹ Unload</button>
                <button class="btn-ai" onclick="modelActionFromDash('warm')">⟳ Warm GPU</button>
                <a href="?page=tools" class="btn-ai" style="margin-left:auto;">AI Manager →</a>
            </div>
        </div>
        <?php endif; ?>

        <footer class="footer">
            YT Comment Intelligence Engine v2.0 &mdash; FastAPI + FAISS + llama.cpp &mdash; AI-Powered Market Intelligence
        </footer>

    </div>

</div>

<script src="assets/js/app.js"></script>
</body>
</html>
