/* ══════════════════════════════════════════════════════════
   DecryptTrace – Frontend Application Logic
   ══════════════════════════════════════════════════════════ */

// Auto-detect API: use Render backend when on GitHub Pages, localhost for local dev
const RENDER_API = 'https://decrypttrace-api.onrender.com/api';
const LOCAL_API  = 'http://127.0.0.1:5000/api';
const API = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:')
  ? LOCAL_API
  : RENDER_API;
let AUTH_TOKEN = localStorage.getItem('dt_token') || null;
let CURRENT_USER = JSON.parse(localStorage.getItem('dt_user') || 'null');
let SELECTED_FILE = null;

// ─────────────────────────────────────────────────────────
// Particle Background
// ─────────────────────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  const ctx = canvas.getContext('2d');
  let particles = [];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function Particle() {
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.r = Math.random() * 1.5 + 0.3;
    this.vx = (Math.random() - 0.5) * 0.3;
    this.vy = (Math.random() - 0.5) * 0.3;
    this.alpha = Math.random() * 0.4 + 0.1;
  }

  for (let i = 0; i < 90; i++) particles.push(new Particle());

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(99,102,241,${p.alpha})`;
      ctx.fill();
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    });

    // draw faint connection lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 100) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(99,102,241,${0.05 * (1 - dist / 100)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
})();

// ─────────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────────
function apiCall(endpoint, method = 'GET', body = null, isFormData = false) {
  const headers = {};
  if (AUTH_TOKEN) headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
  if (!isFormData && body) headers['Content-Type'] = 'application/json';

  return fetch(`${API}${endpoint}`, {
    method,
    headers,
    body: body ? (isFormData ? body : JSON.stringify(body)) : undefined
  }).then(async res => {
    const data = res.headers.get('content-type')?.includes('application/json')
      ? await res.json()
      : { _raw: res };
    if (!res.ok) throw { status: res.status, data };
    return { data, res };
  });
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

function formatDate(dateStr) {
  if (!dateStr) return '–';
  return new Date(dateStr).toLocaleString('en-IN', {
    dateStyle: 'medium', timeStyle: 'short'
  });
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

function truncHash(hash, len = 16) {
  if (!hash) return '–';
  return hash.slice(0, len) + '…';
}

function roleChip(role) {
  const cls = { admin: 'role-admin', auditor: 'role-auditor', user: 'role-user' };
  return `<span class="chip ${cls[role] || 'chip-violet'}">${role}</span>`;
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  const text = btn.querySelector('.btn-text');
  const spinner = btn.querySelector('.btn-spinner');
  btn.disabled = loading;
  if (text) text.classList.toggle('hidden', loading);
  if (spinner) spinner.classList.toggle('hidden', !loading);
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.classList.remove('hidden');
}

function hideError(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.add('hidden');
}

function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text'; btn.textContent = '🙈';
  } else {
    input.type = 'password'; btn.textContent = '👁';
  }
}

// ─────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────
function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
  document.getElementById(`tab-${tab}`).classList.add('active');
  document.getElementById(`${tab}-form`).classList.add('active');
}

async function handleLogin(e) {
  e.preventDefault();
  hideError('login-error');
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  setLoading('login-btn', true);

  try {
    const { data } = await apiCall('/auth/login', 'POST', { username, password });
    AUTH_TOKEN = data.token;
    CURRENT_USER = data.user;
    localStorage.setItem('dt_token', AUTH_TOKEN);
    localStorage.setItem('dt_user', JSON.stringify(CURRENT_USER));
    showToast('Login successful! Welcome back.', 'success');
    initApp();
  } catch (err) {
    showError('login-error', err?.data?.error || 'Login failed. Please check your credentials.');
  } finally {
    setLoading('login-btn', false);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  hideError('register-error');
  const username = document.getElementById('reg-username').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const role     = document.getElementById('reg-role').value;

  if (password.length < 6) {
    showError('register-error', 'Password must be at least 6 characters.');
    return;
  }
  setLoading('register-btn', true);

  try {
    const { data } = await apiCall('/auth/register', 'POST', { username, email, password, role });
    AUTH_TOKEN = data.token;
    CURRENT_USER = data.user;
    localStorage.setItem('dt_token', AUTH_TOKEN);
    localStorage.setItem('dt_user', JSON.stringify(CURRENT_USER));
    showToast('Account created! RSA key pair generated.', 'success');
    initApp();
  } catch (err) {
    showError('register-error', err?.data?.error || 'Registration failed.');
  } finally {
    setLoading('register-btn', false);
  }
}

function handleLogout() {
  AUTH_TOKEN = null;
  CURRENT_USER = null;
  localStorage.removeItem('dt_token');
  localStorage.removeItem('dt_user');
  document.getElementById('app-screen').classList.remove('active');
  document.getElementById('auth-screen').classList.add('active');
  showToast('Signed out successfully.', 'info');
}

// ─────────────────────────────────────────────────────────
// App Shell / Navigation
// ─────────────────────────────────────────────────────────
function initApp() {
  document.getElementById('auth-screen').classList.remove('active');
  document.getElementById('app-screen').classList.add('active');

  const user = CURRENT_USER;
  // Sidebar user info
  document.getElementById('sidebar-username').textContent = user.username;
  document.getElementById('sidebar-avatar').textContent = user.username[0].toUpperCase();
  const roleEl = document.getElementById('sidebar-role');
  roleEl.textContent = user.role;
  roleEl.className = `user-role-badge role-${user.role}`;
  document.getElementById('dash-greeting').textContent = `Welcome back, ${user.username}!`;

  // Admin nav visibility
  if (user.role === 'admin') {
    document.getElementById('nav-admin').style.display = '';
    document.getElementById('stat-card-users').style.display = '';
  }

  showPage('dashboard');
}

function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`page-${name}`).classList.add('active');
  const navEl = document.getElementById(`nav-${name}`);
  if (navEl) navEl.classList.add('active');

  // Close sidebar on mobile
  document.getElementById('sidebar').classList.remove('open');

  // Lazy load page data
  if (name === 'dashboard')   loadDashboard();
  if (name === 'files')       loadFiles();
  if (name === 'provenance')  loadProvenance();
  if (name === 'ledger')      loadLedger();
  if (name === 'admin' && CURRENT_USER?.role === 'admin') loadAdmin();
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

function closeModal(id) {
  document.getElementById(`${id}-overlay`).classList.add('hidden');
}

// ─────────────────────────────────────────────────────────
// Dashboard
// ─────────────────────────────────────────────────────────
async function loadDashboard() {
  // Load files count
  try {
    const { data: filesData } = await apiCall('/files/');
    document.getElementById('stat-files').textContent = filesData.files?.length ?? 0;
  } catch { document.getElementById('stat-files').textContent = '–'; }

  // Load provenance count
  try {
    const { data: proData } = await apiCall('/provenance/records');
    document.getElementById('stat-decryptions').textContent = proData.records?.length ?? 0;
    renderDashboardRecent(proData.records?.slice(0, 5) || []);
  } catch { document.getElementById('stat-decryptions').textContent = '–'; }

  // Load admin stats
  if (CURRENT_USER?.role === 'admin') {
    try {
      const { data: stats } = await apiCall('/admin/stats');
      document.getElementById('stat-users').textContent = stats.stats?.total_users ?? 0;
    } catch {}
  }

  // Ledger status
  if (CURRENT_USER?.role === 'admin' || CURRENT_USER?.role === 'auditor') {
    try {
      const { data: ledger } = await apiCall('/provenance/ledger/verify');
      document.getElementById('stat-ledger').textContent = ledger.total_blocks ?? 0;
      renderLedgerStatus(ledger);
    } catch { document.getElementById('stat-ledger').textContent = '–'; }
  } else {
    document.getElementById('stat-ledger').textContent = '–';
    document.getElementById('ledger-status-card').innerHTML =
      '<div class="loading-state" style="padding:1.5rem">Ledger view requires Admin or Auditor role</div>';
  }
}

function renderDashboardRecent(records) {
  const el = document.getElementById('dashboard-recent');
  if (!records.length) {
    el.innerHTML = '<div class="empty-state">No decryption events yet. Upload a file and decrypt it to see records here.</div>';
    return;
  }
  el.innerHTML = `
    <table>
      <thead><tr>
        <th>#</th><th>File</th><th>Decrypted By</th><th>Time</th><th>Status</th>
      </tr></thead>
      <tbody>
        ${records.map(r => `
          <tr>
            <td><span class="text-mono">#${r.id}</span></td>
            <td><span class="truncate" title="${r.file_name}">${r.file_name}</span></td>
            <td>${r.decryptor_name || '–'}</td>
            <td>${formatDate(r.decrypted_at)}</td>
            <td><span class="chip chip-green">✓ Logged</span></td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

function renderLedgerStatus(ledger) {
  const el = document.getElementById('ledger-status-card');
  const valid = ledger.valid;
  el.innerHTML = `
    <div class="ledger-status-row">
      <span style="font-size:1.75rem">${valid ? '⛓️' : '⚠️'}</span>
      <div>
        <div style="font-weight:700;font-size:1rem;color:${valid ? '#34d399' : '#f87171'}">
          ${valid ? 'Ledger Intact – No Tampering Detected' : `Tamper Detected at Block #${ledger.tampered_at}`}
        </div>
        <div style="font-size:.8rem;color:var(--text-secondary);margin-top:.2rem">
          Total blocks: <strong>${ledger.total_blocks}</strong>
        </div>
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────
// Files Page
// ─────────────────────────────────────────────────────────
async function loadFiles() {
  const el = document.getElementById('files-table');
  el.innerHTML = '<div class="loading-state">Loading files…</div>';
  try {
    const { data } = await apiCall('/files/');
    const files = data.files || [];
    if (!files.length) {
      el.innerHTML = '<div class="empty-state">No files uploaded yet. <a href="#" onclick="showPage(\'upload\')" style="color:var(--accent-violet)">Upload your first file.</a></div>';
      return;
    }
    el.innerHTML = `
      <table>
        <thead><tr>
          <th>ID</th><th>Filename</th><th>SHA-256 Hash</th><th>Uploaded By</th><th>Date</th><th>Actions</th>
        </tr></thead>
        <tbody>
          ${files.map(f => `
            <tr>
              <td><span class="text-mono">#${f.id}</span></td>
              <td><strong>${f.original_name}</strong></td>
              <td><span class="hash-display" title="${f.file_hash}">${truncHash(f.file_hash)}</span></td>
              <td>${f.uploader_name || '–'}</td>
              <td>${formatDate(f.uploaded_at)}</td>
              <td>
                <button class="btn-sm btn-sm-cyan" onclick="decryptFile(${f.id}, '${f.original_name}')">🔓 Decrypt</button>
              </td>
            </tr>`).join('')}
        </tbody>
      </table>`;
  } catch (err) {
    el.innerHTML = `<div class="empty-state">Failed to load files: ${err?.data?.error || 'Unknown error'}</div>`;
  }
}

// ─────────────────────────────────────────────────────────
// Upload / Encrypt
// ─────────────────────────────────────────────────────────
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) setSelectedFile(file);
}

