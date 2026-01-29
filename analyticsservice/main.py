from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from interface.api.controllers import analytics_controller

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
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProctorWise - Admin Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; padding: 20px; color: #fff; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 15px; backdrop-filter: blur(10px); }
        .header h1 { color: #fff; font-size: 24px; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .btn-logout { padding: 8px 16px; background: #e94560; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .btn-refresh { padding: 8px 16px; background: rgba(255,255,255,0.2); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; display: flex; align-items: center; gap: 6px; }
        .btn-refresh:hover { background: rgba(255,255,255,0.3); }
        .btn-refresh.loading svg { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        /* KPI Cards */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .kpi-card { background: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px; backdrop-filter: blur(10px); transition: transform 0.2s; }
        .kpi-card:hover { transform: translateY(-5px); }
        .kpi-icon { font-size: 32px; margin-bottom: 10px; }
        .kpi-value { font-size: 36px; font-weight: bold; color: #fff; }
        .kpi-label { font-size: 14px; color: rgba(255,255,255,0.7); margin-top: 5px; }
        .kpi-card.users { border-left: 4px solid #4facfe; }
        .kpi-card.exams { border-left: 4px solid #00f2fe; }
        .kpi-card.submissions { border-left: 4px solid #43e97b; }
        .kpi-card.sessions { border-left: 4px solid #fa709a; }
        .kpi-card.anomalies { border-left: 4px solid #fee140; }
        .kpi-card.active { border-left: 4px solid #f093fb; }

        /* Alerts */
        .alerts-container { margin-bottom: 20px; }
        .alert { padding: 15px 20px; border-radius: 10px; margin-bottom: 10px; display: flex; align-items: center; gap: 12px; }
        .alert-warning { background: rgba(254, 225, 64, 0.2); border: 1px solid #fee140; }
        .alert-critical { background: rgba(233, 69, 96, 0.2); border: 1px solid #e94560; }
        .alert-error { background: rgba(255, 0, 0, 0.2); border: 1px solid #ff0000; }
        .alert-icon { font-size: 20px; }
        .alert-message { flex: 1; }

        /* System Health */
        .health-grid { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 30px; }
        .health-item { display: flex; align-items: center; gap: 8px; padding: 10px 15px; background: rgba(255,255,255,0.1); border-radius: 8px; }
        .health-dot { width: 10px; height: 10px; border-radius: 50%; }
        .health-dot.healthy { background: #43e97b; box-shadow: 0 0 10px #43e97b; }
        .health-dot.unhealthy { background: #e94560; box-shadow: 0 0 10px #e94560; }
        .health-dot.unknown { background: #888; }

        /* Cards */
        .card { background: rgba(255,255,255,0.1); padding: 25px; border-radius: 15px; backdrop-filter: blur(10px); margin-bottom: 20px; }
        .card h2 { color: #fff; margin-bottom: 20px; font-size: 18px; display: flex; justify-content: space-between; align-items: center; }
        .card h2 .badge { font-size: 12px; padding: 4px 10px; background: rgba(255,255,255,0.2); border-radius: 12px; }

        /* Grid layout */
        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }

        /* Tables */
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { color: rgba(255,255,255,0.7); font-weight: 500; font-size: 13px; text-transform: uppercase; }
        td { color: #fff; }
        tr:hover { background: rgba(255,255,255,0.05); }

        /* Severity badges */
        .severity { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .severity-low { background: rgba(67, 233, 123, 0.3); color: #43e97b; }
        .severity-medium { background: rgba(254, 225, 64, 0.3); color: #fee140; }
        .severity-high { background: rgba(250, 112, 154, 0.3); color: #fa709a; }
        .severity-critical { background: rgba(233, 69, 96, 0.3); color: #e94560; }

        /* Status badges */
        .status { padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
        .status-graded { background: rgba(67, 233, 123, 0.3); color: #43e97b; }
        .status-submitted { background: rgba(79, 172, 254, 0.3); color: #4facfe; }
        .status-pending { background: rgba(254, 225, 64, 0.3); color: #fee140; }

        /* Top performers */
        .performer { display: flex; align-items: center; gap: 15px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .performer:last-child { border-bottom: none; }
        .performer-rank { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }
        .rank-1 { background: linear-gradient(135deg, #f5af19, #f12711); }
        .rank-2 { background: linear-gradient(135deg, #c0c0c0, #808080); }
        .rank-3 { background: linear-gradient(135deg, #cd7f32, #8b4513); }
        .rank-other { background: rgba(255,255,255,0.2); }
        .performer-info { flex: 1; }
        .performer-name { font-weight: 500; }
        .performer-stats { font-size: 12px; color: rgba(255,255,255,0.6); }
        .performer-score { font-size: 20px; font-weight: bold; color: #43e97b; }

        /* Export buttons */
        .export-btn { padding: 6px 12px; background: rgba(255,255,255,0.2); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; margin-left: 10px; }
        .export-btn:hover { background: rgba(255,255,255,0.3); }

        /* Login prompt */
        .login-prompt { text-align: center; padding: 60px 20px; }
        .login-prompt a { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; text-decoration: none; border-radius: 10px; font-size: 18px; }
        .hidden { display: none; }
        .role-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; background: #e94560; }

        /* Loading */
        .loading-spinner { display: flex; justify-content: center; align-items: center; padding: 40px; }
        .loading-spinner::after { content: ""; width: 40px; height: 40px; border: 4px solid rgba(255,255,255,0.2); border-top-color: #4facfe; border-radius: 50%; animation: spin 1s linear infinite; }

        /* Empty state */
        .empty-state { text-align: center; padding: 40px; color: rgba(255,255,255,0.5); }

        /* Timestamp */
        .timestamp { font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 15px; text-align: right; }
    </style>
</head>
<body>
    <div class="container">
        <div id="loginRequired" class="card login-prompt">
            <h2>Acces Admin Requis</h2>
            <p style="margin: 20px 0; color: rgba(255,255,255,0.7);">Veuillez vous connecter avec un compte administrateur.</p>
            <a href="http://localhost:8001">Se connecter</a>
        </div>

        <div id="mainApp" class="hidden">
            <div class="header">
                <h1>Dashboard Admin</h1>
                <div class="user-info">
                    <button class="btn-refresh" onclick="loadDashboard()" id="refreshBtn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                        </svg>
                        Actualiser
                    </button>
                    <span id="userName"></span>
                    <span id="userRole" class="role-badge"></span>
                    <button class="btn-logout" onclick="logout()">Deconnexion</button>
                </div>
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
            document.getElementById('userName').textContent = currentUser.name;
            document.getElementById('userRole').textContent = 'Admin';
            loadDashboard();
            // Start auto-refresh only once
            if (!refreshInterval) {
                refreshInterval = setInterval(loadDashboard, 60000); // Every 60 seconds
            }
        }

        function logout() {
            localStorage.removeItem('token');
            window.location.href = 'http://localhost:8001';
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
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #4facfe;">${metrics.exams_today || 0}</div>
                        <div style="color: rgba(255,255,255,0.6); margin-top: 5px;">Examens aujourd'hui</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #43e97b;">${metrics.submissions_today || 0}</div>
                        <div style="color: rgba(255,255,255,0.6); margin-top: 5px;">Soumissions aujourd'hui</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #fa709a;">${metrics.anomalies_today || 0}</div>
                        <div style="color: rgba(255,255,255,0.6); margin-top: 5px;">Anomalies aujourd'hui</div>
                    </div>
                    <div style="text-align: center; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <div style="font-size: 32px; font-weight: bold; color: #fee140;">${parseFloat(metrics.average_anomalies_per_exam || 0).toFixed(1)}</div>
                        <div style="color: rgba(255,255,255,0.6); margin-top: 5px;">Anomalies/Examen (moy)</div>
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
