from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from interface.api.controllers import reservation_controller
from interface.api.controllers import exam_controller
from infrastructure.database.mariadb_cluster import engine
from infrastructure.database.models import Base

app = FastAPI(title="ReservationService", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reservation_controller.router)
app.include_router(exam_controller.router)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reservationservice"}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProctorWise - Reservations</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding: 20px; background: rgba(255,255,255,0.95); border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .header h1 { color: #333; font-size: 24px; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .user-badge { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; }
        .btn-logout { padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .btn-logout:hover { background: #c82333; }
        h1 { text-align: center; color: white; margin-bottom: 30px; font-size: 32px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { color: #333; margin-bottom: 20px; font-size: 20px; border-bottom: 2px solid #11998e; padding-bottom: 10px; }
        .form-row { display: flex; gap: 15px; margin-bottom: 15px; }
        .form-group { flex: 1; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input, select, textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #11998e; }
        button { padding: 12px 24px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(17, 153, 142, 0.4); }
        .btn-danger { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .btn-danger:hover { box-shadow: 0 5px 20px rgba(235, 51, 73, 0.4); }
        .btn-secondary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .message { padding: 15px; border-radius: 8px; margin-top: 15px; text-align: center; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .hidden { display: none; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background: #f8f9fa; color: #333; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        .status { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .status-scheduled { background: #cce5ff; color: #004085; }
        .status-cancelled { background: #f8d7da; color: #721c24; }
        .status-active { background: #d4edda; color: #155724; }
        .btn-small { padding: 6px 12px; font-size: 12px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .tab.active { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .login-prompt { text-align: center; padding: 60px 20px; }
        .login-prompt h2 { color: #333; margin-bottom: 20px; }
        .login-prompt p { color: #666; margin-bottom: 30px; }
        .login-prompt a { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; font-size: 18px; }
        .login-prompt a:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(102,126,234,0.4); }
        .role-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .role-student { background: #cce5ff; color: #004085; }
        .role-teacher { background: #d4edda; color: #155724; }
        .role-proctor { background: #fff3cd; color: #856404; }
        .role-admin { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Login Required Screen -->
        <div id="loginRequired" class="card login-prompt">
            <h2>Connexion requise</h2>
            <p>Veuillez vous connecter pour acceder aux reservations d'examens.</p>
            <a href="http://localhost:8001">Se connecter</a>
        </div>

        <!-- Main App (hidden until logged in) -->
        <div id="mainApp" class="hidden">
            <div class="header">
                <h1>ProctorWise</h1>
                <div class="user-info">
                    <span id="userName"></span>
                    <span id="userRole" class="role-badge"></span>
                    <button class="btn-logout" onclick="logout()">Deconnexion</button>
                </div>
            </div>

            <!-- Student View -->
            <div id="studentView" class="hidden">
                <div class="card">
                    <h2>Reserver un examen</h2>
                    <form id="reservationForm" onsubmit="createReservation(event)">
                        <div class="form-group">
                            <label for="examSelect">Choisir un examen</label>
                            <select id="examSelect" required>
                                <option value="">-- Selectionnez un examen --</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="startTime">Date et heure</label>
                                <input type="datetime-local" id="startTime" required>
                            </div>
                        </div>
                        <button type="submit">Reserver</button>
                    </form>
                    <div id="reservationMessage" class="message hidden"></div>
                </div>

                <div class="card">
                    <h2>Mes Reservations</h2>
                    <div id="studentReservations">
                        <p style="color: #666; text-align: center;">Chargement...</p>
                    </div>
                </div>
            </div>

            <!-- Teacher View -->
            <div id="teacherView" class="hidden">
                <div class="tabs">
                    <button class="tab active" onclick="showTeacherTab('create')">Creer un examen</button>
                    <button class="tab" onclick="showTeacherTab('myexams')">Mes examens</button>
                </div>

                <div id="teacherCreateTab" class="card">
                    <h2>Creer un nouvel examen</h2>
                    <form id="examForm" onsubmit="createExam(event)">
                        <div class="form-group">
                            <label for="examTitle">Titre de l'examen</label>
                            <input type="text" id="examTitle" required placeholder="Ex: Mathematiques - Partiel 1">
                        </div>
                        <div class="form-group">
                            <label for="examDescription">Description</label>
                            <textarea id="examDescription" rows="3" placeholder="Description de l'examen..."></textarea>
                        </div>
                        <div class="form-group">
                            <label for="examDuration">Duree (minutes)</label>
                            <input type="number" id="examDuration" value="60" min="15" max="300" required>
                        </div>
                        <button type="submit">Creer l'examen</button>
                    </form>
                    <div id="examMessage" class="message hidden"></div>
                </div>

                <div id="teacherExamsTab" class="card hidden">
                    <h2>Mes examens</h2>
                    <div id="teacherExamsList">
                        <p style="color: #666; text-align: center;">Chargement...</p>
                    </div>
                </div>
            </div>

            <!-- Proctor View -->
            <div id="proctorView" class="hidden">
                <div class="card">
                    <h2>Surveillance des examens</h2>
                    <p style="color: #666; text-align: center; padding: 40px;">
                        Accedez au <a href="http://localhost:8003" style="color: #11998e;">Service de Monitoring</a> pour surveiller les examens en cours.
                    </p>
                </div>
            </div>

            <!-- Admin View -->
            <div id="adminView" class="hidden">
                <div class="card">
                    <h2>Administration</h2>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px;">
                        <a href="http://localhost:8006" style="padding: 30px; background: #f8f9fa; border-radius: 10px; text-decoration: none; text-align: center;">
                            <h3 style="color: #333; margin-bottom: 10px;">Analytics</h3>
                            <p style="color: #666;">Statistiques et rapports</p>
                        </a>
                        <a href="http://localhost:8001" style="padding: 30px; background: #f8f9fa; border-radius: 10px; text-decoration: none; text-align: center;">
                            <h3 style="color: #333; margin-bottom: 10px;">Utilisateurs</h3>
                            <p style="color: #666;">Gestion des comptes</p>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;

        // Check for token on page load
        window.onload = function() {
            // Check URL params first (from redirect)
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');

            if (token) {
                localStorage.setItem('token', token);
                // Clean URL
                window.history.replaceState({}, document.title, window.location.pathname);
            }

            const storedToken = localStorage.getItem('token');
            if (storedToken) {
                parseToken(storedToken);
            }
        };

        function parseToken(token) {
            try {
                // Decode JWT payload
                const payload = JSON.parse(atob(token.split('.')[1]));
                currentUser = {
                    user_id: payload.sub || payload.user_id,
                    name: payload.name || 'Utilisateur',
                    email: payload.email,
                    role: payload.role || 'student'
                };
                showMainApp();
            } catch (e) {
                console.error('Invalid token:', e);
                localStorage.removeItem('token');
            }
        }

        function showMainApp() {
            document.getElementById('loginRequired').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');

            document.getElementById('userName').textContent = currentUser.name;
            const roleEl = document.getElementById('userRole');
            roleEl.textContent = getRoleLabel(currentUser.role);
            roleEl.className = 'role-badge role-' + currentUser.role;

            // Show appropriate view based on role
            hideAllViews();
            switch(currentUser.role) {
                case 'teacher':
                    document.getElementById('teacherView').classList.remove('hidden');
                    loadTeacherExams();
                    break;
                case 'proctor':
                    document.getElementById('proctorView').classList.remove('hidden');
                    break;
                case 'admin':
                    document.getElementById('adminView').classList.remove('hidden');
                    break;
                default: // student
                    document.getElementById('studentView').classList.remove('hidden');
                    loadExams();
                    loadStudentReservations();
            }
        }

        function hideAllViews() {
            document.getElementById('studentView').classList.add('hidden');
            document.getElementById('teacherView').classList.add('hidden');
            document.getElementById('proctorView').classList.add('hidden');
            document.getElementById('adminView').classList.add('hidden');
        }

        function getRoleLabel(role) {
            const labels = {
                'student': 'Etudiant',
                'teacher': 'Enseignant',
                'proctor': 'Surveillant',
                'admin': 'Administrateur'
            };
            return labels[role] || role;
        }

        function logout() {
            localStorage.removeItem('token');
            currentUser = null;
            window.location.href = 'http://localhost:8001';
        }

        function showMessage(elementId, text, isError = false) {
            const msg = document.getElementById(elementId);
            msg.textContent = text;
            msg.className = 'message ' + (isError ? 'error' : 'success');
        }

        function formatDateTime(isoString) {
            if (!isoString) return '-';
            const date = new Date(isoString);
            return date.toLocaleString('fr-FR', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit'
            });
        }

        // ==================== STUDENT FUNCTIONS ====================

        async function loadExams() {
            try {
                const res = await fetch('/exams/');
                const exams = await res.json();

                const select = document.getElementById('examSelect');
                select.innerHTML = '<option value="">-- Selectionnez un examen --</option>';

                exams.forEach(exam => {
                    const option = document.createElement('option');
                    option.value = exam.exam_id;
                    option.textContent = exam.title + ' (' + exam.duration_minutes + ' min)';
                    option.dataset.duration = exam.duration_minutes;
                    select.appendChild(option);
                });
            } catch (err) {
                console.error('Error loading exams:', err);
            }
        }

        async function loadStudentReservations() {
            try {
                const res = await fetch('/reservations/user/' + currentUser.user_id);
                const reservations = await res.json();

                const container = document.getElementById('studentReservations');

                if (reservations.length === 0) {
                    container.innerHTML = '<p style="color: #666; text-align: center;">Aucune reservation</p>';
                    return;
                }

                let html = '<table><thead><tr><th>Examen</th><th>Date</th><th>Statut</th><th>Actions</th></tr></thead><tbody>';

                for (const r of reservations) {
                    const statusClass = 'status-' + r.status;
                    html += '<tr>';
                    html += '<td>' + (r.exam_id ? r.exam_id.substring(0, 8) + '...' : '-') + '</td>';
                    html += '<td>' + formatDateTime(r.start_time) + '</td>';
                    html += '<td><span class="status ' + statusClass + '">' + r.status + '</span></td>';
                    html += '<td>';
                    if (r.status === 'scheduled') {
                        html += '<button class="btn-small btn-danger" onclick="cancelReservation(\\'' + r.reservation_id + '\\')">Annuler</button>';
                    }
                    html += '</td>';
                    html += '</tr>';
                }

                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (err) {
                console.error('Error loading reservations:', err);
            }
        }

        async function createReservation(e) {
            e.preventDefault();

            const examSelect = document.getElementById('examSelect');
            const examId = examSelect.value;
            const startTime = document.getElementById('startTime').value;
            const duration = parseInt(examSelect.options[examSelect.selectedIndex].dataset.duration) || 60;

            const startDate = new Date(startTime);
            const endDate = new Date(startDate.getTime() + duration * 60000);

            try {
                const res = await fetch('/reservations/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUser.user_id,
                        exam_id: examId,
                        start_time: startDate.toISOString(),
                        end_time: endDate.toISOString()
                    })
                });

                if (res.ok) {
                    showMessage('reservationMessage', 'Reservation creee avec succes!');
                    document.getElementById('reservationForm').reset();
                    loadStudentReservations();
                } else {
                    const data = await res.json();
                    showMessage('reservationMessage', data.detail || 'Erreur', true);
                }
            } catch (err) {
                showMessage('reservationMessage', 'Erreur de connexion', true);
            }
        }

        async function cancelReservation(reservationId) {
            if (!confirm('Voulez-vous vraiment annuler cette reservation?')) return;

            try {
                const res = await fetch('/reservations/' + reservationId, { method: 'DELETE' });
                if (res.ok) {
                    loadStudentReservations();
                }
            } catch (err) {
                console.error('Error cancelling:', err);
            }
        }

        // ==================== TEACHER FUNCTIONS ====================

        function showTeacherTab(tab) {
            document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');

            document.getElementById('teacherCreateTab').classList.toggle('hidden', tab !== 'create');
            document.getElementById('teacherExamsTab').classList.toggle('hidden', tab !== 'myexams');

            if (tab === 'myexams') {
                loadTeacherExams();
            }
        }

        async function createExam(e) {
            e.preventDefault();

            const title = document.getElementById('examTitle').value;
            const description = document.getElementById('examDescription').value;
            const duration = parseInt(document.getElementById('examDuration').value);

            try {
                const res = await fetch('/exams/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: title,
                        description: description,
                        duration_minutes: duration,
                        teacher_id: currentUser.user_id
                    })
                });

                if (res.ok) {
                    showMessage('examMessage', 'Examen cree avec succes!');
                    document.getElementById('examForm').reset();
                    loadTeacherExams();
                } else {
                    const data = await res.json();
                    showMessage('examMessage', data.detail || 'Erreur', true);
                }
            } catch (err) {
                showMessage('examMessage', 'Erreur de connexion', true);
            }
        }

        async function loadTeacherExams() {
            try {
                const res = await fetch('/exams/teacher/' + currentUser.user_id);
                const exams = await res.json();

                const container = document.getElementById('teacherExamsList');

                if (exams.length === 0) {
                    container.innerHTML = '<p style="color: #666; text-align: center;">Aucun examen cree</p>';
                    return;
                }

                let html = '<table><thead><tr><th>Titre</th><th>Duree</th><th>Statut</th><th>Cree le</th><th>Actions</th></tr></thead><tbody>';

                exams.forEach(exam => {
                    html += '<tr>';
                    html += '<td>' + exam.title + '</td>';
                    html += '<td>' + exam.duration_minutes + ' min</td>';
                    html += '<td><span class="status status-' + exam.status + '">' + exam.status + '</span></td>';
                    html += '<td>' + formatDateTime(exam.created_at) + '</td>';
                    html += '<td>';
                    if (exam.status === 'active') {
                        html += '<button class="btn-small btn-danger" onclick="deleteExam(\\'' + exam.exam_id + '\\')">Supprimer</button>';
                    }
                    html += '</td>';
                    html += '</tr>';
                });

                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (err) {
                console.error('Error loading exams:', err);
            }
        }

        async function deleteExam(examId) {
            if (!confirm('Voulez-vous vraiment supprimer cet examen?')) return;

            try {
                const res = await fetch('/exams/' + examId, { method: 'DELETE' });
                if (res.ok) {
                    loadTeacherExams();
                }
            } catch (err) {
                console.error('Error deleting:', err);
            }
        }
    </script>
</body>
</html>
"""