function handleDrop(event) {
  event.preventDefault();
  document.getElementById('drop-zone').classList.remove('drag-over');
  const file = event.dataTransfer.files[0];
  if (file) setSelectedFile(file);
}

function setSelectedFile(file) {
  SELECTED_FILE = file;
  document.getElementById('preview-name').textContent = file.name;
  document.getElementById('preview-size').textContent = formatBytes(file.size);
  document.getElementById('file-preview').classList.remove('hidden');
  document.getElementById('upload-btn').disabled = false;
  document.getElementById('upload-success').classList.add('hidden');
  hideError('upload-error');
}

function clearFileSelection() {
  SELECTED_FILE = null;
  document.getElementById('file-input').value = '';
  document.getElementById('file-preview').classList.add('hidden');
  document.getElementById('upload-btn').disabled = true;
}

async function uploadFile() {
  if (!SELECTED_FILE) return;
  hideError('upload-error');
  document.getElementById('upload-progress').classList.remove('hidden');
  document.getElementById('upload-btn').disabled = true;

  const bar = document.getElementById('upload-progress-bar');
  bar.style.width = '30%';

  const formData = new FormData();
  formData.append('file', SELECTED_FILE);

  try {
    bar.style.width = '70%';
    const { data } = await apiCall('/files/upload', 'POST', formData, true);
    bar.style.width = '100%';

    setTimeout(() => {
      document.getElementById('upload-progress').classList.add('hidden');
      bar.style.width = '0';
    }, 500);

    const successEl = document.getElementById('upload-success');
    successEl.classList.remove('hidden');
    successEl.innerHTML = `
      ✅ <strong>${data.file.original_name}</strong> encrypted and stored!<br>
      SHA-256: <span class="hash-display">${data.file.file_hash}</span>`;

    showToast(`File "${data.file.original_name}" encrypted with AES-256!`, 'success');
    clearFileSelection();
  } catch (err) {
    bar.style.width = '0';
    document.getElementById('upload-progress').classList.add('hidden');
    showError('upload-error', err?.data?.error || 'Upload failed. Please try again.');
    document.getElementById('upload-btn').disabled = false;
  }
}

