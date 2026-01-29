import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from interface.api.controllers import user_controller

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


app = FastAPI(title="UserService", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_controller.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "userservice"}

@app.get("/", response_class=HTMLResponse)
async def home():
    html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProctorWise</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; min-height: 100vh; }

        /* Login Container */
        .login-container { min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .login-box { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 100%; max-width: 450px; }
        .login-box h1 { text-align: center; color: #333; margin-bottom: 10px; font-size: 32px; }
        .login-box .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
        .tabs { display: flex; margin-bottom: 30px; }
        .tab { flex: 1; padding: 15px; text-align: center; cursor: pointer; border: none; background: #f0f0f0; font-size: 16px; transition: all 0.3s; }
        .tab:first-child { border-radius: 10px 0 0 10px; }
        .tab:last-child { border-radius: 0 10px 10px 0; }
        .tab.active { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input, select { width: 100%; padding: 14px; border: 2px solid #e0e0e0; border-radius: 10px; font-size: 16px; transition: border-color 0.3s; }
        input:focus, select:focus { outline: none; border-color: #667eea; }
        button[type="submit"] { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 18px; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        button[type="submit"]:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4); }
        .message { padding: 15px; border-radius: 10px; margin-top: 20px; text-align: center; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .hidden { display: none; }

        /* Hub Container */
        .hub-container { min-height: 100vh; padding: 30px 20px; background: linear-gradient(180deg, #f5f7fa 0%, #e4e8f0 100%); }
        .hub-header { max-width: 1200px; margin: 0 auto 40px; display: flex; justify-content: space-between; align-items: center; padding: 20px 30px; background: white; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .hub-header h1 { color: #333; font-size: 24px; display: flex; align-items: center; gap: 10px; }
        .hub-header .logo { font-size: 28px; }
        .user-menu { display: flex; align-items: center; gap: 15px; }
        .user-name { font-weight: 500; color: #333; }
        .role-badge { padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .role-student { background: #e3f2fd; color: #1565c0; }
        .role-teacher { background: #e8f5e9; color: #2e7d32; }
        .role-proctor { background: #fff3e0; color: #ef6c00; }
        .role-admin { background: #fce4ec; color: #c2185b; }
        .btn-logout { padding: 10px 20px; background: #e94560; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; transition: background 0.2s; }
        .btn-logout:hover { background: #d63050; }

        /* Notification Bell */
        .notif-bell { position: relative; cursor: pointer; font-size: 22px; padding: 8px; border-radius: 50%; transition: background 0.2s; }
        .notif-bell:hover { background: #f0f0f0; }
        .notif-badge { position: absolute; top: 2px; right: 2px; background: #e94560; color: white; font-size: 10px; font-weight: bold; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; }
        .notif-badge.hidden { display: none; }

        /* Welcome Section */
        .welcome-section { max-width: 1200px; margin: 0 auto 40px; text-align: center; }
        .welcome-section h2 { font-size: 36px; margin-bottom: 10px; color: #333; }
        .welcome-section p { font-size: 18px; color: #666; }

        /* Service Grid */
        .services-grid { max-width: 1000px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; }
        .service-card { background: white; border-radius: 20px; padding: 35px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.08); transition: all 0.3s; cursor: pointer; text-decoration: none; display: block; border: 2px solid transparent; }
        .service-card:hover { transform: translateY(-8px); box-shadow: 0 12px 40px rgba(0,0,0,0.15); }
        .service-icon { font-size: 52px; margin-bottom: 20px; }
        .service-card h3 { color: #333; font-size: 22px; margin-bottom: 10px; }
        .service-card p { color: #666; font-size: 14px; line-height: 1.6; }
        .service-card .service-tag { display: inline-block; margin-top: 15px; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }

        /* Service Colors */
        .service-exams { border-color: #e8f5e9; }
        .service-exams:hover { border-color: #4CAF50; }
        .service-exams .service-tag { background: #e8f5e9; color: #2e7d32; }
        .service-monitoring { border-color: #fff3e0; }
        .service-monitoring:hover { border-color: #FF9800; }
        .service-monitoring .service-tag { background: #fff3e0; color: #ef6c00; }
        .service-analytics { border-color: #e3f2fd; }
        .service-analytics:hover { border-color: #2196F3; }
        .service-analytics .service-tag { background: #e3f2fd; color: #1565c0; }

        /* Quick Stats - hidden for now */
        .quick-stats { display: none; }
    </style>
</head>
<body>
    <!-- Login/Register View -->
    <div id="loginView" class="login-container">
        <div class="login-box">
            <h1>🎓 ProctorWise</h1>
            <p class="subtitle">Plateforme de surveillance d'examens</p>

            <div class="tabs">
                <button class="tab active" onclick="showTab('login')">Connexion</button>
                <button class="tab" onclick="showTab('register')">Inscription</button>
            </div>

            <form id="loginForm" onsubmit="login(event)">
                <div class="form-group">
                    <label for="loginEmail">Email</label>
                    <input type="email" id="loginEmail" required placeholder="votre@email.com">
                </div>
                <div class="form-group">
                    <label for="loginPassword">Mot de passe</label>
                    <input type="password" id="loginPassword" required placeholder="********">
                </div>
                <button type="submit">Se connecter</button>
            </form>

            <form id="registerForm" class="hidden" onsubmit="register(event)">
                <div class="form-group">
                    <label for="regName">Nom complet</label>
                    <input type="text" id="regName" required placeholder="Jean Dupont">
                </div>
                <div class="form-group">
                    <label for="regEmail">Email</label>
                    <input type="email" id="regEmail" required placeholder="votre@email.com">
                </div>
                <div class="form-group">
                    <label for="regPassword">Mot de passe</label>
                    <input type="password" id="regPassword" required placeholder="********" minlength="6">
                </div>
                <div class="form-group">
                    <label for="regRole">Role</label>
                    <select id="regRole">
                        <option value="student">Etudiant</option>
                        <option value="teacher">Enseignant</option>
                        <option value="proctor">Surveillant</option>
                        <option value="admin">Administrateur</option>
                    </select>
                </div>
                <button type="submit">S'inscrire</button>
            </form>

            <div id="message" class="message hidden"></div>
        </div>
    </div>

    <!-- Hub View (after login) -->
    <div id="hubView" class="hub-container hidden">
        <div class="hub-header">
            <h1><span class="logo">🎓</span> ProctorWise</h1>
            <div class="user-menu">
                <span class="user-name" id="hubUserName"></span>
                <span class="role-badge" id="hubUserRole"></span>
                <a href="http://localhost:8005" id="notifBellLink" class="notif-bell" title="Notifications">
                    🔔
                    <span class="notif-badge hidden" id="notifBadge">0</span>
                </a>
                <button class="btn-logout" onclick="logout()">Deconnexion</button>
            </div>
        </div>

        <div class="welcome-section">
            <h2>Bienvenue, <span id="hubWelcomeName"></span> !</h2>
            <p>Selectionnez un service pour commencer</p>
        </div>

        <div class="services-grid" id="servicesGrid">
            <!-- Services will be populated based on role -->
        </div>

        <div class="quick-stats" id="quickStats">
            <!-- Stats will be populated -->
        </div>
    </div>

    <script>
        let currentUser = null;
        let currentToken = null;

        // Check if already logged in on page load
        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);

            // Check for logout request from other services
            if (urlParams.get('logout') === 'true') {
                localStorage.removeItem('token');
                window.history.replaceState({}, document.title, window.location.pathname);
                return; // Stay on login page
            }

            const token = localStorage.getItem('token');
            if (token) {
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    // Check if token is expired
                    if (payload.exp * 1000 > Date.now()) {
                        currentToken = token;
                        currentUser = {
                            user_id: payload.sub || payload.user_id,
                            name: payload.name,
                            email: payload.email,
                            role: payload.role
                        };
                        showHub();
                    } else {
                        localStorage.removeItem('token');
                    }
                } catch (e) {
                    localStorage.removeItem('token');
                }
            }
        };

        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
            document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');
            document.getElementById('message').classList.add('hidden');
        }

        function showMessage(text, isError = false) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + (isError ? 'error' : 'success');
        }

        async function login(e) {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;

            try {
                const res = await fetch('/users/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();

                if (res.ok) {
                    currentToken = data.access_token;
                    localStorage.setItem('token', currentToken);

                    const payload = JSON.parse(atob(currentToken.split('.')[1]));
                    currentUser = {
                        user_id: payload.sub || payload.user_id,
                        name: payload.name,
                        email: payload.email,
                        role: payload.role
                    };

                    showMessage('Connexion reussie!');
                    setTimeout(showHub, 500);
                } else {
                    showMessage(data.detail || 'Erreur de connexion', true);
                }
            } catch (err) {
                showMessage('Erreur de connexion au serveur', true);
            }
        }

        async function register(e) {
            e.preventDefault();
            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;
            const role = document.getElementById('regRole').value;

            try {
                const res = await fetch('/users/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password, role })
                });
                const data = await res.json();

                if (res.ok) {
                    showMessage('Inscription reussie! Vous pouvez maintenant vous connecter.');
                    setTimeout(() => {
                        document.querySelector('.tab:first-child').click();
                    }, 2000);
                } else {
                    showMessage(data.detail || 'Erreur d\\'inscription', true);
                }
            } catch (err) {
                showMessage('Erreur de connexion au serveur', true);
            }
        }

        function showHub() {
            document.getElementById('loginView').classList.add('hidden');
            document.getElementById('hubView').classList.remove('hidden');

            // Update user info
            document.getElementById('hubUserName').textContent = currentUser.name;
            document.getElementById('hubWelcomeName').textContent = currentUser.name.split(' ')[0];

            const roleEl = document.getElementById('hubUserRole');
            const roleNames = { student: 'Etudiant', teacher: 'Enseignant', proctor: 'Surveillant', admin: 'Admin' };
            roleEl.textContent = roleNames[currentUser.role] || currentUser.role;
            roleEl.className = 'role-badge role-' + currentUser.role;

            // Render services based on role
            renderServices();
            loadNotificationCount();
        }

        function renderServices() {
            const grid = document.getElementById('servicesGrid');
            const services = getServicesForRole(currentUser.role);
            const token = localStorage.getItem('token');

            grid.innerHTML = services.map(s => `
                <a href="${s.url}?token=${token}" class="service-card ${s.class}">
                    <div class="service-icon">${s.icon}</div>
                    <h3>${s.name}</h3>
                    <p>${s.description}</p>
                    <span class="service-tag">${s.tag}</span>
                </a>
            `).join('');
        }

        function getServicesForRole(role) {
            const allServices = {
                exams: {
                    name: 'Examens',
                    icon: '📝',
                    description: 'Gerer vos examens, reservations et resultats',
                    url: 'http://localhost:8000',
                    tag: 'Reservations',
                    class: 'service-exams',
                    roles: ['student', 'teacher', 'admin']
                },
                monitoring: {
                    name: 'Surveillance',
                    icon: '👁️',
                    description: 'Dashboard temps reel, alertes et sessions',
                    url: 'http://localhost:8003',
                    tag: 'Monitoring',
                    class: 'service-monitoring',
                    roles: ['proctor', 'admin']
                },
                analytics: {
                    name: 'Analytics',
                    icon: '📊',
                    description: 'Statistiques, rapports et metriques',
                    url: 'http://localhost:8006',
                    tag: 'Dashboard',
                    class: 'service-analytics',
                    roles: ['admin']
                }
            };

            return Object.values(allServices).filter(s => s.roles.includes(role));
        }

        async function loadNotificationCount() {
            if (!currentUser) return;
            try {
                const res = await fetch('http://localhost:8005/notifications/user/' + currentUser.user_id);
                if (res.ok) {
                    const notifications = await res.json();
                    // Count recent unread (last 24h, status pending or sent)
                    const now = new Date();
                    const recentCount = notifications.filter(n => {
                        const created = new Date(n.created_at);
                        const hoursDiff = (now - created) / (1000 * 60 * 60);
                        return hoursDiff < 24;
                    }).length;

                    const badge = document.getElementById('notifBadge');
                    if (recentCount > 0) {
                        badge.textContent = recentCount > 99 ? '99+' : recentCount;
                        badge.classList.remove('hidden');
                    } else {
                        badge.classList.add('hidden');
                    }
                }
            } catch (e) {
                console.log('Could not load notifications');
            }

            // Update bell link with token
            document.getElementById('notifBellLink').href = 'http://localhost:8005?token=' + currentToken;
        }

        function logout() {
            localStorage.removeItem('token');
            currentUser = null;
            currentToken = null;
            document.getElementById('hubView').classList.add('hidden');
            document.getElementById('loginView').classList.remove('hidden');
            document.getElementById('loginForm').reset();
        }
    </script>
</body>
</html>
"""
    return _rewrite_urls(html)
