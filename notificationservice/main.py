import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from interface.api.controllers import notification_controller
from application.use_cases.send_notification import SendNotification
from infrastructure.repositories.sqlalchemy_notification_repository import SQLAlchemyNotificationRepository
from infrastructure.email.smtp_email_sender import MockEmailSender, SMTPEmailSender
from infrastructure.push.websocket_sender import WebSocketSender, MockRealtimeSender
from infrastructure.events.kafka_consumer import KafkaEventConsumer
from infrastructure.database.mariadb_cluster import engine
from infrastructure.database.models import Base

consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task

    # Create tables on startup
    Base.metadata.create_all(bind=engine)

    repo = SQLAlchemyNotificationRepository()

    if os.getenv("USE_MOCK_SENDERS", "true").lower() == "true":
        email_sender = MockEmailSender()
        realtime_sender = MockRealtimeSender()
    else:
        email_sender = SMTPEmailSender()
        realtime_sender = WebSocketSender()

    send_notification = SendNotification(repo, email_sender, realtime_sender)
    kafka_consumer = KafkaEventConsumer(send_notification)

    if os.getenv("ENABLE_KAFKA_CONSUMER", "false").lower() == "true":
        await kafka_consumer.start()
        consumer_task = asyncio.create_task(kafka_consumer.consume())

    yield

    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await kafka_consumer.stop()


