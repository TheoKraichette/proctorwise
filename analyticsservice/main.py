import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from interface.api.controllers import analytics_controller

_PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")


def _rewrite_urls(html: str) -> str:
    if _PUBLIC_HOST == "localhost":
        return html
    base = f"https://{_PUBLIC_HOST}"
    # Step 1: API URLs (with path after port) - remove port, keep path
    for port in ["8000", "8001", "8003", "8004", "8005", "8006"]:
        html = html.replace(f"http://localhost:{port}/", f"{base}/")
    # Step 2: Page URLs (no path after port) - map to nginx paths
    html = html.replace("http://localhost:8001", base)
    html = html.replace("http://localhost:8000", f"{base}/app")
    html = html.replace("http://localhost:8003", f"{base}/proctor")
    html = html.replace("http://localhost:8005", f"{base}/notifs")
    html = html.replace("http://localhost:8006", f"{base}/admin")
    html = html.replace("http://localhost:8004", base)
    return html


app = FastAPI(
    title="ProctorWise Analytics Service",
    description="Analytics and reporting service for exam performance and platform metrics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_controller.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "analytics"}


@app.get("/", response_class=HTMLResponse)
async def home():
    html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProctorWise - Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding-top: 80px; padding-left: 20px; padding-right: 20px; padding-bottom: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }

        /* Navbar */
        .navbar { position: fixed; top: 0; left: 0; right: 0; height: 60px; background: rgba(255,255,255,0.98); box-shadow: 0 2px 20px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between; padding: 0 30px; z-index: 1000; }
        .navbar-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: #333; font-weight: bold; font-size: 18px; }
        .navbar-brand:hover { color: #667eea; }
        .navbar-brand .logo { font-size: 24px; }
        .navbar-nav { display: flex; align-items: center; gap: 8px; }
        .nav-link { padding: 8px 16px; border-radius: 8px; text-decoration: none; color: #555; font-size: 14px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
        .nav-link:hover { background: #f0f0f0; color: #333; }
        .nav-link.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; }
        .nav-link .nav-icon { font-size: 16px; }
        .navbar-user { display: flex; align-items: center; gap: 12px; }
        .user-name { color: #333; font-size: 14px; }

        /* Notification Bell */
        .notif-bell { position: relative; cursor: pointer; font-size: 20px; padding: 8px; border-radius: 50%; transition: background 0.2s; text-decoration: none; }
        .notif-bell:hover { background: #f0f0f0; }
        .notif-badge { position: absolute; top: 2px; right: 2px; background: #e94560; color: white; font-size: 10px; font-weight: bold; min-width: 16px; height: 16px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
        .notif-badge.hidden { display: none; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding: 20px; background: white; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header h1 { color: #333; font-size: 24px; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .btn-logout { padding: 8px 16px; background: #e94560; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .btn-refresh { padding: 8px 16px; background: #f0f0f0; color: #333; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; display: flex; align-items: center; gap: 6px; }
        .btn-refresh:hover { background: #e0e0e0; }
        .btn-refresh.loading svg { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        /* KPI Cards */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .kpi-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: transform 0.2s; }
        .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
        .kpi-icon { font-size: 32px; margin-bottom: 10px; }
        .kpi-value { font-size: 36px; font-weight: bold; color: #333; }
        .kpi-label { font-size: 14px; color: #666; margin-top: 5px; }
        .kpi-card.users { border-left: 4px solid #667eea; }
        .kpi-card.exams { border-left: 4px solid #764ba2; }
        .kpi-card.submissions { border-left: 4px solid #11998e; }
        .kpi-card.sessions { border-left: 4px solid #e74c3c; }
        .kpi-card.anomalies { border-left: 4px solid #f39c12; }
        .kpi-card.active { border-left: 4px solid #27ae60; }

        /* Alerts */
        .alerts-container { margin-bottom: 20px; }
        .alert { padding: 15px 20px; border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; gap: 12px; background: white; }
        .alert-warning { border-left: 4px solid #f39c12; }
        .alert-critical { border-left: 4px solid #e94560; }
        .alert-error { border-left: 4px solid #c0392b; }
        .alert-icon { font-size: 20px; }
        .alert-message { flex: 1; color: #333; }

        /* System Health */
        .health-grid { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 30px; }
        .health-item { display: flex; align-items: center; gap: 8px; padding: 10px 15px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); color: #333; }
        .health-dot { width: 10px; height: 10px; border-radius: 50%; }
        .health-dot.healthy { background: #27ae60; box-shadow: 0 0 8px #27ae60; }
        .health-dot.unhealthy { background: #e94560; box-shadow: 0 0 8px #e94560; }
        .health-dot.unknown { background: #888; }

        /* Cards */
        .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .card h2 { color: #333; margin-bottom: 20px; font-size: 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .card h2 .badge { font-size: 12px; padding: 4px 10px; background: #667eea; color: white; border-radius: 12px; }

        /* Grid layout */
        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }

        /* Tables */
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { color: #666; font-weight: 600; font-size: 13px; text-transform: uppercase; background: #f8f9fa; }
        td { color: #333; }
        tr:hover { background: #f8f9fa; }

        /* Severity badges */
        .severity { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .severity-low { background: #d4edda; color: #155724; }
        .severity-medium { background: #fff3cd; color: #856404; }
        .severity-high { background: #ffe0b2; color: #e65100; }
        .severity-critical { background: #f8d7da; color: #721c24; }

        /* Status badges */
        .status { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
        .status-graded { background: #d4edda; color: #155724; }
        .status-submitted { background: #cce5ff; color: #004085; }
        .status-pending { background: #fff3cd; color: #856404; }

        /* Top performers */
        .performer { display: flex; align-items: center; gap: 15px; padding: 12px 0; border-bottom: 1px solid #e0e0e0; }
        .performer:last-child { border-bottom: none; }
        .performer-rank { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; color: white; }
        .rank-1 { background: linear-gradient(135deg, #f5af19, #f12711); }
        .rank-2 { background: linear-gradient(135deg, #c0c0c0, #808080); }
        .rank-3 { background: linear-gradient(135deg, #cd7f32, #8b4513); }
        .rank-other { background: #e0e0e0; color: #333; }
        .performer-info { flex: 1; }
        .performer-name { font-weight: 500; color: #333; }
        .performer-stats { font-size: 12px; color: #666; }
        .performer-score { font-size: 20px; font-weight: bold; color: #27ae60; }

        /* Export buttons */
        .export-btn { padding: 6px 12px; background: #667eea; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; margin-left: 10px; }
        .export-btn:hover { background: #764ba2; }

        /* Login prompt */
        .login-prompt { text-align: center; padding: 60px 20px; background: white; }
        .login-prompt h2 { color: #333; border: none; }
        .login-prompt a { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; font-size: 18px; }
        .hidden { display: none; }
        .role-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; background: #fce4ec; color: #c2185b; }

        /* Loading */
        .loading-spinner { display: flex; justify-content: center; align-items: center; padding: 40px; }
        .loading-spinner::after { content: ""; width: 40px; height: 40px; border: 4px solid #e0e0e0; border-top-color: #667eea; border-radius: 50%; animation: spin 1s linear infinite; }

        /* Empty state */
        .empty-state { text-align: center; padding: 40px; color: #888; }

        /* Timestamp */
        .timestamp { font-size: 12px; color: #888; margin-top: 15px; text-align: right; }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar" id="navbar" style="display: none;">
        <a href="http://localhost:8001" class="navbar-brand" onclick="goToHub(); return false;">
            <span class="logo">🎓</span>
            ProctorWise
        </a>
        <div class="navbar-nav" id="navLinks"></div>
        <div class="navbar-user">
            <span id="navUserName" class="user-name"></span>
            <span id="navUserRole" class="role-badge"></span>
            <a href="#" id="notifBellLink" class="notif-bell" title="Notifications">
                🔔
                <span class="notif-badge hidden" id="notifBadge">0</span>
            </a>
            <button class="btn-logout" onclick="logout()">Deconnexion</button>
        </div>
    </nav>

    <div class="container">
        <div id="loginRequired" class="card login-prompt">
            <h2>Acces Admin Requis</h2>
            <p style="margin: 20px 0; color: rgba(255,255,255,0.7);">Veuillez vous connecter avec un compte administrateur.</p>
            <a href="http://localhost:8001">Se connecter</a>
        </div>

        <div id="mainApp" class="hidden">
            <div class="header">
                <h1>📊 Dashboard Admin</h1>
                <button class="btn-refresh" onclick="loadDashboard()" id="refreshBtn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                    </svg>
                    Actualiser
                </button>
            </div>

            <!-- Alerts -->
            <div id="alertsContainer" class="alerts-container"></div>

            <!-- System Health -->
            <div id="healthGrid" class="health-grid"></div>

            <!-- KPI Cards -->
            <div class="kpi-grid">
                <div class="kpi-card users">
                    <div class="kpi-icon">👥</div>
                    <div class="kpi-value" id="totalUsers">-</div>
                    <div class="kpi-label">Utilisateurs</div>
                </div>
                <div class="kpi-card exams">
                    <div class="kpi-icon">📝</div>
                    <div class="kpi-value" id="totalExams">-</div>
                    <div class="kpi-label">Examens</div>
                </div>
                <div class="kpi-card submissions">
                    <div class="kpi-icon">📊</div>
                    <div class="kpi-value" id="totalSubmissions">-</div>
                    <div class="kpi-label">Soumissions</div>
                </div>
                <div class="kpi-card sessions">
                    <div class="kpi-icon">🎥</div>
                    <div class="kpi-value" id="totalSessions">-</div>
                    <div class="kpi-label">Sessions Monitoring</div>
                </div>
                <div class="kpi-card anomalies">
                    <div class="kpi-icon">⚠️</div>
                    <div class="kpi-value" id="anomaliesToday">-</div>
                    <div class="kpi-label">Anomalies Aujourd'hui</div>
                </div>
                <div class="kpi-card active">
                    <div class="kpi-icon">🟢</div>
                    <div class="kpi-value" id="activeSessions">-</div>
                    <div class="kpi-label">Sessions Actives</div>
                </div>
            </div>

            <!-- Main Grid -->
            <div class="grid-2">
                <!-- Recent Submissions -->
                <div class="card">
                    <h2>
                        Soumissions Recentes
                        <span class="badge" id="submissionsBadge">0</span>
                    </h2>
                    <div id="recentExams">
                        <div class="loading-spinner"></div>
                    </div>
                </div>

                <!-- Recent Anomalies -->
                <div class="card">
                    <h2>
                        Anomalies Recentes
                        <span class="badge" id="anomaliesBadge">0</span>
                    </h2>
                    <div id="recentAnomalies">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <!-- Top Performers -->
                <div class="card">
                    <h2>Top Performers</h2>
                    <div id="topPerformers">
                        <div class="loading-spinner"></div>
                    </div>
                </div>

                <!-- Quick Stats -->
                <div class="card">
                    <h2>Activite du Jour</h2>
                    <div id="todayStats">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
            </div>

            <!-- Export Section -->
            <div class="card">
                <h2>Exporter des Rapports</h2>
                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px;">
                        <label style="display: block; margin-bottom: 8px; color: rgba(255,255,255,0.7);">Rapport par Examen</label>
                        <select id="examSelect" style="width: 100%; padding: 10px; border-radius: 8px; border: none; background: rgba(255,255,255,0.1); color: #fff;">
                            <option value="">-- Selectionnez un examen --</option>
                        </select>
                        <div style="margin-top: 10px;">
                            <button class="export-btn" onclick="exportExamPDF()">📄 PDF</button>
                            <button class="export-btn" onclick="exportExamCSV()">📊 CSV</button>
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <label style="display: block; margin-bottom: 8px; color: rgba(255,255,255,0.7);">Rapport par Utilisateur</label>
                        <select id="userSelect" style="width: 100%; padding: 10px; border-radius: 8px; border: none; background: rgba(255,255,255,0.1); color: #fff;">
                            <option value="">-- Selectionnez un utilisateur --</option>
                        </select>
                        <div style="margin-top: 10px;">
                            <button class="export-btn" onclick="exportUserPDF()">📄 PDF</button>
                            <button class="export-btn" onclick="exportUserCSV()">📊 CSV</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="timestamp" id="lastUpdate"></div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let isLoading = false;
        let refreshInterval = null;

        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            if (token) {
                localStorage.setItem('token', token);
                window.history.replaceState({}, document.title, window.location.pathname);
            }
            const storedToken = localStorage.getItem('token');
            if (storedToken) parseToken(storedToken);
        };

        function parseToken(token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                currentUser = {
                    user_id: payload.sub || payload.user_id,
                    name: payload.name || 'Utilisateur',
                    email: payload.email,
                    role: payload.role || 'student'
                };
                if (currentUser.role !== 'admin') {
                    alert('Acces reserve aux administrateurs');
                    window.location.href = 'http://localhost:8001';
                    return;
                }
                showMainApp();
            } catch (e) {
                console.error('Token parse error:', e);
                localStorage.removeItem('token');
            }
        }

        function showMainApp() {
            document.getElementById('loginRequired').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            document.getElementById('navbar').style.display = 'flex';

            // Update navbar user info
            document.getElementById('navUserName').textContent = currentUser.name;
            const roleEl = document.getElementById('navUserRole');
            roleEl.textContent = 'Admin';
            roleEl.className = 'role-badge';

            renderNavLinks();
            loadDashboard();
            // Start auto-refresh only once
            if (!refreshInterval) {
                refreshInterval = setInterval(loadDashboard, 60000); // Every 60 seconds
            }
        }

        function renderNavLinks() {
            const nav = document.getElementById('navLinks');
            const token = localStorage.getItem('token');
            const links = [
                { name: 'Examens', icon: '📝', url: 'http://localhost:8000', active: false, roles: ['student', 'teacher', 'admin'] },
                { name: 'Monitoring', icon: '👁️', url: 'http://localhost:8003', active: false, roles: ['proctor', 'admin'] },
                { name: 'Analytics', icon: '📊', url: 'http://localhost:8006', active: true, roles: ['admin'] }
            ];
            nav.innerHTML = links
                .filter(l => l.roles.includes(currentUser.role))
                .map(l => '<a href="' + l.url + '?token=' + token + '" class="nav-link ' + (l.active ? 'active' : '') + '"><span class="nav-icon">' + l.icon + '</span> ' + l.name + '</a>')
                .join('');
            loadNotificationCount();
        }

        async function loadNotificationCount() {
            const token = localStorage.getItem('token');
            try {
                const res = await fetch('http://localhost:8005/notifications/user/' + currentUser.user_id);
                if (res.ok) {
                    const notifications = await res.json();
                    const now = new Date();
                    const recentCount = notifications.filter(n => {
                        const created = new Date(n.created_at);
                        return (now - created) / (1000 * 60 * 60) < 24;
                    }).length;
                    const badge = document.getElementById('notifBadge');
                    if (recentCount > 0) {
                        badge.textContent = recentCount > 99 ? '99+' : recentCount;
                        badge.classList.remove('hidden');
                    } else {
                        badge.classList.add('hidden');
                    }
                }
            } catch (e) { console.log('Could not load notifications'); }
            document.getElementById('notifBellLink').href = 'http://localhost:8005?token=' + token;
        }

        function goToHub() {
            window.location.href = 'http://localhost:8001';
        }

        function logout() {
            localStorage.removeItem('token');
            window.location.href = 'http://localhost:8001?logout=true';
        }

        function formatDateTime(iso) {
            if (!iso) return '-';
            return new Date(iso).toLocaleString('fr-FR', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        }

        function formatTime(iso) {
            if (!iso) return '-';
            return new Date(iso).toLocaleTimeString('fr-FR', {
                hour: '2-digit', minute: '2-digit'
            });
        }

        async function loadDashboard() {
            if (isLoading) return; // Prevent multiple concurrent calls
            isLoading = true;

            const btn = document.getElementById('refreshBtn');
            if (btn) btn.classList.add('loading');

            try {
                const res = await fetch('/analytics/dashboards/admin?use_cache=false');
                if (!res.ok) throw new Error('Failed to load dashboard');
                const data = await res.json();
                renderDashboard(data);
            } catch (e) {
                console.error('Dashboard load error:', e);
            } finally {
                isLoading = false;
                if (btn) btn.classList.remove('loading');
            }
        }

        function renderDashboard(data) {
            const metrics = data.platform_metrics || {};

            // KPIs
            document.getElementById('totalUsers').textContent = metrics.total_users || 0;
            document.getElementById('totalExams').textContent = metrics.total_exams || 0;
            document.getElementById('totalSubmissions').textContent = metrics.total_submissions || 0;
            document.getElementById('totalSessions').textContent = metrics.total_monitoring_sessions || 0;
            document.getElementById('anomaliesToday').textContent = metrics.anomalies_today || 0;
            document.getElementById('activeSessions').textContent = metrics.active_sessions_now || 0;

            // System Health
            renderHealth(metrics.system_health || {});

            // Alerts
            renderAlerts(data.alerts || []);

            // Recent Exams
            renderRecentExams(data.recent_exams || []);

            // Recent Anomalies
            renderRecentAnomalies(data.recent_anomalies || []);

            // Top Performers
            renderTopPerformers(data.top_performers || []);

            // Today Stats
            renderTodayStats(metrics);

            // Update timestamp
            document.getElementById('lastUpdate').textContent =
                'Derniere mise a jour: ' + formatDateTime(data.generated_at || new Date().toISOString());

            // Load exam/user selects for export
            loadExportSelects(data);
        }

        function renderHealth(health) {
            const container = document.getElementById('healthGrid');
            const services = ['database', 'kafka', 'hdfs', 'redis'];
            let html = '';
            services.forEach(service => {
                const status = health[service] || 'unknown';
                const statusClass = status === 'healthy' ? 'healthy' : (status === 'unhealthy' ? 'unhealthy' : 'unknown');
                html += '<div class="health-item">';
                html += '<span class="health-dot ' + statusClass + '"></span>';
                html += '<span>' + service.charAt(0).toUpperCase() + service.slice(1) + '</span>';
                html += '</div>';
            });
            container.innerHTML = html;
        }

        function renderAlerts(alerts) {
            const container = document.getElementById('alertsContainer');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '';
                return;
            }
            let html = '';
            alerts.forEach(alert => {
                const icon = alert.level === 'critical' ? '🚨' : (alert.level === 'warning' ? '⚠️' : '❌');
                html += '<div class="alert alert-' + alert.level + '">';
                html += '<span class="alert-icon">' + icon + '</span>';
                html += '<span class="alert-message">' + alert.message + '</span>';
                html += '</div>';
            });
            container.innerHTML = html;
        }

        function renderRecentExams(exams) {
            const container = document.getElementById('recentExams');
            document.getElementById('submissionsBadge').textContent = exams.length;

            if (!exams || exams.length === 0) {
                container.innerHTML = '<div class="empty-state">Aucune soumission recente</div>';
                return;
            }

            let html = '<table><thead><tr><th>Utilisateur</th><th>Score</th><th>Date</th><th>Statut</th></tr></thead><tbody>';
            exams.slice(0, 10).forEach(exam => {
                const percentage = exam.percentage !== null ? parseFloat(exam.percentage).toFixed(1) + '%' : '-';
                const statusClass = exam.status === 'graded' ? 'graded' : (exam.status === 'submitted' ? 'submitted' : 'pending');
                html += '<tr>';
                html += '<td>' + (exam.user_id || '-').substring(0, 8) + '...</td>';
                html += '<td><strong>' + percentage + '</strong></td>';
                html += '<td>' + formatTime(exam.submitted_at) + '</td>';
                html += '<td><span class="status status-' + statusClass + '">' + exam.status + '</span></td>';
                html += '</tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function renderRecentAnomalies(anomalies) {
            const container = document.getElementById('recentAnomalies');
            document.getElementById('anomaliesBadge').textContent = anomalies.length;

            if (!anomalies || anomalies.length === 0) {
                container.innerHTML = '<div class="empty-state">Aucune anomalie recente</div>';
                return;
            }

            let html = '<table><thead><tr><th>Type</th><th>Severite</th><th>Heure</th></tr></thead><tbody>';
            anomalies.slice(0, 10).forEach(anomaly => {
                const severity = anomaly.severity || 'medium';
                const type = (anomaly.anomaly_type || 'unknown').replace(/_/g, ' ');
                html += '<tr>';
                html += '<td>' + type + '</td>';
                html += '<td><span class="severity severity-' + severity + '">' + severity + '</span></td>';
                html += '<td>' + formatTime(anomaly.detected_at) + '</td>';
                html += '</tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function renderTopPerformers(performers) {
            const container = document.getElementById('topPerformers');

            if (!performers || performers.length === 0) {
                container.innerHTML = '<div class="empty-state">Pas assez de donnees</div>';
                return;
            }

            let html = '';
            performers.slice(0, 5).forEach((performer, index) => {
                const rank = index + 1;
                const rankClass = rank === 1 ? 'rank-1' : (rank === 2 ? 'rank-2' : (rank === 3 ? 'rank-3' : 'rank-other'));
                const avgScore = performer.avg_score !== null ? parseFloat(performer.avg_score).toFixed(1) : '-';
                html += '<div class="performer">';
                html += '<div class="performer-rank ' + rankClass + '">' + rank + '</div>';
                html += '<div class="performer-info">';
                html += '<div class="performer-name">' + (performer.user_id || '-').substring(0, 12) + '...</div>';
                html += '<div class="performer-stats">' + (performer.exam_count || 0) + ' examens</div>';
                html += '</div>';
                html += '<div class="performer-score">' + avgScore + '%</div>';
                html += '</div>';
            });
            container.innerHTML = html;
        }

        function renderTodayStats(metrics) {
            const container = document.getElementById('todayStats');
            const html = `
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #667eea;">${metrics.exams_today || 0}</div>
                        <div style="color: #666; margin-top: 5px;">Examens aujourd'hui</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #27ae60;">${metrics.submissions_today || 0}</div>
                        <div style="color: #666; margin-top: 5px;">Soumissions aujourd'hui</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #e74c3c;">${metrics.anomalies_today || 0}</div>
                        <div style="color: #666; margin-top: 5px;">Anomalies aujourd'hui</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #f39c12;">${parseFloat(metrics.average_anomalies_per_exam || 0).toFixed(1)}</div>
                        <div style="color: #666; margin-top: 5px;">Anomalies/Examen (moy)</div>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        }

        function loadExportSelects(data) {
            // For now, just populate with recent data IDs
            const examSelect = document.getElementById('examSelect');
            const userSelect = document.getElementById('userSelect');

            // Get unique exam IDs from recent submissions
            const examIds = [...new Set((data.recent_exams || []).map(e => e.exam_id).filter(Boolean))];
            examSelect.innerHTML = '<option value="">-- Selectionnez un examen --</option>';
            examIds.forEach(id => {
                examSelect.innerHTML += '<option value="' + id + '">' + id.substring(0, 12) + '...</option>';
            });

            // Get unique user IDs
            const userIds = [...new Set((data.recent_exams || []).map(e => e.user_id).filter(Boolean))];
            userSelect.innerHTML = '<option value="">-- Selectionnez un utilisateur --</option>';
            userIds.forEach(id => {
                userSelect.innerHTML += '<option value="' + id + '">' + id.substring(0, 12) + '...</option>';
            });
        }

        function exportExamPDF() {
            const examId = document.getElementById('examSelect').value;
            if (!examId) { alert('Selectionnez un examen'); return; }
            window.open('/analytics/exams/' + examId + '/report/pdf', '_blank');
        }

        function exportExamCSV() {
            const examId = document.getElementById('examSelect').value;
            if (!examId) { alert('Selectionnez un examen'); return; }
            window.open('/analytics/exams/' + examId + '/report/csv', '_blank');
        }

        function exportUserPDF() {
            const userId = document.getElementById('userSelect').value;
            if (!userId) { alert('Selectionnez un utilisateur'); return; }
            window.open('/analytics/users/' + userId + '/report/pdf', '_blank');
        }

        function exportUserCSV() {
            const userId = document.getElementById('userSelect').value;
            if (!userId) { alert('Selectionnez un utilisateur'); return; }
            window.open('/analytics/users/' + userId + '/report/csv', '_blank');
        }

    </script>
</body>
</html>
"""
    return _rewrite_urls(html)