// ─────────────────────────────────────────────────────────
// Decrypt & Record Provenance
// ─────────────────────────────────────────────────────────
async function decryptFile(fileId, filename) {
  showToast(`Decrypting "${filename}"... Recording provenance...`, 'info');
  try {
    const { res } = await apiCall(`/provenance/decrypt/${fileId}`, 'POST', {}, false);

    // Get provenance headers from the response (but data is a binary blob)
    const recordId   = res.headers.get('X-Provenance-Record-Id');
    const eventHash  = res.headers.get('X-Event-Hash');
    const ledgerIdx  = res.headers.get('X-Ledger-Block');
    const hashMatch  = res.headers.get('X-Hash-Verified');

    // Trigger download
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    a.click();
    URL.revokeObjectURL(url);

    showToast(`✅ Decrypted! Record #${recordId} added to ledger block #${ledgerIdx}.`, 'success');

    // Show modal with provenance info
    showProvenanceModal({ recordId, eventHash, ledgerIdx, hashMatch, filename });

    // Refresh files page
    if (document.getElementById('page-files').classList.contains('active')) loadFiles();
  } catch (err) {
    const msg = err?.data?.error || 'Decryption failed or access denied.';
    showToast(msg, 'error');
  }
}

function showProvenanceModal({ recordId, eventHash, ledgerIdx, hashMatch, filename }) {
  const content = document.getElementById('record-modal-content');
  content.innerHTML = `
    <h3 style="font-size:1.1rem;font-weight:700;margin-bottom:1.25rem;
               background:var(--grad-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent">
      🔗 Provenance Record Created
    </h3>
    <div class="verify-meta">
      <div class="verify-meta-row">
        <span class="verify-meta-label">File</span>
        <span class="verify-meta-value">${filename}</span>
      </div>
      <div class="verify-meta-row">
        <span class="verify-meta-label">Record ID</span>
        <span class="verify-meta-value">#${recordId}</span>
      </div>
      <div class="verify-meta-row">
        <span class="verify-meta-label">Event Hash</span>
        <span class="verify-meta-value">${eventHash || '–'}</span>
      </div>
      <div class="verify-meta-row">
        <span class="verify-meta-label">Ledger Block</span>
        <span class="verify-meta-value">#${ledgerIdx}</span>
      </div>
      <div class="verify-meta-row">
        <span class="verify-meta-label">Hash Match</span>
        <span class="verify-meta-value">${hashMatch === 'True' ? '✅ Verified' : '⚠️ Mismatch'}</span>
      </div>
    </div>
    <p style="font-size:.8rem;color:var(--text-secondary);margin-top:1rem">
      This event is digitally signed and recorded in the immutable ledger. Use the <strong>Verify Record</strong> page to confirm authenticity.
    </p>
    <button class="btn-primary" style="margin-top:1rem" onclick="closeModal('record-modal');showPage('verify');document.getElementById('verify-record-id').value='${recordId}'">
      🔎 Verify This Record
    </button>`;
  document.getElementById('record-modal-overlay').classList.remove('hidden');
}

