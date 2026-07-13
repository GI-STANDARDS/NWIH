<?php
/**
 * PHP API Proxy — relays requests from frontend to Python FastAPI backend.
 * PHP NEVER does any processing — it's purely a communication layer.
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

define('API_BASE', 'http://127.0.0.1:8000');

$action = $_GET['action'] ?? '';

try {
    switch ($action) {
        // ─── Health ────────────────────────────────────────────
        case 'health':
            echo http_get('/health');
            break;

        // ─── Analyze ───────────────────────────────────────────
        case 'analyze':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $body = json_decode(file_get_contents('php://input'), true);
            echo http_post('/analyze', $body);
            break;

        case 'analyze_batch':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $body = json_decode(file_get_contents('php://input'), true);
            echo http_post('/analyze/batch', $body);
            break;

        case 'analyze_channel':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $body = json_decode(file_get_contents('php://input'), true);
            echo http_post('/analyze/channel?' . http_build_query($body), []);
            break;

        case 'analyze_playlist':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $body = json_decode(file_get_contents('php://input'), true);
            echo http_post('/analyze/playlist?' . http_build_query($body), []);
            break;

        // ─── Status ────────────────────────────────────────────
        case 'status':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_get("/status/{$jobId}");
            break;

        case 'result':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_get("/result/{$jobId}");
            break;

        case 'ai_analysis':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_get("/analyze/{$jobId}/ai-analysis");
            break;

        case 'jobs':
            echo http_get('/jobs');
            break;

        // ─── ML Pipeline Status ─────────────────────────────────
        case 'ml_status':
            echo http_get('/ml/status');
            break;

        case 'system_status':
            echo http_get('/system/status');
            break;

        case 'system_diagnostics':
            echo http_get('/system/diagnostics');
            break;

        case 'model_health':
            echo http_get('/model/health');
            break;

        case 'model_scan':
            echo http_get('/model/scan');
            break;

        case 'system_config-validate':
            echo http_get('/system/config-validate');
            break;

        case 'system_dependency-status':
            echo http_get('/system/dependency-status');
            break;

        case 'install_dependency':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $name = $_GET['name'] ?? '';
            if (!$name) throw new Exception('name required');
            echo http_post('/system/install-dependency?name=' . urlencode($name), []);
            break;

        case 'logs':
            $channel = $_GET['channel'] ?? '';
            $count = $_GET['count'] ?? '50';
            $severity = $_GET['severity'] ?? '0';
            $search = $_GET['search'] ?? '';
            $path = "/logs?count={$count}&severity={$severity}";
            if ($channel) $path .= '&channel=' . urlencode($channel);
            if ($search) $path .= '&search=' . urlencode($search);
            echo http_get($path);
            break;

        case 'logs_clear':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $channel = $_GET['channel'] ?? '';
            $path = '/logs/clear';
            if ($channel) $path .= '?channel=' . urlencode($channel);
            echo http_post($path, []);
            break;

        case 'model_delete':
            $filename = $_GET['filename'] ?? '';
            if (!$filename) throw new Exception('filename required');
            echo http_del('/llama/models/delete?filename=' . urlencode($filename));
            break;

        case 'cancel_job':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_get('/cancel/' . urlencode($jobId));
            break;

        // ─── LLM Analyze (on completed jobs) ────────────────────
        case 'analyze_llm':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_post("/analyze/{$jobId}/llm-analyze", []);
            break;

        // ─── Setup / Tools ──────────────────────────────────────
        case 'setup_status':
            echo http_get('/setup/status');
            break;

        case 'setup_cuda':
            echo http_get('/setup/detect-cuda');
            break;

        case 'llama_download_binary':
            // SSE stream - call backend directly
            http_post_raw_llm('/llama/binary/download', []);
            break;

        case 'llama_download_model':
            $body = json_decode(file_get_contents('php://input'), true);
            $modelId = $body['model_id'] ?? '';
            http_post_raw_llm('/llama/model/download', ['model_id' => $modelId]);
            break;

        case 'llama_list_models':
            echo http_get('/llama/models');
            break;

        // ─── Model Manager ────────────────────────────────────────
        case 'model_status':
            echo http_get('/model/status');
            break;

        case 'model_load':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $body = json_decode(file_get_contents('php://input'), true);
            $model = $body['model_name'] ?? '';
            echo http_post('/model/load?model_name=' . urlencode($model), []);
            break;

        case 'model_unload':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            echo http_post('/model/unload', []);
            break;

        case 'model_warm':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            echo http_post('/model/warm', []);
            break;

        // ─── Job Management ──────────────────────────────────────────
        case 'delete_job':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_del('/jobs/' . urlencode($jobId));
            break;

        case 'pause_job':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_post('/jobs/' . urlencode($jobId) . '/pause', []);
            break;

        case 'process_job':
            if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
                throw new Exception('POST required');
            }
            $body = json_decode(file_get_contents('php://input'), true);
            $jobId = $body['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_post('/jobs/' . urlencode($jobId) . '/process', []);
            break;

        case 'resume_job':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_post('/jobs/' . urlencode($jobId) . '/resume', []);
            break;

        case 'restart_job':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_post('/jobs/' . urlencode($jobId) . '/restart', []);
            break;

        case 'export_text':
            $jobId = $_GET['job_id'] ?? '';
            if (!$jobId) throw new Exception('job_id required');
            echo http_post('/jobs/' . urlencode($jobId) . '/export-text', []);
            break;

        default:
            http_response_code(400);
            echo json_encode(['error' => "Unknown action: {$action}"]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}

// ─── HTTP helpers ────────────────────────────────────────────────────────────

function http_post_raw_llm(string $path, array $data): void {
    $url = API_BASE . $path;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 600,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($data),
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: text/event-stream',
        ],
    ]);
    curl_exec($ch);
    curl_close($ch);
}

function http_get(string $path): string {
    $url = API_BASE . $path;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 300,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_HTTPHEADER => ['Accept: application/json'],
    ]);
    $result = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        http_response_code(502);
        return json_encode(['error' => "Backend unreachable: {$error}"]);
    }
    if ($httpCode >= 400) {
        http_response_code($httpCode);
    }
    return $result;
}

function http_del(string $path): string {
    $url = API_BASE . $path;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 300,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_CUSTOMREQUEST => 'DELETE',
        CURLOPT_HTTPHEADER => ['Accept: application/json'],
    ]);
    $result = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    if ($error) {
        http_response_code(502);
        return json_encode(['error' => "Backend unreachable: {$error}"]);
    }
    if ($httpCode >= 400) {
        http_response_code($httpCode);
    }
    return $result;
}

function http_post(string $path, array $data): string {
    $url = API_BASE . $path;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 600,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($data),
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: application/json',
        ],
    ]);
    $result = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        http_response_code(502);
        return json_encode(['error' => "Backend unreachable: {$error}"]);
    }
    if ($httpCode >= 400) {
        http_response_code($httpCode);
    }
    return $result;
}