app = FastAPI(
    title="ProctorWise Notification Service",
    description="Email and WebSocket notification service with Kafka event processing",
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

app.include_router(notification_controller.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "notification"}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProctorWise - Notifications</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding-top: 80px; }

        /* Navbar */
        .navbar { position: fixed; top: 0; left: 0; right: 0; height: 60px; background: rgba(255,255,255,0.98); box-shadow: 0 2px 20px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between; padding: 0 30px; z-index: 1000; }
        .navbar-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: #333; font-weight: bold; font-size: 18px; }
        .navbar-brand:hover { color: #667eea; }
        .navbar-brand .logo { font-size: 24px; }
        .navbar-nav { display: flex; align-items: center; gap: 8px; }
        .nav-link { padding: 8px 16px; border-radius: 8px; text-decoration: none; color: #555; font-size: 14px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
        .nav-link:hover { background: #f0f0f0; color: #333; }
        .nav-link.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .nav-link .nav-icon { font-size: 16px; }
        .navbar-user { display: flex; align-items: center; gap: 12px; }
        .btn-home { padding: 8px 12px; background: #f0f0f0; color: #333; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; transition: background 0.2s; text-decoration: none; }
        .btn-home:hover { background: #e0e0e0; }

        .container { max-width: 900px; margin: 0 auto; padding: 20px; }
        .header { display: none; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .user-name { font-weight: 500; color: #333; font-size: 14px; }
        .btn-logout { padding: 8px 16px; background: #e94560; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 13px; transition: background 0.2s; }
        .btn-logout:hover { background: #d63050; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { color: #333; margin-bottom: 20px; font-size: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .hidden { display: none; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .tab:hover { background: #d0d0d0; }
        .tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .login-prompt { text-align: center; padding: 60px 20px; }
        .login-prompt a { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; font-size: 18px; }
        .login-prompt a:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
        .role-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .role-student { background: #cce5ff; color: #004085; }
        .role-teacher { background: #d4edda; color: #155724; }
        .role-proctor { background: #fff3cd; color: #856404; }
        .role-admin { background: #f8d7da; color: #721c24; }

        /* Notification list */
        .notification-list { max-height: 500px; overflow-y: auto; }
        .notification-item { padding: 15px; border: 1px solid #e0e0e0; border-radius: 10px; margin-bottom: 10px; transition: all 0.2s; }
        .notification-item:hover { border-color: #667eea; box-shadow: 0 2px 10px rgba(102, 126, 234, 0.1); }
        .notification-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
        .notification-subject { font-weight: 600; color: #333; font-size: 16px; }
        .notification-meta { display: flex; gap: 10px; align-items: center; }
        .notification-time { font-size: 12px; color: #888; }
        .notification-body { color: #555; font-size: 14px; line-height: 1.5; }
        .notification-type { padding: 3px 10px; border-radius: 15px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .type-exam_reminder { background: #cce5ff; color: #004085; }
        .type-anomaly_detected { background: #fff3cd; color: #856404; }
        .type-grade_ready { background: #d4edda; color: #155724; }
        .type-high_risk_alert { background: #f8d7da; color: #721c24; }
        .notification-channel { font-size: 11px; color: #888; }
        .notification-status { padding: 2px 8px; border-radius: 10px; font-size: 10px; }
        .status-sent { background: #d4edda; color: #155724; }
        .status-pending { background: #fff3cd; color: #856404; }
        .status-failed { background: #f8d7da; color: #721c24; }

        /* Preferences */
        .pref-section { margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid #e0e0e0; }
        .pref-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .pref-section h3 { color: #333; margin-bottom: 15px; font-size: 16px; }
        .toggle-group { display: flex; gap: 20px; flex-wrap: wrap; }
        .toggle-item { display: flex; align-items: center; gap: 10px; padding: 10px 15px; background: #f8f9fa; border-radius: 8px; }
        .toggle-item label { cursor: pointer; font-size: 14px; color: #333; }
        .toggle-switch { position: relative; width: 50px; height: 26px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: 0.3s; border-radius: 26px; }
        .toggle-slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background-color: white; transition: 0.3s; border-radius: 50%; }
        .toggle-switch input:checked + .toggle-slider { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .toggle-switch input:checked + .toggle-slider:before { transform: translateX(24px); }
        .checkbox-group { display: flex; flex-wrap: wrap; gap: 10px; }
        .checkbox-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #f8f9fa; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
        .checkbox-item:hover { background: #e9ecef; }
        .checkbox-item input { width: 18px; height: 18px; cursor: pointer; }
        .checkbox-item label { cursor: pointer; font-size: 13px; }
        .checkbox-item.checked { background: #e8edff; border: 1px solid #667eea; }
        button.btn-save { padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 20px; }
        button.btn-save:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
        .message { padding: 12px 20px; border-radius: 8px; margin-top: 15px; text-align: center; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }

        /* Toast notifications */
        .toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; }
        .toast { padding: 15px 20px; background: white; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.2); display: flex; align-items: flex-start; gap: 12px; min-width: 300px; max-width: 400px; animation: slideIn 0.3s ease; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
        .toast.hiding { animation: slideOut 0.3s ease forwards; }
        .toast-icon { font-size: 24px; }
        .toast-content { flex: 1; }
        .toast-title { font-weight: 600; color: #333; margin-bottom: 4px; }
        .toast-body { font-size: 13px; color: #666; }
        .toast-close { background: none; border: none; font-size: 18px; color: #999; cursor: pointer; padding: 0; line-height: 1; }
        .toast-close:hover { color: #333; }
        .toast.type-exam_reminder { border-left: 4px solid #007bff; }
        .toast.type-anomaly_detected { border-left: 4px solid #ffc107; }
        .toast.type-grade_ready { border-left: 4px solid #28a745; }
        .toast.type-high_risk_alert { border-left: 4px solid #dc3545; }

        /* Connection status */
        .ws-status { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #666; }
        .ws-dot { width: 8px; height: 8px; border-radius: 50%; }
        .ws-dot.connected { background: #28a745; }
        .ws-dot.disconnected { background: #dc3545; }
        .ws-dot.connecting { background: #ffc107; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

        /* Empty state */
        .empty-state { text-align: center; padding: 40px; color: #888; }
        .empty-state svg { width: 80px; height: 80px; margin-bottom: 15px; opacity: 0.5; }

        /* Refresh button */
        .btn-refresh { padding: 8px 16px; background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 6px; }
        .btn-refresh:hover { background: #e9ecef; }
        .btn-refresh.loading svg { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
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
            <div class="ws-status">
                <span class="ws-dot disconnected" id="wsDot"></span>
                <span id="wsStatusText">Deconnecte</span>
            </div>
            <span id="navUserName" class="user-name"></span>
            <span id="navUserRole" class="role-badge"></span>
            <button class="btn-logout" onclick="logout()">Deconnexion</button>
        </div>
    </nav>

    <div class="container">
        <div id="loginRequired" class="card login-prompt">
            <h2>Connexion requise</h2>
            <p style="margin: 20px 0; color: #666;">Veuillez vous connecter pour acceder a vos notifications.</p>
            <a href="http://localhost:8001">Se connecter</a>
        </div>

        <div id="mainApp" class="hidden">

            <div class="tabs">
                <button class="tab active" onclick="showTab('history')">Historique</button>
                <button class="tab" onclick="showTab('preferences')">Preferences</button>
            </div>

            <!-- History Tab -->
            <div id="historyTab" class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin-bottom: 0; border-bottom: none; padding-bottom: 0;">Historique des notifications</h2>
                    <button class="btn-refresh" onclick="loadNotifications()" id="refreshBtn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                        </svg>
                        Actualiser
                    </button>
                </div>
                <div id="notificationList" class="notification-list">
                    <div class="empty-state">
                        <p>Chargement...</p>
                    </div>
                </div>
            </div>

            <!-- Preferences Tab -->
            <div id="preferencesTab" class="card hidden">
                <h2>Preferences de notification</h2>

                <div class="pref-section">
                    <h3>Canaux de notification</h3>
                    <div class="toggle-group">
                        <div class="toggle-item">
                            <label class="toggle-switch">
                                <input type="checkbox" id="emailEnabled" checked>
                                <span class="toggle-slider"></span>
                            </label>
                            <label for="emailEnabled">Email</label>
                        </div>
                        <div class="toggle-item">
                            <label class="toggle-switch">
                                <input type="checkbox" id="websocketEnabled" checked>
                                <span class="toggle-slider"></span>
                            </label>
                            <label for="websocketEnabled">Temps reel (WebSocket)</label>
                        </div>
                    </div>
                </div>

                <div class="pref-section">
                    <h3>Types de notifications</h3>
                    <div class="checkbox-group" id="notificationTypes">
                        <div class="checkbox-item checked">
                            <input type="checkbox" id="type_exam_reminder" value="exam_reminder" checked>
                            <label for="type_exam_reminder">Rappels d'examen</label>
                        </div>
                        <div class="checkbox-item checked">
                            <input type="checkbox" id="type_anomaly_detected" value="anomaly_detected" checked>
                            <label for="type_anomaly_detected">Anomalies detectees</label>
                        </div>
                        <div class="checkbox-item checked">
                            <input type="checkbox" id="type_grade_ready" value="grade_ready" checked>
                            <label for="type_grade_ready">Notes disponibles</label>
                        </div>
                        <div class="checkbox-item checked">
                            <input type="checkbox" id="type_high_risk_alert" value="high_risk_alert" checked>
                            <label for="type_high_risk_alert">Alertes risque eleve</label>
                        </div>
                    </div>
                </div>

                <div class="pref-section">
                    <h3>Rappels avant examen</h3>
                    <div class="checkbox-group" id="reminderHours">
                        <div class="checkbox-item checked">
                            <input type="checkbox" id="reminder_24" value="24" checked>
                            <label for="reminder_24">24 heures avant</label>
                        </div>
                        <div class="checkbox-item checked">
                            <input type="checkbox" id="reminder_1" value="1" checked>
                            <label for="reminder_1">1 heure avant</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="reminder_2" value="2">
                            <label for="reminder_2">2 heures avant</label>
                        </div>
                        <div class="checkbox-item">
                            <input type="checkbox" id="reminder_12" value="12">
                            <label for="reminder_12">12 heures avant</label>
                        </div>
                    </div>
                </div>

                <button class="btn-save" onclick="savePreferences()">Enregistrer les preferences</button>
                <div id="prefMessage" class="message hidden"></div>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <script>
        let currentUser = null;
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            if (token) {
                localStorage.setItem('token', token);
                window.history.replaceState({}, document.title, window.location.pathname);
            }
            const storedToken = localStorage.getItem('token');
            if (storedToken) parseToken(storedToken);

            // Update checkbox styling
            document.querySelectorAll('.checkbox-item input').forEach(cb => {
                cb.addEventListener('change', function() {
                    this.closest('.checkbox-item').classList.toggle('checked', this.checked);
                });
            });
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
            const roleNames = { student: 'Etudiant', teacher: 'Enseignant', proctor: 'Surveillant', admin: 'Admin' };
            roleEl.textContent = roleNames[currentUser.role] || currentUser.role;
            roleEl.className = 'role-badge role-' + currentUser.role;

            renderNavLinks();
            loadNotifications();
            loadPreferences();
            connectWebSocket();
        }

        function renderNavLinks() {
            const nav = document.getElementById('navLinks');
            const token = localStorage.getItem('token');
            const links = [
                { name: 'Examens', icon: '📝', url: 'http://localhost:8000', active: false, roles: ['student', 'teacher', 'admin'] },
                { name: 'Monitoring', icon: '👁️', url: 'http://localhost:8003', active: false, roles: ['proctor', 'admin'] },
                { name: 'Analytics', icon: '📊', url: 'http://localhost:8006', active: false, roles: ['admin'] }
            ];
            // Add a "Notifications" indicator since we're on this page
            nav.innerHTML = '<span class="nav-link active"><span class="nav-icon">🔔</span> Notifications</span>' +
                links
                .filter(l => l.roles.includes(currentUser.role))
                .map(l => '<a href="' + l.url + '?token=' + token + '" class="nav-link"><span class="nav-icon">' + l.icon + '</span> ' + l.name + '</a>')
                .join('');
        }

        function goToHub() {
            window.location.href = 'http://localhost:8001';
        }

        function logout() {
            if (ws) ws.close();
            localStorage.removeItem('token');
            window.location.href = 'http://localhost:8001';
        }

        function showTab(tab) {
            document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('historyTab').classList.toggle('hidden', tab !== 'history');
            document.getElementById('preferencesTab').classList.toggle('hidden', tab !== 'preferences');
        }

        function formatDateTime(iso) {
            if (!iso) return '-';
            const date = new Date(iso);
            const now = new Date();
            const diff = now - date;

            if (diff < 60000) return 'A l\\'instant';
            if (diff < 3600000) return 'Il y a ' + Math.floor(diff / 60000) + ' min';
            if (diff < 86400000) return 'Il y a ' + Math.floor(diff / 3600000) + ' h';

            return date.toLocaleString('fr-FR', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        }

        function getTypeIcon(type) {
            const icons = {
                'exam_reminder': '📅',
                'anomaly_detected': '⚠️',
                'grade_ready': '📊',
                'high_risk_alert': '🚨'
            };
            return icons[type] || '📬';
        }

        function getTypeName(type) {
            const names = {
                'exam_reminder': 'Rappel',
                'anomaly_detected': 'Anomalie',
                'grade_ready': 'Note',
                'high_risk_alert': 'Alerte'
            };
            return names[type] || type;
        }

        // ========== NOTIFICATIONS ==========
        async function loadNotifications() {
            const btn = document.getElementById('refreshBtn');
            btn.classList.add('loading');

            try {
                const res = await fetch('/notifications/user/' + currentUser.user_id);
                const notifications = await res.json();
                renderNotifications(notifications);
            } catch (e) {
                console.error('Load notifications error:', e);
                document.getElementById('notificationList').innerHTML =
                    '<div class="empty-state"><p style="color: #dc3545;">Erreur de chargement</p></div>';
            } finally {
                btn.classList.remove('loading');
            }
        }

        function renderNotifications(notifications) {
            const container = document.getElementById('notificationList');

            if (!notifications || notifications.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>Aucune notification</p></div>';
                return;
            }

            let html = '';
            notifications.forEach(n => {
                html += '<div class="notification-item">';
                html += '<div class="notification-header">';
                html += '<span class="notification-subject">' + getTypeIcon(n.notification_type) + ' ' + n.subject + '</span>';
                html += '<div class="notification-meta">';
                html += '<span class="notification-type type-' + n.notification_type + '">' + getTypeName(n.notification_type) + '</span>';
                html += '<span class="notification-status status-' + n.status + '">' + n.status + '</span>';
                html += '</div></div>';
                html += '<div class="notification-body">' + n.body + '</div>';
                html += '<div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">';
                html += '<span class="notification-channel">Canal: ' + n.channel + '</span>';
                html += '<span class="notification-time">' + formatDateTime(n.created_at) + '</span>';
                html += '</div></div>';
            });
            container.innerHTML = html;
        }

        // ========== PREFERENCES ==========
        async function loadPreferences() {
            try {
                const res = await fetch('/notifications/preferences/' + currentUser.user_id);
                if (res.ok) {
                    const prefs = await res.json();
                    applyPreferences(prefs);
                }
            } catch (e) {
                console.error('Load preferences error:', e);
            }
        }

        function applyPreferences(prefs) {
            document.getElementById('emailEnabled').checked = prefs.email_enabled;
            document.getElementById('websocketEnabled').checked = prefs.websocket_enabled;

            // Notification types
            const types = ['exam_reminder', 'anomaly_detected', 'grade_ready', 'high_risk_alert'];
            types.forEach(type => {
                const cb = document.getElementById('type_' + type);
                if (cb) {
                    cb.checked = prefs.notification_types.includes(type);
                    cb.closest('.checkbox-item').classList.toggle('checked', cb.checked);
                }
            });

            // Reminder hours
            const defaultHours = [1, 2, 12, 24];
            defaultHours.forEach(h => {
                const cb = document.getElementById('reminder_' + h);
                if (cb) {
                    cb.checked = prefs.reminder_hours_before.includes(h);
                    cb.closest('.checkbox-item').classList.toggle('checked', cb.checked);
                }
            });
        }

        async function savePreferences() {
            const notificationTypes = [];
            ['exam_reminder', 'anomaly_detected', 'grade_ready', 'high_risk_alert'].forEach(type => {
                if (document.getElementById('type_' + type).checked) {
                    notificationTypes.push(type);
                }
            });

            const reminderHours = [];
            [1, 2, 12, 24].forEach(h => {
                if (document.getElementById('reminder_' + h).checked) {
                    reminderHours.push(h);
                }
            });

            const prefs = {
                email: currentUser.email,
                email_enabled: document.getElementById('emailEnabled').checked,
                websocket_enabled: document.getElementById('websocketEnabled').checked,
                notification_types: notificationTypes,
                reminder_hours_before: reminderHours
            };

            try {
                const res = await fetch('/notifications/preferences/' + currentUser.user_id, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(prefs)
                });

                const msg = document.getElementById('prefMessage');
                if (res.ok) {
                    msg.textContent = 'Preferences enregistrees!';
                    msg.className = 'message success';
                } else {
                    msg.textContent = 'Erreur lors de l\\'enregistrement';
                    msg.className = 'message error';
                }
                msg.classList.remove('hidden');
                setTimeout(() => msg.classList.add('hidden'), 3000);
            } catch (e) {
                console.error('Save preferences error:', e);
            }
        }

        // ========== WEBSOCKET ==========
        function connectWebSocket() {
            updateWsStatus('connecting');

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = protocol + '//' + window.location.host + '/notifications/ws/' + currentUser.user_id;

            try {
                ws = new WebSocket(wsUrl);

                ws.onopen = function() {
                    console.log('WebSocket connected');
                    reconnectAttempts = 0;
                    updateWsStatus('connected');
                };

                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'notification') {
                            showToast(data);
                            loadNotifications(); // Refresh list
                        }
                    } catch (e) {
                        console.log('WS message:', event.data);
                    }
                };

                ws.onclose = function() {
                    console.log('WebSocket disconnected');
                    updateWsStatus('disconnected');
                    attemptReconnect();
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    updateWsStatus('disconnected');
                };
            } catch (e) {
                console.error('WebSocket connection error:', e);
                updateWsStatus('disconnected');
            }
        }

        function attemptReconnect() {
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                console.log('Reconnecting... attempt ' + reconnectAttempts);
                setTimeout(connectWebSocket, 3000 * reconnectAttempts);
            }
        }

        function updateWsStatus(status) {
            const dot = document.getElementById('wsDot');
            const text = document.getElementById('wsStatusText');

            dot.className = 'ws-dot ' + status;
            const statusTexts = {
                'connected': 'Connecte',
                'disconnected': 'Deconnecte',
                'connecting': 'Connexion...'
            };
            text.textContent = statusTexts[status] || status;
        }

        // ========== TOAST NOTIFICATIONS ==========
        function showToast(data) {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast type-' + (data.notification_type || 'default');

            const icon = getTypeIcon(data.notification_type);

            toast.innerHTML =
                '<span class="toast-icon">' + icon + '</span>' +
                '<div class="toast-content">' +
                '<div class="toast-title">' + (data.title || data.subject || 'Notification') + '</div>' +
                '<div class="toast-body">' + (data.body || '') + '</div>' +
                '</div>' +
                '<button class="toast-close" onclick="closeToast(this)">&times;</button>';

            container.appendChild(toast);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.classList.add('hiding');
                    setTimeout(() => toast.remove(), 300);
                }
            }, 5000);
        }

        function closeToast(btn) {
            const toast = btn.closest('.toast');
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }

        // Ping WebSocket to keep alive
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    </script>
</body>
</html>
"""