// ─────────────────────────────────────────────────────────
// Provenance Records Page
// ─────────────────────────────────────────────────────────
async function loadProvenance() {
  const el = document.getElementById('provenance-table');
  el.innerHTML = '<div class="loading-state">Loading records…</div>';
  try {
    const { data } = await apiCall('/provenance/records');
    const records = data.records || [];
    if (!records.length) {
      el.innerHTML = '<div class="empty-state">No provenance records yet. Decrypt a file to create the first record.</div>';
      return;
    }
    el.innerHTML = `
      <table>
        <thead><tr>
          <th>ID</th><th>File</th><th>Decrypted By</th><th>Timestamp</th>
          <th>Event Hash</th><th>Ledger Block</th><th>Actions</th>
        </tr></thead>
        <tbody>
          ${records.map(r => `
            <tr>
              <td><span class="text-mono">#${r.id}</span></td>
              <td><span class="truncate" title="${r.file_name}">${r.file_name}</span></td>
              <td>${r.decryptor_name || '–'}</td>
              <td>${formatDate(r.decrypted_at)}</td>
              <td><span class="hash-display">${truncHash(r.event_hash)}</span></td>
              <td>${r.ledger_index !== null ? `<span class="chip chip-cyan">Block #${r.ledger_index}</span>` : '–'}</td>
              <td>
                <button class="btn-sm btn-sm-violet" onclick="openRecordDetail(${r.id})">🔍 Details</button>
              </td>
            </tr>`).join('')}
        </tbody>
      </table>`;
  } catch (err) {
    el.innerHTML = `<div class="empty-state">Error loading records: ${err?.data?.error || 'Unknown'}</div>`;
  }
}

