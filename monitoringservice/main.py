from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from interface.api.controllers import monitoring_controller
from infrastructure.database.models import Base
from infrastructure.database.mariadb_cluster import engine


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    try:
        await monitoring_controller.kafka_publisher.start()
    except Exception as e:
        print(f"Warning: Could not start Kafka producer: {e}")
    yield
    try:
        await monitoring_controller.kafka_publisher.stop()
    except Exception as e:
        print(f"Warning: Could not stop Kafka producer: {e}")


app = FastAPI(
    title="ProctorWise Monitoring Service",
    description="Real-time exam proctoring with hybrid ML/rule-based anomaly detection",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitoring_controller.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "monitoring"}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProctorWise - Monitoring</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #e74c3c 0%, #e67e22 100%); min-height: 100vh; padding-top: 80px; padding-left: 20px; padding-right: 20px; padding-bottom: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }

        /* Navbar */
        .navbar { position: fixed; top: 0; left: 0; right: 0; height: 60px; background: rgba(255,255,255,0.98); box-shadow: 0 2px 20px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between; padding: 0 30px; z-index: 1000; }
        .navbar-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: #333; font-weight: bold; font-size: 18px; }
        .navbar-brand:hover { color: #e74c3c; }
        .navbar-brand .logo { font-size: 24px; }
        .navbar-nav { display: flex; align-items: center; gap: 8px; }
        .nav-link { padding: 8px 16px; border-radius: 8px; text-decoration: none; color: #555; font-size: 14px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
        .nav-link:hover { background: #f0f0f0; color: #333; }
        .nav-link.active { background: linear-gradient(135deg, #e74c3c 0%, #e67e22 100%); color: white; }
        .nav-link .nav-icon { font-size: 16px; }
        .navbar-user { display: flex; align-items: center; gap: 12px; }
        .nav-user-name { font-weight: 500; color: #333; font-size: 14px; }

        /* Notification Bell */
        .notif-bell { position: relative; cursor: pointer; font-size: 20px; padding: 8px; border-radius: 50%; transition: background 0.2s; text-decoration: none; }
        .notif-bell:hover { background: #f0f0f0; }
        .notif-badge { position: absolute; top: 2px; right: 2px; background: #e94560; color: white; font-size: 10px; font-weight: bold; min-width: 16px; height: 16px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
        .notif-badge.hidden { display: none; }

        /* Header */
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 20px; background: rgba(255,255,255,0.95); border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .header h1 { color: #333; font-size: 24px; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .btn-logout { padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .btn-logout:hover { background: #c82333; }

        /* Cards */
        .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { color: #333; margin-bottom: 15px; font-size: 20px; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
        .hidden { display: none !important; }

        /* Stats bar */
        .stats-bar { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .stat-card { background: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden; }
        .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
        .stat-active::before { background: linear-gradient(90deg, #28a745, #20c997); }
        .stat-total::before { background: linear-gradient(90deg, #6c757d, #adb5bd); }
        .stat-anomalies::before { background: linear-gradient(90deg, #e74c3c, #e67e22); }
        .stat-critical::before { background: linear-gradient(90deg, #dc3545, #c82333); }
        .stat-card .stat-value { font-size: 32px; font-weight: 700; color: #333; }
        .stat-card .stat-label { font-size: 13px; color: #888; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.5px; }

        /* Tabs */
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .tab.active { background: linear-gradient(135deg, #e74c3c 0%, #e67e22 100%); color: white; }
        .tab:hover:not(.active) { background: #ccc; }

        /* Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background: #f8f9fa; color: #333; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.3px; }
        tr:hover { background: #f8f9fa; }

        /* Status badges */
        .status { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
        .status-active { background: #d4edda; color: #155724; }
        .status-stopped { background: #f8d7da; color: #721c24; }
        .status-paused { background: #fff3cd; color: #856404; }

        /* Severity badges */
        .severity { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block; }
        .severity-critical { background: #e74c3c; color: white; }
        .severity-high { background: #e67e22; color: white; }
        .severity-medium { background: #f1c40f; color: #333; }
        .severity-low { background: #3498db; color: white; }

        /* Buttons */
        .btn-small { padding: 6px 12px; font-size: 12px; background: linear-gradient(135deg, #e74c3c 0%, #e67e22 100%); color: white; border: none; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
        .btn-small:hover { transform: translateY(-1px); box-shadow: 0 3px 10px rgba(231, 76, 60, 0.4); }
        .btn-stop { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); }
        .btn-stop:hover { box-shadow: 0 3px 10px rgba(220, 53, 69, 0.4); }
        .btn-secondary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 12px; transition: all 0.2s; }
        .btn-secondary:hover { transform: translateY(-1px); }
        .refresh-btn { padding: 6px 14px; font-size: 12px; background: #f8f9fa; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
        .refresh-btn:hover { background: #e9ecef; }

        /* Role badge */
        .role-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .role-proctor { background: #fff3cd; color: #856404; }
        .role-admin { background: #f8d7da; color: #721c24; }

        /* Login/Access screens */
        .login-prompt { text-align: center; padding: 60px 20px; }
        .login-prompt h2 { border: none; justify-content: center; }
        .login-prompt a { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; font-size: 18px; transition: all 0.2s; }
        .login-prompt a:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }

        /* Modal */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 1000; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.2s ease; }
        .modal { background: white; border-radius: 15px; padding: 30px; width: 90%; max-width: 950px; max-height: 85vh; overflow-y: auto; position: relative; animation: slideUp 0.3s ease; }
        .modal h2 { color: #333; margin-bottom: 20px; font-size: 20px; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }
        .modal-close { position: absolute; top: 15px; right: 20px; font-size: 28px; cursor: pointer; color: #999; background: none; border: none; line-height: 1; }
        .modal-close:hover { color: #333; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        /* Summary grid */
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .summary-card { padding: 15px; border-radius: 10px; text-align: center; }
        .summary-card .count { font-size: 28px; font-weight: bold; }
        .summary-card .label { font-size: 12px; color: #666; margin-top: 5px; }
        .summary-critical { background: #fde8e8; border: 2px solid #e74c3c; }
        .summary-critical .count { color: #e74c3c; }
        .summary-high { background: #fef3e2; border: 2px solid #e67e22; }
        .summary-high .count { color: #e67e22; }
        .summary-medium { background: #fef9e7; border: 2px solid #f1c40f; }
        .summary-medium .count { color: #b7950b; }
        .summary-low { background: #e8f4fd; border: 2px solid #3498db; }
        .summary-low .count { color: #3498db; }
        .summary-total { background: #f8f9fa; border: 2px solid #6c757d; }
        .summary-total .count { color: #333; }

        /* Info grid */
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px; }
        .info-item { font-size: 14px; }
        .info-item span { font-weight: 600; color: #333; }

        /* Live feed */
        .live-feed { margin-top: 20px; }
        .live-feed h3 { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
        .live-dot { width: 10px; height: 10px; background: #e74c3c; border-radius: 50%; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .feed-item { padding: 10px 15px; margin-bottom: 8px; border-radius: 8px; border-left: 4px solid #ccc; background: #f8f9fa; animation: fadeIn 0.3s ease; }
        .feed-item.critical { border-left-color: #e74c3c; background: #fde8e8; }
        .feed-item.high { border-left-color: #e67e22; background: #fef3e2; }
        .feed-item.medium { border-left-color: #f1c40f; background: #fef9e7; }
        .feed-item.low { border-left-color: #3498db; background: #e8f4fd; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .feed-time { font-size: 11px; color: #888; }
        .feed-type { font-weight: 600; }

        /* Notification toast */
        .toast-container { position: fixed; top: 20px; right: 20px; z-index: 2000; display: flex; flex-direction: column; gap: 10px; }
        .toast { padding: 15px 20px; border-radius: 10px; color: white; font-size: 14px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); animation: slideIn 0.3s ease; max-width: 400px; cursor: pointer; }
        .toast-critical { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .toast-high { background: linear-gradient(135deg, #e67e22, #d35400); }
        .toast-medium { background: linear-gradient(135deg, #f39c12, #e67e22); }
        .toast-info { background: linear-gradient(135deg, #3498db, #2980b9); }
        @keyframes slideIn { from { opacity: 0; transform: translateX(100px); } to { opacity: 1; transform: translateX(0); } }

        .no-data { text-align: center; padding: 40px; color: #999; font-size: 15px; }
        .anomaly-type-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
        .anomaly-type-tag { padding: 5px 12px; background: #f0f0f0; border-radius: 15px; font-size: 13px; }
        .anomaly-type-tag strong { margin-right: 4px; }

        /* Auto-refresh indicator */
        .auto-refresh { font-size: 11px; color: #999; display: flex; align-items: center; gap: 5px; }
        .auto-refresh .dot { width: 6px; height: 6px; background: #28a745; border-radius: 50%; animation: pulse 2s infinite; }

        /* Live video viewer */
        .live-video-container { background: #1a1a2e; border-radius: 12px; overflow: hidden; margin-bottom: 20px; }
        .live-video-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #16213e; }
        .live-video-header .live-title { color: #e0e0e0; font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
        .live-video-body { position: relative; min-height: 300px; display: flex; align-items: center; justify-content: center; background: #0f0f23; }
        .live-video-body img { width: 100%; display: block; }
        .live-video-placeholder { color: #666; font-size: 14px; text-align: center; padding: 40px; }
        .live-video-overlay { position: absolute; bottom: 0; left: 0; right: 0; padding: 8px 14px; background: rgba(0,0,0,0.6); color: #ccc; font-size: 12px; display: flex; justify-content: space-between; }
        .live-anomaly-banner { position: absolute; top: 10px; left: 10px; right: 10px; padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; color: white; animation: fadeIn 0.3s ease; z-index: 10; }
        .live-anomaly-banner.critical { background: rgba(231, 76, 60, 0.9); }
        .live-anomaly-banner.high { background: rgba(230, 126, 34, 0.9); }
        .live-anomaly-banner.medium { background: rgba(241, 196, 15, 0.85); color: #333; }
        .live-anomaly-banner.low { background: rgba(52, 152, 219, 0.9); }
        .btn-live-start { padding: 6px 14px; font-size: 12px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
        .btn-live-start:hover { background: #218838; }
        .btn-live-stop { padding: 6px 14px; font-size: 12px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
        .btn-live-stop:hover { background: #5a6268; }
        .live-status-indicator { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .live-status-indicator.connected { background: #28a745; animation: pulse 1.5s infinite; }
        .live-status-indicator.disconnected { background: #6c757d; }
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
            <span id="navUserName" class="nav-user-name"></span>
            <span id="navUserRole" class="role-badge role-proctor"></span>
            <a href="#" id="notifBellLink" class="notif-bell" title="Notifications">
                🔔
                <span class="notif-badge hidden" id="notifBadge">0</span>
            </a>
            <button class="btn-logout" onclick="logout()">Deconnexion</button>
        </div>
    </nav>

    <div class="container">
        <!-- Login required -->
        <div id="loginRequired" class="card login-prompt">
            <h2>Connexion requise</h2>
            <p style="margin: 20px 0;">Veuillez vous connecter en tant que surveillant pour acceder au monitoring.</p>
            <a href="http://localhost:8001">Se connecter</a>
        </div>

        <!-- Wrong role -->
        <div id="wrongRole" class="card login-prompt hidden">
            <h2>Acces refuse</h2>
            <p style="margin: 20px 0;">Cette interface est reservee aux surveillants (proctors).</p>
            <a href="http://localhost:8001">Retour</a>
        </div>

        <!-- Main app -->
        <div id="mainApp" class="hidden">

            <!-- Stats overview -->
            <div class="stats-bar">
                <div class="stat-card stat-active">
                    <div class="stat-value" id="statActive">0</div>
                    <div class="stat-label">Sessions actives</div>
                </div>
                <div class="stat-card stat-total">
                    <div class="stat-value" id="statTotal">0</div>
                    <div class="stat-label">Total sessions</div>
                </div>
                <div class="stat-card stat-anomalies">
                    <div class="stat-value" id="statAnomalies">0</div>
                    <div class="stat-label">Anomalies totales</div>
                </div>
                <div class="stat-card stat-critical">
                    <div class="stat-value" id="statCritical">0</div>
                    <div class="stat-label">Alertes critiques</div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="tabs">
                <button class="tab active" onclick="showTab('active', this)">Sessions actives</button>
                <button class="tab" onclick="showTab('all', this)">Toutes les sessions</button>
                <button class="tab" onclick="showTab('alerts', this)">Alertes recentes</button>
            </div>

            <!-- Active sessions tab -->
            <div id="activeTab" class="card">
                <h2>
                    Sessions actives
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span class="auto-refresh"><span class="dot"></span> Actualisation auto 10s</span>
                        <button class="refresh-btn" onclick="loadActiveSessions()">Rafraichir</button>
                    </div>
                </h2>
                <div id="activeSessionsList"></div>
            </div>

            <!-- All sessions tab -->
            <div id="allTab" class="card hidden">
                <h2>
                    Historique des sessions
                    <button class="refresh-btn" onclick="loadAllSessions()">Rafraichir</button>
                </h2>
                <div id="allSessionsList"></div>
            </div>

            <!-- Alerts tab -->
            <div id="alertsTab" class="card hidden">
                <h2>
                    Alertes recentes
                    <button class="refresh-btn" onclick="loadRecentAlerts()">Rafraichir</button>
                </h2>
                <div id="alertsList"></div>
            </div>
        </div>
    </div>

    <!-- Toast container for real-time notifications -->
    <div class="toast-container" id="toastContainer"></div>

    <!-- Detail Modal -->
    <div id="detailModal" class="modal-overlay hidden" onclick="if(event.target===this)closeDetail()">
        <div class="modal">
            <button class="modal-close" onclick="closeDetail()">&times;</button>
            <h2 id="modalTitle">Detail de la session</h2>
            <div id="modalContent"></div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let activeWebSocket = null;
        let pingIntervalId = null;
        let autoRefreshIntervalId = null;
        let allSessionsCache = [];
        let currentDetailSessionId = null;
        let liveWebSocket = null;
        let livePingIntervalId = null;
        let liveViewActive = false;

        // ========== INIT ==========
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
                let base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
                while (base64.length % 4) base64 += '=';
                const payload = JSON.parse(atob(base64));
                currentUser = {
                    user_id: payload.sub || payload.user_id,
                    name: payload.name || 'Utilisateur',
                    email: payload.email,
                    role: payload.role || 'student'
                };
                if (currentUser.role !== 'proctor' && currentUser.role !== 'admin') {
                    document.getElementById('loginRequired').classList.add('hidden');
                    document.getElementById('wrongRole').classList.remove('hidden');
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
            document.getElementById('wrongRole').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            document.getElementById('navbar').style.display = 'flex';

            // Update navbar user info
            document.getElementById('navUserName').textContent = currentUser.name;
            const roleEl = document.getElementById('navUserRole');
            const roleNames = { proctor: 'Surveillant', admin: 'Admin' };
            roleEl.textContent = roleNames[currentUser.role] || currentUser.role;
            roleEl.className = 'role-badge role-' + currentUser.role;

            renderNavLinks();
            loadActiveSessions();
            loadStats();
            startAutoRefresh();
        }

        function renderNavLinks() {
            const nav = document.getElementById('navLinks');
            const token = localStorage.getItem('token');
            const links = [
                { name: 'Examens', icon: '📝', url: 'http://localhost:8000', active: false, roles: ['student', 'teacher', 'admin'] },
                { name: 'Monitoring', icon: '👁️', url: 'http://localhost:8003', active: true, roles: ['proctor', 'admin'] },
                { name: 'Analytics', icon: '📊', url: 'http://localhost:8006', active: false, roles: ['admin'] }
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
            stopAutoRefresh();
            disconnectWebSocket();
            localStorage.removeItem('token');
            window.location.href = 'http://localhost:8001';
        }

        // ========== AUTO REFRESH ==========
        function startAutoRefresh() {
            stopAutoRefresh();
            autoRefreshIntervalId = setInterval(function() {
                const activeTab = document.getElementById('activeTab');
                if (!activeTab.classList.contains('hidden')) {
                    loadActiveSessions();
                }
                loadStats();
            }, 10000);
        }

        function stopAutoRefresh() {
            if (autoRefreshIntervalId) {
                clearInterval(autoRefreshIntervalId);
                autoRefreshIntervalId = null;
            }
        }

        // ========== UTILITIES ==========
        function formatDateTime(iso) {
            if (!iso) return '-';
            return new Date(iso).toLocaleString('fr-FR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }

        function formatDuration(startedAt, stoppedAt) {
            const start = new Date(startedAt);
            const end = stoppedAt ? new Date(stoppedAt) : new Date();
            const diff = Math.floor((end - start) / 1000);
            if (diff < 0) return '0min 00s';
            const hours = Math.floor(diff / 3600);
            const mins = Math.floor((diff % 3600) / 60);
            const secs = diff % 60;
            if (hours > 0) return hours + 'h ' + mins.toString().padStart(2, '0') + 'min';
            return mins + 'min ' + secs.toString().padStart(2, '0') + 's';
        }

        function showToast(message, level) {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast toast-' + (level || 'info');
            toast.textContent = message;
            toast.onclick = function() { toast.remove(); };
            container.appendChild(toast);
            setTimeout(function() { if (toast.parentNode) toast.remove(); }, 6000);
        }

        // ========== TABS ==========
        function showTab(tab, btn) {
            document.querySelectorAll('.tabs .tab').forEach(function(t) { t.classList.remove('active'); });
            if (btn) btn.classList.add('active');
            document.getElementById('activeTab').classList.toggle('hidden', tab !== 'active');
            document.getElementById('allTab').classList.toggle('hidden', tab !== 'all');
            document.getElementById('alertsTab').classList.toggle('hidden', tab !== 'alerts');
            if (tab === 'active') loadActiveSessions();
            else if (tab === 'all') loadAllSessions();
            else if (tab === 'alerts') loadRecentAlerts();
        }

        // ========== STATS ==========
        async function loadStats() {
            try {
                const res = await fetch('/monitoring/sessions');
                if (!res.ok) return;
                const sessions = await res.json();
                allSessionsCache = sessions;

                const active = sessions.filter(function(s) { return s.status === 'active'; }).length;
                const totalAnomalies = sessions.reduce(function(sum, s) { return sum + s.anomaly_count; }, 0);

                document.getElementById('statActive').textContent = active;
                document.getElementById('statTotal').textContent = sessions.length;
                document.getElementById('statAnomalies').textContent = totalAnomalies;

                // Load critical count from active sessions
                let criticalCount = 0;
                for (const s of sessions.filter(function(s) { return s.status === 'active'; })) {
                    try {
                        const summaryRes = await fetch('/monitoring/sessions/' + s.session_id + '/anomalies/summary');
                        if (summaryRes.ok) {
                            const summary = await summaryRes.json();
                            criticalCount += (summary.by_severity.critical || 0);
                        }
                    } catch (e) { /* ignore */ }
                }
                document.getElementById('statCritical').textContent = criticalCount;
            } catch (e) { /* ignore */ }
        }

        // ========== SESSIONS ==========
        async function loadActiveSessions() {
            const container = document.getElementById('activeSessionsList');
            try {
                const res = await fetch('/monitoring/sessions?status=active');
                if (!res.ok) throw new Error('Erreur serveur');
                const sessions = await res.json();
                renderSessionsTable(sessions, container, true);
            } catch (e) {
                container.innerHTML = '<p class="no-data" style="color:#dc3545;">Erreur de chargement: ' + e.message + '</p>';
            }
        }

        async function loadAllSessions() {
            const container = document.getElementById('allSessionsList');
            container.innerHTML = '<p class="no-data">Chargement...</p>';
            try {
                const res = await fetch('/monitoring/sessions');
                if (!res.ok) throw new Error('Erreur serveur');
                const sessions = await res.json();
                allSessionsCache = sessions;
                renderSessionsTable(sessions, container, false);
            } catch (e) {
                container.innerHTML = '<p class="no-data" style="color:#dc3545;">Erreur de chargement: ' + e.message + '</p>';
            }
        }

        function renderSessionsTable(sessions, container, activeOnly) {
            if (sessions.length === 0) {
                container.innerHTML = '<p class="no-data">' + (activeOnly ? 'Aucune session active en cours.' : 'Aucune session de monitoring enregistree.') + '</p>';
                return;
            }
            let html = '<table><thead><tr>';
            html += '<th>Session</th><th>Examen</th><th>Etudiant</th><th>Debut</th><th>Duree</th><th>Frames</th><th>Anomalies</th><th>Statut</th><th>Actions</th>';
            html += '</tr></thead><tbody>';
            for (const s of sessions) {
                const anomalyColor = s.anomaly_count > 5 ? '#e74c3c' : s.anomaly_count > 0 ? '#e67e22' : '#28a745';
                html += '<tr>';
                html += '<td title="' + s.session_id + '"><code>' + s.session_id.substring(0, 8) + '...</code></td>';
                html += '<td title="' + s.exam_id + '"><code>' + s.exam_id.substring(0, 8) + '...</code></td>';
                html += '<td title="' + s.user_id + '"><code>' + s.user_id.substring(0, 8) + '...</code></td>';
                html += '<td>' + formatDateTime(s.started_at) + '</td>';
                html += '<td>' + formatDuration(s.started_at, s.stopped_at) + '</td>';
                html += '<td>' + s.total_frames_processed + '</td>';
                html += '<td><strong style="color:' + anomalyColor + ';">' + s.anomaly_count + '</strong></td>';
                html += '<td><span class="status status-' + s.status + '">' + s.status + '</span></td>';
                html += '<td style="white-space:nowrap;">';
                html += '<button class="btn-small" onclick="openDetail(&apos;' + s.session_id + '&apos;)">Details</button>';
                if (s.status === 'active') {
                    html += ' <button class="btn-small btn-stop" onclick="stopSession(&apos;' + s.session_id + '&apos;)">Arreter</button>';
                }
                html += '</td>';
                html += '</tr>';
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        // ========== STOP SESSION ==========
        async function stopSession(sessionId) {
            if (!confirm('Etes-vous sur de vouloir arreter cette session de monitoring ?')) return;
            try {
                const res = await fetch('/monitoring/sessions/' + sessionId + '/stop', { method: 'PUT' });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Erreur');
                }
                showToast('Session arretee avec succes', 'info');
                loadActiveSessions();
                loadStats();
            } catch (e) {
                showToast('Erreur: ' + e.message, 'critical');
            }
        }

        // ========== RECENT ALERTS ==========
        async function loadRecentAlerts() {
            const container = document.getElementById('alertsList');
            container.innerHTML = '<p class="no-data">Chargement des alertes...</p>';

            try {
                const sessionsRes = await fetch('/monitoring/sessions');
                if (!sessionsRes.ok) throw new Error('Erreur serveur');
                const sessions = await sessionsRes.json();

                let allAnomalies = [];
                // Fetch anomalies from all sessions (limit to recent 20 sessions for performance)
                const recentSessions = sessions.slice(0, 20);
                const promises = recentSessions.map(function(s) {
                    return fetch('/monitoring/sessions/' + s.session_id + '/anomalies')
                        .then(function(r) { return r.ok ? r.json() : []; })
                        .then(function(anomalies) {
                            return anomalies.map(function(a) {
                                a._session = s;
                                return a;
                            });
                        })
                        .catch(function() { return []; });
                });

                const results = await Promise.all(promises);
                for (const r of results) allAnomalies = allAnomalies.concat(r);

                // Sort by date desc
                allAnomalies.sort(function(a, b) { return new Date(b.detected_at) - new Date(a.detected_at); });

                // Show last 50
                allAnomalies = allAnomalies.slice(0, 50);

                if (allAnomalies.length === 0) {
                    container.innerHTML = '<p class="no-data">Aucune alerte enregistree.</p>';
                    return;
                }

                let html = '<table><thead><tr>';
                html += '<th>Heure</th><th>Session</th><th>Type</th><th>Severite</th><th>Methode</th><th>Confiance</th><th>Description</th>';
                html += '</tr></thead><tbody>';
                for (const a of allAnomalies) {
                    html += '<tr>';
                    html += '<td style="white-space:nowrap;">' + formatDateTime(a.detected_at) + '</td>';
                    html += '<td><code title="' + a.session_id + '">' + a.session_id.substring(0, 8) + '...</code></td>';
                    html += '<td>' + (a.anomaly_type || '').replace(/_/g, ' ') + '</td>';
                    html += '<td><span class="severity severity-' + a.severity + '">' + a.severity + '</span></td>';
                    html += '<td>' + (a.detection_method || '-') + '</td>';
                    html += '<td>' + ((a.confidence || 0) * 100).toFixed(0) + '%</td>';
                    html += '<td>' + (a.description || '-') + '</td>';
                    html += '</tr>';
                }
                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (e) {
                container.innerHTML = '<p class="no-data" style="color:#dc3545;">Erreur: ' + e.message + '</p>';
            }
        }

        // ========== DETAIL MODAL ==========
        async function openDetail(sessionId) {
            currentDetailSessionId = sessionId;
            const modal = document.getElementById('detailModal');
            const content = document.getElementById('modalContent');
            document.getElementById('modalTitle').textContent = 'Session ' + sessionId.substring(0, 12) + '...';
            content.innerHTML = '<p class="no-data">Chargement...</p>';
            modal.classList.remove('hidden');

            try {
                const [sessionRes, summaryRes, anomaliesRes] = await Promise.all([
                    fetch('/monitoring/sessions/' + sessionId),
                    fetch('/monitoring/sessions/' + sessionId + '/anomalies/summary'),
                    fetch('/monitoring/sessions/' + sessionId + '/anomalies')
                ]);

                const session = await sessionRes.json();
                if (!sessionRes.ok) throw new Error(session.detail || 'Session non trouvee');

                const summary = summaryRes.ok ? await summaryRes.json() : null;
                const anomalies = anomaliesRes.ok ? await anomaliesRes.json() : [];

                let html = '';

                // Session info
                html += '<div class="info-grid">';
                html += '<div class="info-item">Session ID: <span>' + session.session_id + '</span></div>';
                html += '<div class="info-item">Examen: <span>' + session.exam_id + '</span></div>';
                html += '<div class="info-item">Reservation: <span>' + session.reservation_id + '</span></div>';
                html += '<div class="info-item">Etudiant: <span>' + session.user_id + '</span></div>';
                html += '<div class="info-item">Statut: <span class="status status-' + session.status + '">' + session.status + '</span></div>';
                html += '<div class="info-item">Demarre le: <span>' + formatDateTime(session.started_at) + '</span></div>';
                if (session.stopped_at) {
                    html += '<div class="info-item">Arrete le: <span>' + formatDateTime(session.stopped_at) + '</span></div>';
                }
                html += '<div class="info-item">Duree: <span>' + formatDuration(session.started_at, session.stopped_at) + '</span></div>';
                html += '<div class="info-item">Frames traites: <span>' + session.total_frames_processed + '</span></div>';
                html += '<div class="info-item">Total anomalies: <span style="color:' + (session.anomaly_count > 0 ? '#e74c3c' : '#28a745') + ';font-size:18px;">' + session.anomaly_count + '</span></div>';
                html += '</div>';

                // Stop button for active sessions
                if (session.status === 'active') {
                    html += '<div style="margin-bottom:20px;"><button class="btn-small btn-stop" onclick="stopSession(&apos;' + session.session_id + '&apos;);closeDetail();">Arreter cette session</button></div>';
                }

                // Live video viewer for active sessions
                if (session.status === 'active') {
                    html += '<div class="live-video-container">';
                    html += '<div class="live-video-header">';
                    html += '<div class="live-title"><span class="live-status-indicator disconnected" id="liveStatusDot"></span> Flux video en direct</div>';
                    html += '<button class="btn-live-start" id="liveToggleBtn" onclick="toggleLiveView(&apos;' + session.session_id + '&apos;)">Voir en direct</button>';
                    html += '</div>';
                    html += '<div class="live-video-body" id="liveVideoBody">';
                    html += '<div class="live-video-placeholder" id="liveVideoPlaceholder">Cliquez sur "Voir en direct" pour afficher le flux webcam de l&apos;etudiant</div>';
                    html += '<img id="liveVideoFrame" style="display:none;" alt="Live frame">';
                    html += '<div class="live-anomaly-banner" id="liveAnomalyBanner" style="display:none;"></div>';
                    html += '<div class="live-video-overlay" id="liveVideoOverlay" style="display:none;"><span id="liveFrameInfo"></span><span id="liveTimestamp"></span></div>';
                    html += '</div>';
                    html += '</div>';
                }

                // Anomaly summary
                if (summary) {
                    html += '<h3 style="margin-bottom:10px;font-size:16px;">Resume des anomalies</h3>';
                    html += '<div class="summary-grid">';
                    html += '<div class="summary-card summary-total"><div class="count">' + summary.total_anomalies + '</div><div class="label">Total</div></div>';
                    html += '<div class="summary-card summary-critical"><div class="count">' + (summary.by_severity.critical || 0) + '</div><div class="label">Critical</div></div>';
                    html += '<div class="summary-card summary-high"><div class="count">' + (summary.by_severity.high || 0) + '</div><div class="label">High</div></div>';
                    html += '<div class="summary-card summary-medium"><div class="count">' + (summary.by_severity.medium || 0) + '</div><div class="label">Medium</div></div>';
                    html += '<div class="summary-card summary-low"><div class="count">' + (summary.by_severity.low || 0) + '</div><div class="label">Low</div></div>';
                    html += '</div>';

                    // By type
                    if (Object.keys(summary.by_type).length > 0) {
                        html += '<h3 style="margin:15px 0 10px;font-size:16px;">Par type d&apos;anomalie</h3>';
                        html += '<div class="anomaly-type-tags">';
                        for (const [type, count] of Object.entries(summary.by_type)) {
                            html += '<span class="anomaly-type-tag"><strong>' + type.replace(/_/g, ' ') + '</strong>: ' + count + '</span>';
                        }
                        html += '</div>';
                    }

                    // By detection method
                    if (Object.keys(summary.by_detection_method).length > 0) {
                        const methods = summary.by_detection_method;
                        const hasData = Object.values(methods).some(function(v) { return v > 0; });
                        if (hasData) {
                            html += '<h3 style="margin:15px 0 10px;font-size:16px;">Par methode de detection</h3>';
                            html += '<div class="anomaly-type-tags">';
                            for (const [method, count] of Object.entries(methods)) {
                                if (count > 0) {
                                    html += '<span class="anomaly-type-tag"><strong>' + method + '</strong>: ' + count + '</span>';
                                }
                            }
                            html += '</div>';
                        }
                    }
                }

                // Live feed section for active sessions
                if (session.status === 'active') {
                    html += '<div class="live-feed">';
                    html += '<h3><span class="live-dot"></span> Feed temps reel</h3>';
                    html += '<div id="liveFeed"><p class="no-data">En attente de connexion...</p></div>';
                    html += '</div>';
                }

                // Anomaly list
                html += '<h3 style="margin:20px 0 10px;font-size:16px;">Liste des anomalies (' + anomalies.length + ')</h3>';
                if (anomalies.length === 0) {
                    html += '<p class="no-data">Aucune anomalie detectee pour cette session.</p>';
                } else {
                    html += '<div id="anomalyList">';
                    const sorted = anomalies.sort(function(a, b) { return new Date(b.detected_at) - new Date(a.detected_at); });
                    for (const a of sorted) {
                        html += renderAnomalyItem(a);
                    }
                    html += '</div>';
                }

                content.innerHTML = html;

                // Connect WebSocket for active sessions
                if (session.status === 'active') {
                    connectWebSocket(sessionId);
                }

            } catch (e) {
                content.innerHTML = '<p class="no-data" style="color:#dc3545;">Erreur: ' + e.message + '</p>';
            }
        }

        function renderAnomalyItem(a) {
            let html = '<div class="feed-item ' + a.severity + '">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<div>';
            html += '<span class="severity severity-' + a.severity + '">' + a.severity + '</span> ';
            html += '<span class="feed-type">' + (a.anomaly_type || '').replace(/_/g, ' ') + '</span>';
            html += '</div>';
            html += '<span class="feed-time">' + formatDateTime(a.detected_at) + '</span>';
            html += '</div>';
            if (a.description) {
                html += '<div style="margin-top:5px;font-size:13px;color:#555;">' + a.description + '</div>';
            }
            html += '<div style="margin-top:3px;font-size:11px;color:#999;">';
            html += 'Methode: ' + (a.detection_method || '-') + ' | Confiance: ' + ((a.confidence || 0) * 100).toFixed(0) + '%';
            html += '</div>';
            html += '</div>';
            return html;
        }

        function closeDetail() {
            document.getElementById('detailModal').classList.add('hidden');
            currentDetailSessionId = null;
            disconnectWebSocket();
            stopLiveView();
        }

        // ========== WEBSOCKET ==========
        function connectWebSocket(sessionId) {
            disconnectWebSocket();
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = wsProtocol + '//' + window.location.host + '/monitoring/sessions/' + sessionId + '/stream';

            try {
                activeWebSocket = new WebSocket(wsUrl);

                activeWebSocket.onopen = function() {
                    const feed = document.getElementById('liveFeed');
                    if (feed) {
                        feed.innerHTML = '<div class="feed-item" style="border-left-color:#28a745;background:#d4edda;"><span style="color:#155724;">Connecte au flux temps reel</span></div>';
                    }
                    // Start ping with interval tracking
                    pingIntervalId = setInterval(function() {
                        if (activeWebSocket && activeWebSocket.readyState === WebSocket.OPEN) {
                            activeWebSocket.send(JSON.stringify({ type: 'ping' }));
                        }
                    }, 30000);
                };

                activeWebSocket.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'pong') return;

                        let anomalyItems = [];
                        if (data.type === 'anomalies' && data.data && data.data.length > 0) {
                            anomalyItems = data.data;
                        } else if (data.type === 'frame_processed' && data.anomalies && data.anomalies.length > 0) {
                            anomalyItems = data.anomalies;
                        }

                        if (anomalyItems.length > 0) {
                            const feed = document.getElementById('liveFeed');
                            const anomalyList = document.getElementById('anomalyList');

                            for (const a of anomalyItems) {
                                // Toast notification for high/critical
                                if (a.severity === 'critical' || a.severity === 'high') {
                                    showToast(
                                        (a.severity === 'critical' ? 'CRITIQUE' : 'HAUTE') + ': ' + (a.anomaly_type || '').replace(/_/g, ' ') + (a.description ? ' - ' + a.description : ''),
                                        a.severity
                                    );
                                }

                                // Add to live feed
                                if (feed) {
                                    const item = document.createElement('div');
                                    item.innerHTML = '<div class="feed-item ' + a.severity + '">' +
                                        '<div style="display:flex;justify-content:space-between;align-items:center;">' +
                                        '<div><span class="severity severity-' + a.severity + '">' + a.severity + '</span> ' +
                                        '<span class="feed-type">' + (a.anomaly_type || '').replace(/_/g, ' ') + '</span></div>' +
                                        '<span class="feed-time">maintenant</span>' +
                                        '</div>' +
                                        (a.description ? '<div style="margin-top:5px;font-size:13px;color:#555;">' + a.description + '</div>' : '') +
                                        '</div>';
                                    feed.insertBefore(item.firstChild, feed.firstChild);
                                    // Keep max 50 items in feed
                                    while (feed.children.length > 50) feed.removeChild(feed.lastChild);
                                }

                                // Also prepend to anomaly list
                                if (anomalyList) {
                                    const wrapper = document.createElement('div');
                                    wrapper.innerHTML = renderAnomalyItem({
                                        anomaly_id: a.anomaly_id || '-',
                                        anomaly_type: a.anomaly_type,
                                        severity: a.severity,
                                        description: a.description,
                                        detected_at: new Date().toISOString(),
                                        detection_method: a.detection_method || '-',
                                        confidence: a.confidence || 0
                                    });
                                    anomalyList.insertBefore(wrapper.firstChild, anomalyList.firstChild);
                                }
                            }
                        }
                    } catch (e) {
                        console.error('WebSocket message parse error:', e);
                    }
                };

                activeWebSocket.onclose = function() {
                    const feed = document.getElementById('liveFeed');
                    if (feed) {
                        const item = document.createElement('div');
                        item.className = 'feed-item';
                        item.style.borderLeftColor = '#6c757d';
                        item.innerHTML = '<span style="color:#6c757d;">Connexion WebSocket fermee</span>';
                        feed.insertBefore(item, feed.firstChild);
                    }
                };

                activeWebSocket.onerror = function() {
                    const feed = document.getElementById('liveFeed');
                    if (feed) {
                        feed.innerHTML = '<div class="feed-item" style="border-left-color:#dc3545;background:#f8d7da;"><span style="color:#721c24;">Erreur de connexion WebSocket</span></div>';
                    }
                };

            } catch (e) {
                console.error('WebSocket connection error:', e);
            }
        }

        function disconnectWebSocket() {
            if (pingIntervalId) {
                clearInterval(pingIntervalId);
                pingIntervalId = null;
            }
            if (activeWebSocket) {
                activeWebSocket.close();
                activeWebSocket = null;
            }
        }

        // ========== LIVE VIDEO VIEW ==========
        function toggleLiveView(sessionId) {
            if (liveViewActive) {
                stopLiveView();
            } else {
                startLiveView(sessionId);
            }
        }

        function startLiveView(sessionId) {
            stopLiveView();
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = wsProtocol + '//' + window.location.host + '/monitoring/sessions/' + sessionId + '/live';

            try {
                liveWebSocket = new WebSocket(wsUrl);

                liveWebSocket.onopen = function() {
                    liveViewActive = true;
                    const btn = document.getElementById('liveToggleBtn');
                    if (btn) { btn.textContent = 'Arreter le direct'; btn.className = 'btn-live-stop'; }
                    const dot = document.getElementById('liveStatusDot');
                    if (dot) { dot.className = 'live-status-indicator connected'; }
                    const placeholder = document.getElementById('liveVideoPlaceholder');
                    if (placeholder) { placeholder.textContent = 'En attente de la prochaine image...'; }

                    livePingIntervalId = setInterval(function() {
                        if (liveWebSocket && liveWebSocket.readyState === WebSocket.OPEN) {
                            liveWebSocket.send(JSON.stringify({ type: 'ping' }));
                        }
                    }, 30000);
                };

                liveWebSocket.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'pong') return;

                        if (data.type === 'frame') {
                            const img = document.getElementById('liveVideoFrame');
                            const placeholder = document.getElementById('liveVideoPlaceholder');
                            const overlay = document.getElementById('liveVideoOverlay');
                            if (img) {
                                img.src = 'data:image/jpeg;base64,' + data.frame_data;
                                img.style.display = 'block';
                            }
                            if (placeholder) placeholder.style.display = 'none';
                            if (overlay) {
                                overlay.style.display = 'flex';
                                const frameInfo = document.getElementById('liveFrameInfo');
                                const timestamp = document.getElementById('liveTimestamp');
                                if (frameInfo) frameInfo.textContent = 'Frame #' + data.frame_number;
                                if (timestamp) timestamp.textContent = new Date(data.timestamp).toLocaleTimeString('fr-FR');
                            }

                            if (data.anomalies && data.anomalies.length > 0) {
                                showLiveAnomalies(data.anomalies);
                            }
                        } else if (data.type === 'session_stopped') {
                            stopLiveView();
                            const placeholder = document.getElementById('liveVideoPlaceholder');
                            if (placeholder) {
                                placeholder.style.display = 'block';
                                placeholder.textContent = 'Session de monitoring arretee';
                            }
                            const btn = document.getElementById('liveToggleBtn');
                            if (btn) { btn.disabled = true; btn.textContent = 'Session terminee'; }
                        }
                    } catch (e) {
                        console.error('Live WS message parse error:', e);
                    }
                };

                liveWebSocket.onclose = function() {
                    liveViewActive = false;
                    const btn = document.getElementById('liveToggleBtn');
                    if (btn && !btn.disabled) { btn.textContent = 'Voir en direct'; btn.className = 'btn-live-start'; }
                    const dot = document.getElementById('liveStatusDot');
                    if (dot) { dot.className = 'live-status-indicator disconnected'; }
                };

                liveWebSocket.onerror = function() {
                    console.error('Live WebSocket error');
                };

            } catch (e) {
                console.error('Live WebSocket connection error:', e);
            }
        }

        function stopLiveView() {
            if (livePingIntervalId) {
                clearInterval(livePingIntervalId);
                livePingIntervalId = null;
            }
            if (liveWebSocket) {
                liveWebSocket.close();
                liveWebSocket = null;
            }
            liveViewActive = false;
            const img = document.getElementById('liveVideoFrame');
            if (img) { img.style.display = 'none'; img.src = ''; }
            const overlay = document.getElementById('liveVideoOverlay');
            if (overlay) overlay.style.display = 'none';
            const banner = document.getElementById('liveAnomalyBanner');
            if (banner) banner.style.display = 'none';
            const placeholder = document.getElementById('liveVideoPlaceholder');
            if (placeholder) { placeholder.style.display = 'block'; placeholder.textContent = 'Cliquez sur "Voir en direct" pour afficher le flux webcam de l\\'etudiant'; }
            const btn = document.getElementById('liveToggleBtn');
            if (btn && !btn.disabled) { btn.textContent = 'Voir en direct'; btn.className = 'btn-live-start'; }
            const dot = document.getElementById('liveStatusDot');
            if (dot) { dot.className = 'live-status-indicator disconnected'; }
        }

        function showLiveAnomalies(anomalies) {
            const banner = document.getElementById('liveAnomalyBanner');
            if (!banner) return;
            // Show highest severity anomaly
            const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
            anomalies.sort(function(a, b) { return (severityOrder[a.severity] || 4) - (severityOrder[b.severity] || 4); });
            const top = anomalies[0];
            banner.className = 'live-anomaly-banner ' + top.severity;
            let text = (top.anomaly_type || '').replace(/_/g, ' ').toUpperCase();
            if (top.description) text += ' — ' + top.description;
            if (anomalies.length > 1) text += ' (+' + (anomalies.length - 1) + ' autre' + (anomalies.length > 2 ? 's' : '') + ')';
            banner.textContent = text;
            banner.style.display = 'block';
            setTimeout(function() { if (banner) banner.style.display = 'none'; }, 5000);
        }
    </script>
</body>
</html>
"""
