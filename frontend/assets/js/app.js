/**
 * YT Comment Intelligence — Futuristic Dashboard JS
 * Theme: Glassmorphism + Gold + Dark
 */

const API_BASE = 'api.php';

function apiGet(action, params = {}) {
  const qs = new URLSearchParams({ action, ...params }).toString();
  return fetch(`${API_BASE}?${qs}`).then(r => r.json());
}

function apiPost(action, data) {
  return fetch(`${API_BASE}?action=${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json());
}

// ── Escape HTML ──
function esc(text) {
  if (!text) return '';
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

// ── Format number ──
function fmt(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return n?.toLocaleString() || '0';
}

// ── Health + System Status ──
function checkHealth() {
  apiGet('health')
    .then(data => {
      const dot = document.getElementById('headerStatusDot');
      const label = document.getElementById('headerStatusLabel');
      if (dot) {
        dot.className = 'header-status-dot' + (data.status === 'ok' ? '' : ' offline');
      }
      if (label) label.textContent = data.status === 'ok' ? 'System Online' : 'System Error';
    })
    .catch(() => {
      const dot = document.getElementById('headerStatusDot');
      if (dot) dot.className = 'header-status-dot offline';
      const label = document.getElementById('headerStatusLabel');
      if (label) label.textContent = 'Offline';
    });
}

// ── Sidebar AI Model Status ──
function loadSidebarAIStatus() {
  apiGet('model_status')
    .then(data => {
      const dot = document.getElementById('aiStatusDot');
      const name = document.getElementById('aiStatusName');
      if (dot) {
        if (data.loaded) dot.className = 'ai-status-dot loaded';
        else if (data.server_running) dot.className = 'ai-status-dot idle';
        else dot.className = 'ai-status-dot unloaded';
      }
      if (name) {
        name.textContent = data.loaded
          ? (data.model_name || 'llama.cpp loaded')
          : 'Model unloaded';
      }
      // Also update header LLM status
      const hdot = document.getElementById('headerLLMDot');
      const hlabel = document.getElementById('headerLLMLabel');
      if (hdot) {
        if (data.loaded) hdot.className = 'header-llm-dot loaded';
        else if (data.server_running) hdot.className = 'header-llm-dot idle';
        else hdot.className = 'header-llm-dot unloaded';
      }
      if (hlabel) {
        hlabel.textContent = data.loaded
          ? (data.model_name || 'llama.cpp loaded')
          : (data.server_running ? 'Server: idle' : 'Model: unloaded');
      }
    })
    .catch(() => {
      const dot = document.getElementById('aiStatusDot');
      if (dot) dot.className = 'ai-status-dot unloaded';
      const name = document.getElementById('aiStatusName');
      if (name) name.textContent = 'Offline';
      const hdot = document.getElementById('headerLLMDot');
      if (hdot) hdot.className = 'header-llm-dot unloaded';
      const hlabel = document.getElementById('headerLLMLabel');
      if (hlabel) hlabel.textContent = 'Model: offline';
    });
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  loadSidebarAIStatus();
  setInterval(checkHealth, 30000);
  setInterval(loadSidebarAIStatus, 15000);
});