async function openRecordDetail(recordId) {
  const content = document.getElementById('record-modal-content');
  content.innerHTML = '<div class="loading-state">Loading record details…</div>';
  document.getElementById('record-modal-overlay').classList.remove('hidden');

  try {
    const { data } = await apiCall(`/provenance/records/${recordId}`);
    const r = data.record;
    const sigIcon    = r.signature_valid ? '✅' : '❌';
    const ledgerIcon = r.ledger_block_valid ? '✅' : '❌';

    content.innerHTML = `
      <h3 style="font-size:1.1rem;font-weight:700;margin-bottom:1.25rem;
                 background:var(--grad-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent">
        Provenance Record #${r.id}
      </h3>
      <div class="verify-checks" style="margin-bottom:1rem">
        <div class="verify-check">${sigIcon} <strong>Digital Signature:</strong>&nbsp;${r.signature_valid ? 'Valid' : 'INVALID'}</div>
        <div class="verify-check">${ledgerIcon} <strong>Ledger Block:</strong>&nbsp;${r.ledger_block_valid ? 'Intact' : 'TAMPERED'}</div>
      </div>
      <div class="verify-meta">
        <div class="verify-meta-row"><span class="verify-meta-label">File</span><span class="verify-meta-value">${r.file_name}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Decrypted By</span><span class="verify-meta-value">${r.decryptor_name}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Timestamp</span><span class="verify-meta-value">${formatDate(r.decrypted_at)}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">File Hash</span><span class="verify-meta-value">${r.file_hash}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Event Hash</span><span class="verify-meta-value">${r.event_hash}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Ledger Index</span><span class="verify-meta-value">${r.ledger_index ?? '–'}</span></div>
        <div class="verify-meta-row">
          <span class="verify-meta-label">Signature</span>
          <span class="verify-meta-value" style="font-size:.65rem">${r.signature?.slice(0, 80)}…</span>
        </div>
      </div>
      <button class="btn-primary" style="margin-top:1.25rem"
        onclick="closeModal('record-modal');showPage('verify');document.getElementById('verify-record-id').value='${r.id}'">
        🔎 Full Verification
      </button>`;
  } catch (err) {
    content.innerHTML = `<div class="empty-state">Failed to load record: ${err?.data?.error || 'Unknown'}</div>`;
  }
}

// ─────────────────────────────────────────────────────────
// Verify Page
// ─────────────────────────────────────────────────────────
async function verifyRecord() {
  const id = document.getElementById('verify-record-id').value;
  if (!id || id < 1) {
    showToast('Please enter a valid record ID.', 'error');
    return;
  }

  const resultEl = document.getElementById('verify-result');
  resultEl.className = 'verify-result';
  resultEl.classList.remove('hidden');
  resultEl.innerHTML = '<div class="loading-state" style="padding:1rem">Verifying…</div>';

  try {
    const { data } = await apiCall(`/provenance/verify/${id}`, 'POST');

    const valid = data.overall_valid;
    const checks = data.checks;
    const meta = data.metadata;

    resultEl.className = `verify-result ${valid ? 'verify-valid' : 'verify-invalid'}`;
    resultEl.innerHTML = `
      <div class="verify-status">
        <span class="verify-status-icon">${valid ? '✅' : '❌'}</span>
        <div>
          <div style="font-size:1.1rem">${valid ? 'AUTHENTIC – Record Verified' : 'TAMPER DETECTED – Record Invalid'}</div>
          <div style="font-size:.8rem;color:var(--text-secondary)">Record #${data.record_id}</div>
        </div>
      </div>

      <div class="verify-checks">
        <div class="verify-check">
          <span class="check-icon">${checks.signature_valid ? '✅' : '❌'}</span>
          <span>RSA Digital Signature: <strong>${checks.signature_valid ? 'Valid' : 'INVALID'}</strong></span>
        </div>
        <div class="verify-check">
          <span class="check-icon">${checks.ledger_block_valid ? '✅' : '❌'}</span>
          <span>Ledger Block Integrity: <strong>${checks.ledger_block_valid ? 'Intact' : 'TAMPERED'}</strong></span>
        </div>
        <div class="verify-check">
          <span class="check-icon">${checks.event_hash_valid ? '✅' : '❌'}</span>
          <span>Event Hash Format: <strong>${checks.event_hash_valid ? 'Valid SHA-256' : 'INVALID'}</strong></span>
        </div>
      </div>

      <div class="verify-meta">
        <div class="verify-meta-row"><span class="verify-meta-label">File</span><span class="verify-meta-value">${meta.file_name}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Decrypted By</span><span class="verify-meta-value">${meta.decrypted_by}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Timestamp</span><span class="verify-meta-value">${formatDate(meta.decrypted_at)}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Event Hash</span><span class="verify-meta-value">${meta.event_hash}</span></div>
        <div class="verify-meta-row"><span class="verify-meta-label">Ledger Block</span><span class="verify-meta-value">#${meta.ledger_index ?? '–'}</span></div>
      </div>`;

    showToast(valid ? 'Record is authentic!' : '⚠️ Tampering detected!', valid ? 'success' : 'error');
  } catch (err) {
    resultEl.className = 'verify-result verify-invalid';
    resultEl.innerHTML = `<div class="verify-status"><span class="verify-status-icon">❌</span>
      <div>${err?.data?.error || 'Verification failed. Record may not exist.'}</div></div>`;
  }
}

// ─────────────────────────────────────────────────────────
// Ledger Page
// ─────────────────────────────────────────────────────────
async function loadLedger() {
  const el = document.getElementById('ledger-blocks');
  el.innerHTML = '<div class="loading-state">Loading ledger…</div>';

  if (CURRENT_USER?.role === 'user') {
    el.innerHTML = '<div class="empty-state">Ledger view requires Admin or Auditor role.</div>';
    return;
  }

  try {
    const { data } = await apiCall('/provenance/ledger');
    const blocks = data.ledger || [];
    if (!blocks.length) {
      el.innerHTML = '<div class="empty-state">Ledger is empty. No blocks yet.</div>';
      return;
    }
    el.innerHTML = blocks.map(block => renderBlock(block)).join('');
  } catch (err) {
    el.innerHTML = `<div class="empty-state">Error: ${err?.data?.error || 'Failed to load ledger.'}</div>`;
  }
}

function renderBlock(block) {
  const isGenesis = block.index === 0;
  const typeTag = block.data?.type === 'GENESIS'
    ? '<span class="chip chip-amber">GENESIS</span>'
    : '<span class="chip chip-cyan">PROVENANCE</span>';

  const dataInfo = isGenesis ? block.data?.message :
    `Decrypted by <strong>${block.data?.decrypted_by_username || '–'}</strong> — File: ${block.data?.file_name || '–'}`;

  return `
    <div class="ledger-block">
      <div class="block-header">
        <span class="block-index">Block #${block.index}</span>
        <div style="display:flex;gap:.5rem;align-items:center">
          ${typeTag}
          <span class="block-time">${formatDate(block.timestamp)}</span>
        </div>
      </div>
      <div class="block-hash">🔗 Hash: ${block.hash}</div>
      <div class="block-hash" style="color:var(--text-muted)">⬅ Prev: ${block.previous_hash?.slice(0,32)}…</div>
      <div class="block-data">${dataInfo}</div>
    </div>`;
}

async function verifyFullLedger() {
  if (CURRENT_USER?.role === 'user') {
    showToast('Requires Admin or Auditor role.', 'error');
    return;
  }

  const banner = document.getElementById('ledger-verify-banner');
  banner.innerHTML = 'Verifying chain…';
  banner.className = 'ledger-verify-banner banner-valid';
  banner.classList.remove('hidden');

  try {
    const { data } = await apiCall('/provenance/ledger/verify');
    const valid = data.valid;
    banner.className = `ledger-verify-banner ${valid ? 'banner-valid' : 'banner-invalid'}`;
    banner.innerHTML = valid
      ? `⛓️ Chain Verified — All ${data.total_blocks} blocks intact. No tampering detected.`
      : `❌ Tamper Detected! Block #${data.tampered_at} has been modified. Chain is broken.`;
    showToast(valid ? 'Ledger chain is intact!' : 'TAMPER DETECTED in ledger!', valid ? 'success' : 'error');
  } catch (err) {
    banner.className = 'ledger-verify-banner banner-invalid';
    banner.innerHTML = `❌ Verification failed: ${err?.data?.error || 'Unknown error'}`;
  }
}

// ─────────────────────────────────────────────────────────
// Admin Page
// ─────────────────────────────────────────────────────────
async function loadAdmin() {
  loadAdminUsers();
  loadAdminLogs();
}

async function loadAdminUsers() {
  const el = document.getElementById('admin-users-table');
  el.innerHTML = '<div class="loading-state">Loading users…</div>';
  try {
    const { data } = await apiCall('/admin/users');
    const users = data.users || [];
    el.innerHTML = `
      <table>
        <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Joined</th><th>Actions</th></tr></thead>
        <tbody>
          ${users.map(u => `
            <tr>
              <td><span class="text-mono">#${u.id}</span></td>
              <td><strong>${u.username}</strong></td>
              <td style="color:var(--text-secondary)">${u.email}</td>
              <td>${roleChip(u.role)}</td>
              <td>${formatDate(u.created_at)}</td>
              <td>
                <select class="role-select" id="role-sel-${u.id}" style="
                  background:var(--bg-elevated);border:1px solid var(--border);
                  color:var(--text-primary);border-radius:6px;padding:.3rem .5rem;
                  font-family:inherit;font-size:.78rem;margin-right:.35rem">
                  <option value="user"    ${u.role==='user'    ? 'selected':''}>user</option>
                  <option value="auditor" ${u.role==='auditor' ? 'selected':''}>auditor</option>
                  <option value="admin"   ${u.role==='admin'   ? 'selected':''}>admin</option>
                </select>
                <button class="btn-sm btn-sm-violet" onclick="changeUserRole(${u.id})">Save</button>
              </td>
            </tr>`).join('')}
        </tbody>
      </table>`;
  } catch (err) {
    el.innerHTML = `<div class="empty-state">Error: ${err?.data?.error}</div>`;
  }
}

async function changeUserRole(userId) {
  const role = document.getElementById(`role-sel-${userId}`).value;
  try {
    await apiCall(`/admin/users/${userId}/role`, 'PUT', { role });
    showToast(`Role updated to "${role}"`, 'success');
    loadAdminUsers();
  } catch (err) {
    showToast(err?.data?.error || 'Failed to update role.', 'error');
  }
}

async function loadAdminLogs() {
  const el = document.getElementById('admin-logs-table');
  el.innerHTML = '<div class="loading-state">Loading logs…</div>';
  try {
    const { data } = await apiCall('/admin/logs?limit=50');
    const logs = data.logs || [];
    el.innerHTML = `
      <table>
        <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Status</th></tr></thead>
        <tbody>
          ${logs.map(l => `
            <tr>
              <td style="white-space:nowrap">${formatDate(l.timestamp)}</td>
              <td>${l.username || '<span style="color:var(--text-muted)">anonymous</span>'}</td>
              <td><code style="font-size:.75rem;color:var(--accent-cyan)">${l.action}</code></td>
              <td>${l.success ? '<span class="chip chip-green">✓</span>' : '<span class="chip chip-red">✗</span>'}</td>
            </tr>`).join('')}
        </tbody>
      </table>`;
  } catch (err) {
    el.innerHTML = `<div class="empty-state">Error: ${err?.data?.error}</div>`;
  }
}

// ─────────────────────────────────────────────────────────
// Bootstrap
// ─────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // Remove loader
  setTimeout(() => {
    document.getElementById('page-loader').classList.add('fade-out');
  }, 800);

  // Auto-login if token stored
  if (AUTH_TOKEN && CURRENT_USER) {
    setTimeout(initApp, 900);
  } else {
    // Seed demo users on first load
    seedDemoUsers();
  }
});

async function seedDemoUsers() {
  // Create demo admin if not exists (silently)
  try {
    await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'admin', email: 'admin@decrypttrace.io', password: 'admin123', role: 'admin' })
    });
  } catch {}
  try {
    await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'user', email: 'user@decrypttrace.io', password: 'user123', role: 'user' })
    });
  } catch {}
}
