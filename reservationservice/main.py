from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from interface.api.controllers import reservation_controller
from interface.api.controllers import exam_controller
from interface.api.controllers import question_controller
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
app.include_router(question_controller.router)


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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); min-height: 100vh; padding-top: 70px; }

        /* Navbar */
        .navbar { position: fixed; top: 0; left: 0; right: 0; height: 60px; background: rgba(255,255,255,0.98); box-shadow: 0 2px 20px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: space-between; padding: 0 30px; z-index: 1000; }
        .navbar-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: #333; font-weight: bold; font-size: 18px; }
        .navbar-brand:hover { color: #11998e; }
        .navbar-brand .logo { font-size: 24px; }
        .navbar-nav { display: flex; align-items: center; gap: 8px; }
        .nav-link { padding: 8px 16px; border-radius: 8px; text-decoration: none; color: #555; font-size: 14px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
        .nav-link:hover { background: #f0f0f0; color: #333; }
        .nav-link.active { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .nav-link .nav-icon { font-size: 16px; }
        .navbar-user { display: flex; align-items: center; gap: 12px; }
        .user-name { font-weight: 500; color: #333; font-size: 14px; }
        .btn-logout { padding: 8px 16px; background: #e94560; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 13px; transition: background 0.2s; }
        .btn-logout:hover { background: #d63050; }
        .btn-home { padding: 8px 12px; background: #f0f0f0; color: #333; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; transition: background 0.2s; text-decoration: none; }
        .btn-home:hover { background: #e0e0e0; }

        /* Notification Bell */
        .notif-bell { position: relative; cursor: pointer; font-size: 20px; padding: 8px; border-radius: 50%; transition: background 0.2s; text-decoration: none; }
        .notif-bell:hover { background: #f0f0f0; }
        .notif-badge { position: absolute; top: 2px; right: 2px; background: #e94560; color: white; font-size: 10px; font-weight: bold; min-width: 16px; height: 16px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
        .notif-badge.hidden { display: none; }

        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        .header { display: none; } /* Hidden - replaced by navbar */
        .user-info { display: flex; align-items: center; gap: 15px; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { color: #333; margin-bottom: 20px; font-size: 20px; border-bottom: 2px solid #11998e; padding-bottom: 10px; }
        .form-row { display: flex; gap: 15px; margin-bottom: 15px; }
        .form-group { flex: 1; margin-bottom: 15px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input, select, textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #11998e; }
        button { padding: 12px 24px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(17, 153, 142, 0.4); }
        .btn-danger { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .btn-secondary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .message { padding: 15px; border-radius: 8px; margin-top: 15px; text-align: center; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .hidden { display: none; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background: #f8f9fa; color: #333; font-weight: 600; }
        .status { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .status-scheduled { background: #cce5ff; color: #004085; }
        .status-active { background: #d4edda; color: #155724; }
        .status-completed { background: #d4edda; color: #155724; }
        .status-cancelled { background: #f8d7da; color: #721c24; }
        .btn-small { padding: 6px 12px; font-size: 12px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .tab.active { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .login-prompt { text-align: center; padding: 60px 20px; }
        .login-prompt a { display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 10px; font-size: 18px; }
        .role-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .role-student { background: #cce5ff; color: #004085; }
        .role-teacher { background: #d4edda; color: #155724; }
        .role-proctor { background: #fff3cd; color: #856404; }
        .role-admin { background: #f8d7da; color: #721c24; }
        /* Exam taking styles */
        .exam-container { max-width: 800px; margin: 0 auto; }
        .exam-header { background: #667eea; color: white; padding: 20px; border-radius: 15px 15px 0 0; }
        .exam-timer { font-size: 24px; font-weight: bold; }
        .question-card { background: white; padding: 25px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .question-number { color: #667eea; font-weight: bold; margin-bottom: 10px; }
        .question-text { font-size: 18px; margin-bottom: 20px; color: #333; }
        .options { display: flex; flex-direction: column; gap: 10px; }
        .option { display: flex; align-items: center; padding: 15px; border: 2px solid #e0e0e0; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
        .option:hover { border-color: #667eea; background: #f8f9ff; }
        .option.selected { border-color: #667eea; background: #e8edff; }
        .option input { margin-right: 15px; width: 20px; height: 20px; }
        .option label { cursor: pointer; flex: 1; }
        .exam-nav { display: flex; justify-content: space-between; margin-top: 20px; }
        .progress-bar { height: 8px; background: #e0e0e0; border-radius: 4px; margin-bottom: 20px; }
        .progress-fill { height: 100%; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 4px; transition: width 0.3s; }
        .question-nav { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
        .question-nav button { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #e0e0e0; background: white; cursor: pointer; font-weight: bold; }
        .question-nav button.answered { background: #d4edda; border-color: #28a745; }
        .question-nav button.current { background: #667eea; color: white; border-color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <div id="loginRequired" class="card login-prompt">
            <h2>Connexion requise</h2>
            <p style="margin-bottom: 20px;">Veuillez vous connecter pour acceder aux examens.</p>
            <a href="http://localhost:8001">Se connecter</a>
        </div>

        <!-- Navbar -->
        <nav id="navbar" class="navbar hidden">
            <a href="#" onclick="goToHub(); return false;" class="navbar-brand">
                <span class="logo">🎓</span>
                <span>ProctorWise</span>
            </a>
            <div class="navbar-nav" id="navLinks">
                <a href="#" class="nav-link active"><span class="nav-icon">📝</span> Examens</a>
            </div>
            <div class="navbar-user">
                <span class="user-name" id="userName"></span>
                <span id="userRole" class="role-badge"></span>
                <a href="#" id="notifBellLink" class="notif-bell" title="Notifications">
                    🔔
                    <span class="notif-badge hidden" id="notifBadge">0</span>
                </a>
                <a href="#" onclick="goToHub(); return false;" class="btn-home" title="Hub">🏠</a>
                <button class="btn-logout" onclick="logout()">Deconnexion</button>
            </div>
        </nav>

        <div id="mainApp" class="hidden">

            <!-- Student View -->
            <div id="studentView" class="hidden">
                <div class="tabs">
                    <button class="tab active" onclick="showStudentTab('reserve')">Reserver</button>
                    <button class="tab" onclick="showStudentTab('reservations')">Mes Reservations</button>
                </div>

                <div id="reserveTab" class="card">
                    <h2>Reserver un examen</h2>
                    <form id="reservationForm" onsubmit="createReservation(event)">
                        <div class="form-group">
                            <label>Choisir un examen</label>
                            <select id="examSelect" required onchange="loadSlotsForExam()">
                                <option value="">-- Selectionnez --</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Creneau disponible</label>
                            <select id="slotSelect" required>
                                <option value="">-- Choisissez d'abord un examen --</option>
                            </select>
                        </div>
                        <button type="submit">Reserver</button>
                    </form>
                    <div id="reservationMessage" class="message hidden"></div>
                </div>

                <div id="reservationsTab" class="card hidden">
                    <h2>Mes Reservations</h2>
                    <div id="studentReservations"></div>
                </div>
            </div>

            <!-- Exam Taking View -->
            <div id="examView" class="hidden exam-container">
                <div class="exam-header">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 id="examTakingTitle"></h2>
                            <p id="examTakingInfo"></p>
                        </div>
                        <div class="exam-timer" id="examTimer">--:--</div>
                    </div>
                </div>
                <div class="card" style="border-radius: 0 0 15px 15px;">
                    <div class="progress-bar"><div class="progress-fill" id="progressBar"></div></div>
                    <div class="question-nav" id="questionNav"></div>
                    <div id="questionContainer"></div>
                    <div class="exam-nav">
                        <button onclick="prevQuestion()" id="prevBtn">Precedent</button>
                        <button onclick="nextQuestion()" id="nextBtn">Suivant</button>
                        <button onclick="submitExam()" id="submitBtn" class="btn-secondary hidden">Terminer l'examen</button>
                    </div>
                </div>
            </div>

            <!-- Teacher View -->
            <div id="teacherView" class="hidden">
                <div class="tabs">
                    <button class="tab active" onclick="showTeacherTab('create')">Creer examen</button>
                    <button class="tab" onclick="showTeacherTab('myexams')">Mes examens</button>
                    <button class="tab" onclick="showTeacherTab('questions')">Gerer questions</button>
                    <button class="tab" onclick="showTeacherTab('results')">Resultats</button>
                </div>

                <div id="teacherCreateTab" class="card">
                    <h2>Creer un nouvel examen</h2>
                    <form id="examForm" onsubmit="createExam(event)">
                        <div class="form-group">
                            <label>Titre</label>
                            <input type="text" id="examTitle" required placeholder="Ex: TOEIC - Session 1">
                        </div>
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="examDescription" rows="2" placeholder="Description..."></textarea>
                        </div>
                        <div class="form-group">
                            <label>Duree (minutes)</label>
                            <input type="number" id="examDuration" value="60" min="5" max="300" required>
                        </div>
                        <div class="form-group">
                            <label>Creneaux disponibles</label>
                            <div id="slotsContainer"></div>
                            <button type="button" onclick="addSlotInput()" style="margin-top:8px;padding:8px 16px;font-size:13px;">+ Ajouter un creneau</button>
                        </div>
                        <button type="submit">Creer l'examen</button>
                    </form>
                    <div id="examMessage" class="message hidden"></div>
                </div>

                <div id="teacherExamsTab" class="card hidden">
                    <h2>Mes examens</h2>
                    <div id="teacherExamsList"></div>
                    <div id="slotManager" class="hidden" style="margin-top:20px;padding-top:20px;border-top:2px solid #e0e0e0;">
                        <h3 id="slotManagerTitle" style="margin-bottom:15px;"></h3>
                        <div class="form-row" style="align-items:flex-end;">
                            <div class="form-group" style="flex:2;">
                                <label>Nouveau creneau</label>
                                <input type="datetime-local" id="newSlotTime">
                            </div>
                            <div class="form-group" style="flex:1;">
                                <button type="button" onclick="addSlotToExam()">Ajouter</button>
                            </div>
                        </div>
                        <div id="existingSlots"></div>
                        <button onclick="closeSlotManager()" class="btn-secondary" style="margin-top:10px;">Fermer</button>
                    </div>
                </div>

                <div id="teacherQuestionsTab" class="card hidden">
                    <h2>Gerer les questions</h2>
                    <div class="form-group">
                        <label>Selectionner un examen</label>
                        <select id="questionExamSelect" onchange="loadQuestionsForExam()">
                            <option value="">-- Choisir --</option>
                        </select>
                    </div>
                    <div id="questionEditor" class="hidden">
                        <h3 style="margin: 20px 0;">Ajouter une question</h3>
                        <form id="questionForm" onsubmit="addQuestion(event)">
                            <div class="form-group">
                                <label>Type</label>
                                <select id="questionType" onchange="updateQuestionForm()">
                                    <option value="mcq">QCM (4 choix)</option>
                                    <option value="true_false">Vrai/Faux</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Question</label>
                                <textarea id="questionText" rows="2" required></textarea>
                            </div>
                            <div id="mcqOptions">
                                <div class="form-row">
                                    <div class="form-group"><label>Option A</label><input type="text" id="optionA"></div>
                                    <div class="form-group"><label>Option B</label><input type="text" id="optionB"></div>
                                </div>
                                <div class="form-row">
                                    <div class="form-group"><label>Option C</label><input type="text" id="optionC"></div>
                                    <div class="form-group"><label>Option D</label><input type="text" id="optionD"></div>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Reponse correcte</label>
                                <select id="correctAnswer">
                                    <option value="A">A</option>
                                    <option value="B">B</option>
                                    <option value="C">C</option>
                                    <option value="D">D</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Points</label>
                                <input type="number" id="questionPoints" value="1" min="0.5" step="0.5">
                            </div>
                            <button type="submit">Ajouter la question</button>
                        </form>
                        <div id="questionMessage" class="message hidden"></div>
                        <h3 style="margin: 20px 0;">Questions existantes</h3>
                        <div id="existingQuestions"></div>
                    </div>
                </div>

                <div id="teacherResultsTab" class="card hidden">
                    <h2>Resultats des examens</h2>
                    <div class="form-group">
                        <label>Selectionner un examen</label>
                        <select id="resultsExamSelect" onchange="loadExamResults()">
                            <option value="">-- Choisir --</option>
                        </select>
                    </div>
                    <div id="examResultsContainer"></div>
                    <div id="submissionDetailContainer" class="hidden" style="margin-top:20px; padding-top:20px; border-top:2px solid #e0e0e0;">
                        <h3 id="submissionDetailTitle" style="margin-bottom:15px;"></h3>
                        <div id="submissionDetailContent"></div>
                        <button onclick="closeSubmissionDetail()" class="btn-secondary" style="margin-top:15px;">Fermer</button>
                    </div>
                </div>
            </div>

            <!-- Proctor View -->
            <div id="proctorView" class="hidden">
                <div class="card">
                    <h2>Surveillance des examens</h2>
                    <p style="padding: 40px; text-align: center; color: #666;">
                        <a href="#" onclick="window.location.href='http://localhost:8003?token='+localStorage.getItem('token'); return false;" style="color: #11998e;">Acceder au service de monitoring</a>
                    </p>
                </div>
            </div>

            <!-- Admin View -->
            <div id="adminView" class="hidden">
                <!-- Stats Overview -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div class="card" style="text-align: center; padding: 20px;">
                        <div style="font-size: 28px; font-weight: bold; color: #11998e;" id="adminStatExams">-</div>
                        <div style="color: #666; font-size: 13px;">Examens</div>
                    </div>
                    <div class="card" style="text-align: center; padding: 20px;">
                        <div style="font-size: 28px; font-weight: bold; color: #667eea;" id="adminStatReservations">-</div>
                        <div style="color: #666; font-size: 13px;">Reservations</div>
                    </div>
                    <div class="card" style="text-align: center; padding: 20px;">
                        <div style="font-size: 28px; font-weight: bold; color: #e74c3c;" id="adminStatQuestions">-</div>
                        <div style="color: #666; font-size: 13px;">Questions</div>
                    </div>
                </div>

                <div class="tabs">
                    <button class="tab active" onclick="showAdminTab('allExams')">Tous les examens</button>
                    <button class="tab" onclick="showAdminTab('allReservations')">Toutes les reservations</button>
                </div>

                <!-- All Exams Tab -->
                <div id="allExamsTab" class="card">
                    <h2>Tous les examens</h2>
                    <div id="adminExamsList"></div>
                </div>

                <!-- All Reservations Tab -->
                <div id="allReservationsTab" class="card hidden">
                    <h2>Toutes les reservations</h2>
                    <div id="adminReservationsList"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let examData = { questions: [], answers: {}, currentIndex: 0, examId: null, reservationId: null, duration: 0, startTime: null };
        let timerInterval = null;

        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            console.log('URL token:', token ? 'present' : 'absent');
            if (token) {
                localStorage.setItem('token', token);
                window.history.replaceState({}, document.title, window.location.pathname);
            }
            const storedToken = localStorage.getItem('token');
            console.log('Stored token:', storedToken ? 'present' : 'absent');
            if (storedToken) parseToken(storedToken);
        };

        function parseToken(token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                console.log('Token parsed, role:', payload.role);
                currentUser = { user_id: payload.sub || payload.user_id, name: payload.name || 'Utilisateur', email: payload.email, role: payload.role || 'student' };
                showMainApp();
            } catch (e) {
                console.error('Token parse error:', e);
                localStorage.removeItem('token');
            }
        }

        function showMainApp() {
            document.getElementById('loginRequired').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            document.getElementById('navbar').classList.remove('hidden');
            document.getElementById('userName').textContent = currentUser.name;
            const roleEl = document.getElementById('userRole');
            roleEl.textContent = { student: 'Etudiant', teacher: 'Enseignant', proctor: 'Surveillant', admin: 'Admin' }[currentUser.role] || currentUser.role;
            roleEl.className = 'role-badge role-' + currentUser.role;
            renderNavLinks();
            hideAllViews();
            if (currentUser.role === 'teacher') { document.getElementById('teacherView').classList.remove('hidden'); loadTeacherExams(); loadExamsForQuestionSelect(); }
            else if (currentUser.role === 'proctor') { document.getElementById('proctorView').classList.remove('hidden'); }
            else if (currentUser.role === 'admin') { document.getElementById('adminView').classList.remove('hidden'); loadAdminData(); }
            else { document.getElementById('studentView').classList.remove('hidden'); loadExams(); loadStudentReservations(); }
        }

        function renderNavLinks() {
            const nav = document.getElementById('navLinks');
            const token = localStorage.getItem('token');
            const links = [
                { name: 'Examens', icon: '📝', url: 'http://localhost:8000', active: true, roles: ['student', 'teacher', 'admin'] },
                { name: 'Monitoring', icon: '👁️', url: 'http://localhost:8003', active: false, roles: ['proctor', 'admin'] },
                { name: 'Analytics', icon: '📊', url: 'http://localhost:8006', active: false, roles: ['admin'] }
            ];
            nav.innerHTML = links
                .filter(l => l.roles.includes(currentUser.role))
                .map(l => `<a href="${l.url}?token=${token}" class="nav-link ${l.active ? 'active' : ''}"><span class="nav-icon">${l.icon}</span> ${l.name}</a>`)
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

        function hideAllViews() {
            ['studentView', 'teacherView', 'proctorView', 'adminView', 'examView'].forEach(v => document.getElementById(v).classList.add('hidden'));
        }

        function logout() { localStorage.removeItem('token'); window.location.href = 'http://localhost:8001?logout=true'; }

        function goToHub() { window.location.href = 'http://localhost:8001'; }

        function goToService(url) {
            const token = localStorage.getItem('token');
            window.location.href = url + '?token=' + token;
        }

        // ========== ADMIN FUNCTIONS ==========
        function showAdminTab(tab) {
            document.querySelectorAll('#adminView .tabs .tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('allExamsTab').classList.toggle('hidden', tab !== 'allExams');
            document.getElementById('allReservationsTab').classList.toggle('hidden', tab !== 'allReservations');
        }

        async function loadAdminData() {
            await Promise.all([loadAdminStats(), loadAllExams(), loadAllReservations()]);
        }

        async function loadAdminStats() {
            try {
                const [examsRes, reservationsRes] = await Promise.all([
                    fetch('/exams/'),
                    fetch('/reservations/all')
                ]);
                const exams = examsRes.ok ? await examsRes.json() : [];
                const reservations = reservationsRes.ok ? await reservationsRes.json() : [];

                let totalQuestions = 0;
                for (const exam of exams) {
                    try {
                        const qRes = await fetch('/exams/' + exam.exam_id + '/questions');
                        if (qRes.ok) {
                            const questions = await qRes.json();
                            totalQuestions += questions.length;
                        }
                    } catch (e) {}
                }

                document.getElementById('adminStatExams').textContent = exams.length;
                document.getElementById('adminStatReservations').textContent = reservations.length;
                document.getElementById('adminStatQuestions').textContent = totalQuestions;
            } catch (e) { console.error('Admin stats error:', e); }
        }

        async function loadAllExams() {
            const container = document.getElementById('adminExamsList');
            container.innerHTML = '<p>Chargement...</p>';
            try {
                const res = await fetch('/exams/');
                if (!res.ok) throw new Error('Erreur serveur');
                const exams = await res.json();

                if (exams.length === 0) {
                    container.innerHTML = '<p style="color:#888;">Aucun examen</p>';
                    return;
                }

                let html = '<table><thead><tr><th>Titre</th><th>Enseignant</th><th>Duree</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
                for (const exam of exams) {
                    html += '<tr>';
                    html += '<td><strong>' + exam.title + '</strong></td>';
                    html += '<td><code>' + (exam.teacher_id || '-').substring(0, 8) + '...</code></td>';
                    html += '<td>' + exam.duration_minutes + ' min</td>';
                    html += '<td><span class="status status-' + exam.status + '">' + exam.status + '</span></td>';
                    html += '<td><button class="btn-small btn-danger" onclick="deleteExam(\\'' + exam.exam_id + '\\')">Supprimer</button></td>';
                    html += '</tr>';
                }
                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (e) {
                container.innerHTML = '<p style="color:#e74c3c;">Erreur: ' + e.message + '</p>';
            }
        }

        async function loadAllReservations() {
            const container = document.getElementById('adminReservationsList');
            container.innerHTML = '<p>Chargement...</p>';
            try {
                const res = await fetch('/reservations/all');
                if (!res.ok) throw new Error('Erreur serveur');
                const reservations = await res.json();

                if (reservations.length === 0) {
                    container.innerHTML = '<p style="color:#888;">Aucune reservation</p>';
                    return;
                }

                let html = '<table><thead><tr><th>Etudiant</th><th>Examen</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
                for (const r of reservations) {
                    html += '<tr>';
                    html += '<td><code>' + (r.user_id || '-').substring(0, 8) + '...</code></td>';
                    html += '<td><code>' + (r.exam_id || '-').substring(0, 8) + '...</code></td>';
                    html += '<td>' + formatDateTime(r.start_time) + '</td>';
                    html += '<td><span class="status status-' + r.status + '">' + r.status + '</span></td>';
                    html += '<td><button class="btn-small btn-danger" onclick="cancelReservation(\\'' + r.reservation_id + '\\')">Annuler</button></td>';
                    html += '</tr>';
                }
                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (e) {
                container.innerHTML = '<p style="color:#e74c3c;">Erreur: ' + e.message + '</p>';
            }
        }

        async function deleteExam(examId) {
            if (!confirm('Supprimer cet examen ? Cette action est irreversible.')) return;
            try {
                const res = await fetch('/exams/' + examId, { method: 'DELETE' });
                if (res.ok) {
                    loadAdminData();
                } else {
                    alert('Erreur lors de la suppression');
                }
            } catch (e) { alert('Erreur: ' + e.message); }
        }

        async function cancelReservation(reservationId) {
            if (!confirm('Annuler cette reservation ?')) return;
            try {
                const res = await fetch('/reservations/' + reservationId + '/status?status=cancelled', { method: 'PATCH' });
                if (res.ok) {
                    loadAllReservations();
                } else {
                    alert("Erreur lors de l'annulation");
                }
            } catch (e) { alert('Erreur: ' + e.message); }
        }

        function showMessage(id, text, isError = false) {
            const msg = document.getElementById(id);
            msg.textContent = text;
            msg.className = 'message ' + (isError ? 'error' : 'success');
        }

        function formatDateTime(iso) {
            if (!iso) return '-';
            return new Date(iso).toLocaleString('fr-FR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
        }

        // ========== STUDENT ==========
        function showStudentTab(tab) {
            document.querySelectorAll('#studentView .tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('reserveTab').classList.toggle('hidden', tab !== 'reserve');
            document.getElementById('reservationsTab').classList.toggle('hidden', tab !== 'reservations');
            if (tab === 'reservations') loadStudentReservations();
        }

        async function loadExams() {
            const res = await fetch('/exams/');
            const exams = await res.json();
            const select = document.getElementById('examSelect');
            select.innerHTML = '<option value="">-- Selectionnez --</option>';
            for (const exam of exams) {
                const qRes = await fetch('/exams/' + exam.exam_id + '/questions');
                const questions = await qRes.json();
                const opt = document.createElement('option');
                opt.value = exam.exam_id;
                opt.textContent = exam.title + ' (' + exam.duration_minutes + ' min, ' + questions.length + ' questions)';
                opt.dataset.duration = exam.duration_minutes;
                select.appendChild(opt);
            }
        }

        async function loadStudentReservations() {
            const res = await fetch('/reservations/user/' + currentUser.user_id);
            const reservations = await res.json();
            const container = document.getElementById('studentReservations');
            if (reservations.length === 0) { container.innerHTML = '<p style="color:#666;text-align:center;">Aucune reservation</p>'; return; }
            let html = '<table><thead><tr><th>Examen</th><th>Date</th><th>Statut</th><th>Actions</th></tr></thead><tbody>';
            for (const r of reservations) {
                let examTitle = r.exam_id.substring(0, 8) + '...';
                try { const examRes = await fetch('/exams/' + r.exam_id); if (examRes.ok) { const exam = await examRes.json(); examTitle = exam.title; } } catch (e) {}
                html += '<tr><td>' + examTitle + '</td><td>' + formatDateTime(r.start_time) + '</td>';
                html += '<td><span class="status status-' + r.status + '">' + r.status + '</span></td><td>';
                if (r.status === 'scheduled') {
                    const now = new Date();
                    const start = new Date(r.start_time);
                    const end = new Date(r.end_time);
                    if (now >= start && now <= end) {
                        html += '<button class="btn-small btn-secondary" onclick="startExam(\\'' + r.exam_id + '\\', \\'' + r.reservation_id + '\\')">Passer</button> ';
                    } else if (now < start) {
                        html += '<button class="btn-small" disabled style="opacity:0.5;cursor:not-allowed;">Disponible le ' + formatDateTime(r.start_time) + '</button> ';
                    } else {
                        html += '<span style="color:#dc3545;font-size:12px;">Creneau expire</span> ';
                    }
                    html += '<button class="btn-small btn-danger" onclick="cancelReservation(\\'' + r.reservation_id + '\\')">Annuler</button>';
                }
                html += '</td></tr>';
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function loadSlotsForExam() {
            const examSelect = document.getElementById('examSelect');
            const examId = examSelect.value;
            const slotSelect = document.getElementById('slotSelect');
            slotSelect.innerHTML = '<option value="">-- Selectionnez un creneau --</option>';
            if (!examId) { slotSelect.innerHTML = '<option value="">-- Choisissez d abord un examen --</option>'; return; }
            const res = await fetch('/exams/' + examId + '/slots');
            const slots = await res.json();
            if (slots.length === 0) {
                slotSelect.innerHTML = '<option value="">Aucun creneau disponible</option>';
                return;
            }
            slots.forEach(slot => {
                const opt = document.createElement('option');
                opt.value = slot.start_time;
                opt.textContent = formatDateTime(slot.start_time);
                slotSelect.appendChild(opt);
            });
        }

        async function createReservation(e) {
            e.preventDefault();
            const examSelect = document.getElementById('examSelect');
            const examId = examSelect.value;
            const slotSelect = document.getElementById('slotSelect');
            const selectedSlot = slotSelect.value;
            if (!selectedSlot) { showMessage('reservationMessage', 'Veuillez selectionner un creneau', true); return; }
            const duration = parseInt(examSelect.options[examSelect.selectedIndex].dataset.duration) || 60;
            const startDate = new Date(selectedSlot);
            const endDate = new Date(startDate.getTime() + duration * 60000);
            const res = await fetch('/reservations/', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.user_id, exam_id: examId, start_time: startDate.toISOString(), end_time: endDate.toISOString() })
            });
            if (res.ok) { showMessage('reservationMessage', 'Reservation creee!'); document.getElementById('reservationForm').reset(); loadStudentReservations(); }
            else { const data = await res.json(); showMessage('reservationMessage', data.detail || 'Erreur', true); }
        }

        async function cancelReservation(id) {
            if (!confirm('Annuler cette reservation?')) return;
            await fetch('/reservations/' + id, { method: 'DELETE' });
            loadStudentReservations();
        }

        // ========== EXAM TAKING ==========
        async function startExam(examId, reservationId) {
            const examRes = await fetch('/exams/' + examId);
            const exam = await examRes.json();
            const questionsRes = await fetch('/exams/' + examId + '/questions');
            const questions = await questionsRes.json();
            if (questions.length === 0) { alert("Cet examen n'a pas encore de questions."); return; }
            examData = { questions, answers: {}, currentIndex: 0, examId, reservationId, duration: exam.duration_minutes, startTime: Date.now(), title: exam.title };
            hideAllViews();
            document.getElementById('examView').classList.remove('hidden');
            document.getElementById('examTakingTitle').textContent = exam.title;
            document.getElementById('examTakingInfo').textContent = questions.length + ' questions - ' + exam.duration_minutes + ' minutes';
            buildQuestionNav();
            renderQuestion();
            startTimer();
        }

        function buildQuestionNav() {
            const nav = document.getElementById('questionNav');
            nav.innerHTML = '';
            examData.questions.forEach((q, i) => {
                const btn = document.createElement('button');
                btn.textContent = i + 1;
                btn.onclick = () => goToQuestion(i);
                nav.appendChild(btn);
            });
            updateQuestionNav();
        }

        function updateQuestionNav() {
            const buttons = document.querySelectorAll('#questionNav button');
            buttons.forEach((btn, i) => {
                btn.classList.remove('current', 'answered');
                if (i === examData.currentIndex) btn.classList.add('current');
                if (examData.answers[examData.questions[i].question_id]) btn.classList.add('answered');
            });
            const progress = Object.keys(examData.answers).length / examData.questions.length * 100;
            document.getElementById('progressBar').style.width = progress + '%';
        }

        function goToQuestion(index) { examData.currentIndex = index; renderQuestion(); }

        function renderQuestion() {
            const q = examData.questions[examData.currentIndex];
            const container = document.getElementById('questionContainer');
            let html = '<div class="question-card">';
            html += '<div class="question-number">Question ' + (examData.currentIndex + 1) + ' / ' + examData.questions.length + ' (' + q.points + ' pt)</div>';
            html += '<div class="question-text">' + q.question_text + '</div>';
            html += '<div class="options">';
            const options = q.question_type === 'true_false' ? [{ key: 'True', text: 'Vrai' }, { key: 'False', text: 'Faux' }] :
                [{ key: 'A', text: q.option_a }, { key: 'B', text: q.option_b }, { key: 'C', text: q.option_c }, { key: 'D', text: q.option_d }];
            const currentAnswer = examData.answers[q.question_id] || '';
            options.forEach(opt => {
                if (!opt.text) return;
                const selected = currentAnswer === opt.key ? 'selected' : '';
                html += '<div class="option ' + selected + '" onclick="selectAnswer(\\'' + q.question_id + '\\', \\'' + opt.key + '\\')">';
                html += '<input type="radio" name="q' + q.question_id + '" ' + (selected ? 'checked' : '') + '>';
                html += '<label><strong>' + opt.key + '.</strong> ' + opt.text + '</label></div>';
            });
            html += '</div></div>';
            container.innerHTML = html;
            document.getElementById('prevBtn').disabled = examData.currentIndex === 0;
            document.getElementById('nextBtn').classList.toggle('hidden', examData.currentIndex === examData.questions.length - 1);
            document.getElementById('submitBtn').classList.toggle('hidden', examData.currentIndex !== examData.questions.length - 1);
            updateQuestionNav();
        }

        function selectAnswer(questionId, answer) {
            examData.answers[questionId] = answer;
            renderQuestion();
        }

        function prevQuestion() { if (examData.currentIndex > 0) { examData.currentIndex--; renderQuestion(); } }
        function nextQuestion() { if (examData.currentIndex < examData.questions.length - 1) { examData.currentIndex++; renderQuestion(); } }

        function startTimer() {
            if (timerInterval) clearInterval(timerInterval);
            const timerEl = document.getElementById('examTimer');
            const endTime = examData.startTime + examData.duration * 60000;
            timerInterval = setInterval(() => {
                const remaining = Math.max(0, endTime - Date.now());
                const mins = Math.floor(remaining / 60000);
                const secs = Math.floor((remaining % 60000) / 1000);
                timerEl.textContent = mins.toString().padStart(2, '0') + ':' + secs.toString().padStart(2, '0');
                if (remaining <= 0) { clearInterval(timerInterval); timerInterval = null; submitExam(true); }
            }, 1000);
        }

        async function submitExam(autoSubmit = false) {
            if (!autoSubmit && !confirm("Terminer et soumettre l'examen?")) return;
            // Stop timer
            if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
            // Fetch correct answers for grading
            const correctRes = await fetch('/exams/' + examData.examId + '/questions/with-answers');
            const questionsWithAnswers = await correctRes.json();
            const correctMap = {};
            questionsWithAnswers.forEach(q => { correctMap[q.question_id] = q.correct_answer; });
            const answers = examData.questions.map(q => ({
                question_id: q.question_id,
                question_type: q.question_type,
                user_answer: examData.answers[q.question_id] || '',
                correct_answer: correctMap[q.question_id],
                max_score: q.points
            }));
            let submissionSuccess = false;
            try {
                const res = await fetch('http://localhost:8004/corrections/submissions', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: currentUser.user_id, exam_id: examData.examId, reservation_id: examData.reservationId, answers })
                });
                if (res.ok) {
                    const submission = await res.json();
                    // Auto-grade
                    await fetch('http://localhost:8004/corrections/submissions/' + submission.submission_id + '/grade', { method: 'POST' });
                    submissionSuccess = true;
                    // Mark reservation as completed
                    await fetch('/reservations/' + examData.reservationId + '/status?status=completed', { method: 'PATCH' });
                }
            } catch (e) { console.error('Submission error:', e); }
            hideAllViews();
            document.getElementById('studentView').classList.remove('hidden');
            // Show confirmation message
            const container = document.getElementById('studentReservations');
            if (submissionSuccess) {
                container.innerHTML = '<div class="message success" style="margin-bottom:20px;">Examen soumis avec succes! Votre copie a ete transmise pour correction.</div>';
            } else {
                container.innerHTML = '<div class="message error" style="margin-bottom:20px;">Erreur lors de la soumission. Veuillez contacter un administrateur.</div>';
            }
            setTimeout(() => loadStudentReservations(), 3000);
        }

        // ========== TEACHER ==========
        function showTeacherTab(tab) {
            document.querySelectorAll('#teacherView .tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('teacherCreateTab').classList.toggle('hidden', tab !== 'create');
            document.getElementById('teacherExamsTab').classList.toggle('hidden', tab !== 'myexams');
            document.getElementById('teacherQuestionsTab').classList.toggle('hidden', tab !== 'questions');
            document.getElementById('teacherResultsTab').classList.toggle('hidden', tab !== 'results');
            if (tab === 'myexams') loadTeacherExams();
            if (tab === 'results') loadExamsForResultsSelect();
        }

        function addSlotInput() {
            const container = document.getElementById('slotsContainer');
            const div = document.createElement('div');
            div.style.cssText = 'display:flex;gap:10px;align-items:center;margin-bottom:8px;';
            div.innerHTML = '<input type="datetime-local" class="slot-input" style="flex:1;" required>' +
                '<button type="button" onclick="this.parentElement.remove()" style="padding:8px 12px;font-size:13px;" class="btn-danger">X</button>';
            container.appendChild(div);
        }

        async function createExam(e) {
            e.preventDefault();
            const slotInputs = document.querySelectorAll('#slotsContainer .slot-input');
            const slotTimes = [];
            for (const input of slotInputs) {
                if (input.value) slotTimes.push(input.value);
            }
            const res = await fetch('/exams/', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: document.getElementById('examTitle').value,
                    description: document.getElementById('examDescription').value,
                    duration_minutes: parseInt(document.getElementById('examDuration').value),
                    teacher_id: currentUser.user_id
                })
            });
            if (res.ok) {
                const exam = await res.json();
                // Create slots
                for (const st of slotTimes) {
                    await fetch('/exams/' + exam.exam_id + '/slots', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ start_time: new Date(st).toISOString() })
                    });
                }
                const slotMsg = slotTimes.length > 0 ? ' avec ' + slotTimes.length + ' creneau(x)' : '';
                showMessage('examMessage', 'Examen cree!' + slotMsg);
                document.getElementById('examForm').reset();
                document.getElementById('slotsContainer').innerHTML = '';
                loadTeacherExams(); loadExamsForQuestionSelect();
            }
            else showMessage('examMessage', 'Erreur', true);
        }

        async function loadTeacherExams() {
            const res = await fetch('/exams/teacher/' + currentUser.user_id);
            const exams = await res.json();
            const container = document.getElementById('teacherExamsList');
            if (exams.length === 0) { container.innerHTML = '<p style="color:#666;text-align:center;">Aucun examen</p>'; return; }
            let html = '<table><thead><tr><th>Titre</th><th>Duree</th><th>Questions</th><th>Creneaux</th><th>Actions</th></tr></thead><tbody>';
            for (const exam of exams) {
                const qRes = await fetch('/exams/' + exam.exam_id + '/questions');
                const questions = await qRes.json();
                const sRes = await fetch('/exams/' + exam.exam_id + '/slots');
                const slots = await sRes.json();
                html += '<tr><td>' + exam.title + '</td><td>' + exam.duration_minutes + ' min</td>';
                html += '<td>' + questions.length + '</td>';
                html += '<td>' + slots.length + '</td>';
                html += '<td><button class="btn-small btn-secondary" onclick="openSlotManager(\\'' + exam.exam_id + '\\', \\'' + exam.title.replace(/'/g, "\\\\'") + '\\')">Creneaux</button> ';
                html += '<button class="btn-small btn-danger" onclick="deleteExam(\\'' + exam.exam_id + '\\')">Supprimer</button></td></tr>';
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function deleteExam(id) {
            if (!confirm('Supprimer cet examen?')) return;
            await fetch('/exams/' + id, { method: 'DELETE' });
            loadTeacherExams();
            loadExamsForQuestionSelect();
        }

        let slotManagerExamId = null;

        async function openSlotManager(examId, examTitle) {
            slotManagerExamId = examId;
            document.getElementById('slotManagerTitle').textContent = 'Creneaux - ' + examTitle;
            document.getElementById('slotManager').classList.remove('hidden');
            document.getElementById('newSlotTime').value = '';
            await loadExistingSlots();
        }

        function closeSlotManager() {
            document.getElementById('slotManager').classList.add('hidden');
            slotManagerExamId = null;
            loadTeacherExams();
        }

        async function loadExistingSlots() {
            if (!slotManagerExamId) return;
            const res = await fetch('/exams/' + slotManagerExamId + '/slots');
            const slots = await res.json();
            const container = document.getElementById('existingSlots');
            if (slots.length === 0) { container.innerHTML = '<p style="color:#666;">Aucun creneau</p>'; return; }
            let html = '<table><thead><tr><th>Date et heure</th><th>Actions</th></tr></thead><tbody>';
            slots.forEach(s => {
                html += '<tr><td>' + formatDateTime(s.start_time) + '</td>';
                html += '<td><button class="btn-small btn-danger" onclick="removeSlot(\\'' + s.slot_id + '\\')">Supprimer</button></td></tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function addSlotToExam() {
            const timeInput = document.getElementById('newSlotTime');
            if (!timeInput.value) { alert('Veuillez choisir une date et heure'); return; }
            await fetch('/exams/' + slotManagerExamId + '/slots', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start_time: new Date(timeInput.value).toISOString() })
            });
            timeInput.value = '';
            loadExistingSlots();
        }

        async function removeSlot(slotId) {
            if (!confirm('Supprimer ce creneau?')) return;
            await fetch('/exams/' + slotManagerExamId + '/slots/' + slotId, { method: 'DELETE' });
            loadExistingSlots();
        }

        async function loadExamsForQuestionSelect() {
            const res = await fetch('/exams/teacher/' + currentUser.user_id);
            const exams = await res.json();
            const select = document.getElementById('questionExamSelect');
            select.innerHTML = '<option value="">-- Choisir --</option>';
            exams.forEach(exam => {
                const opt = document.createElement('option');
                opt.value = exam.exam_id;
                opt.textContent = exam.title;
                select.appendChild(opt);
            });
        }

        async function loadQuestionsForExam() {
            const examId = document.getElementById('questionExamSelect').value;
            if (!examId) { document.getElementById('questionEditor').classList.add('hidden'); return; }
            document.getElementById('questionEditor').classList.remove('hidden');
            document.getElementById('questionEditor').dataset.examId = examId;
            const res = await fetch('/exams/' + examId + '/questions/with-answers');
            const questions = await res.json();
            const container = document.getElementById('existingQuestions');
            if (!Array.isArray(questions) || questions.length === 0) { container.innerHTML = '<p style="color:#666;">Aucune question</p>'; return; }
            let html = '<table><thead><tr><th>#</th><th>Question</th><th>Type</th><th>Reponse</th><th>Actions</th></tr></thead><tbody>';
            questions.forEach(q => {
                html += '<tr><td>' + q.question_number + '</td><td>' + q.question_text.substring(0, 50) + '...</td>';
                html += '<td>' + q.question_type + '</td><td>' + q.correct_answer + '</td>';
                html += '<td><button class="btn-small btn-danger" onclick="deleteQuestion(\\'' + q.question_id + '\\')">X</button></td></tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function updateQuestionForm() {
            const type = document.getElementById('questionType').value;
            const isMcq = type !== 'true_false';
            document.getElementById('mcqOptions').classList.toggle('hidden', !isMcq);
            ['optionA', 'optionB', 'optionC', 'optionD'].forEach(id => {
                document.getElementById(id).required = isMcq;
            });
            const correctSelect = document.getElementById('correctAnswer');
            if (type === 'true_false') {
                correctSelect.innerHTML = '<option value="True">Vrai</option><option value="False">Faux</option>';
            } else {
                correctSelect.innerHTML = '<option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option>';
            }
        }

        async function addQuestion(e) {
            e.preventDefault();
            const examId = document.getElementById('questionEditor').dataset.examId;
            const type = document.getElementById('questionType').value;
            const body = {
                question_type: type,
                question_text: document.getElementById('questionText').value,
                correct_answer: document.getElementById('correctAnswer').value,
                points: parseFloat(document.getElementById('questionPoints').value)
            };
            if (type === 'mcq') {
                body.option_a = document.getElementById('optionA').value;
                body.option_b = document.getElementById('optionB').value;
                body.option_c = document.getElementById('optionC').value;
                body.option_d = document.getElementById('optionD').value;
            } else {
                body.option_a = 'Vrai';
                body.option_b = 'Faux';
            }
            const res = await fetch('/exams/' + examId + '/questions/', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (res.ok) { showMessage('questionMessage', 'Question ajoutee!'); document.getElementById('questionForm').reset(); loadQuestionsForExam(); }
            else showMessage('questionMessage', 'Erreur', true);
        }

        async function deleteQuestion(id) {
            const examId = document.getElementById('questionEditor').dataset.examId;
            await fetch('/exams/' + examId + '/questions/' + id, { method: 'DELETE' });
            loadQuestionsForExam();
        }

        async function loadExamsForResultsSelect() {
            const res = await fetch('/exams/teacher/' + currentUser.user_id);
            const exams = await res.json();
            const select = document.getElementById('resultsExamSelect');
            select.innerHTML = '<option value="">-- Choisir --</option>';
            exams.forEach(exam => {
                const opt = document.createElement('option');
                opt.value = exam.exam_id;
                opt.textContent = exam.title;
                select.appendChild(opt);
            });
        }

        async function loadExamResults() {
            const examId = document.getElementById('resultsExamSelect').value;
            const container = document.getElementById('examResultsContainer');
            document.getElementById('submissionDetailContainer').classList.add('hidden');
            if (!examId) { container.innerHTML = ''; return; }
            try {
                const res = await fetch('http://localhost:8004/corrections/submissions/exam/' + examId);
                if (!res.ok) { container.innerHTML = '<p style="color:#666;text-align:center;">Erreur lors du chargement</p>'; return; }
                const submissions = await res.json();
                if (submissions.length === 0) { container.innerHTML = '<p style="color:#666;text-align:center;">Aucune soumission pour cet examen</p>'; return; }
                let html = '<table><thead><tr><th>Etudiant</th><th>Date</th><th>Score</th><th>Pourcentage</th><th>Statut</th><th>Actions</th></tr></thead><tbody>';
                for (const sub of submissions) {
                    let studentName = sub.user_id.substring(0, 8) + '...';
                    try {
                        const userRes = await fetch('http://localhost:8001/users/' + sub.user_id);
                        if (userRes.ok) { const user = await userRes.json(); studentName = user.name || user.email; }
                    } catch (e) {}
                    const percentage = sub.percentage ? sub.percentage.toFixed(1) + '%' : '-';
                    const score = sub.total_score !== null ? sub.total_score + '/' + sub.max_score : '-';
                    const statusClass = sub.status === 'graded' ? 'status-completed' : 'status-scheduled';
                    html += '<tr><td>' + studentName + '</td>';
                    html += '<td>' + formatDateTime(sub.submitted_at) + '</td>';
                    html += '<td>' + score + '</td>';
                    html += '<td><strong>' + percentage + '</strong></td>';
                    html += '<td><span class="status ' + statusClass + '">' + sub.status + '</span></td>';
                    html += '<td><button class="btn-small btn-secondary" onclick="viewSubmissionDetail(\\'' + sub.submission_id + '\\', \\'' + studentName.replace(/'/g, "\\\\'") + '\\')">Details</button></td></tr>';
                }
                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (e) { container.innerHTML = '<p style="color:#666;text-align:center;">Erreur: ' + e.message + '</p>'; }
        }

        async function viewSubmissionDetail(submissionId, studentName) {
            const container = document.getElementById('submissionDetailContainer');
            const content = document.getElementById('submissionDetailContent');
            document.getElementById('submissionDetailTitle').textContent = 'Copie de ' + studentName;
            content.innerHTML = '<p>Chargement...</p>';
            container.classList.remove('hidden');
            try {
                const res = await fetch('http://localhost:8004/corrections/submissions/' + submissionId + '/result');
                if (!res.ok) { content.innerHTML = '<p style="color:red;">Erreur lors du chargement</p>'; return; }
                const result = await res.json();
                let html = '<div style="margin-bottom:15px;padding:15px;background:#f8f9fa;border-radius:10px;">';
                html += '<strong>Score total:</strong> ' + (result.submission.total_score || 0) + '/' + (result.submission.max_score || 0);
                html += ' (<strong>' + (result.submission.percentage || 0).toFixed(1) + '%</strong>)</div>';
                html += '<table><thead><tr><th>#</th><th>Question</th><th>Reponse</th><th>Correcte</th><th>Points</th></tr></thead><tbody>';
                const examId = document.getElementById('resultsExamSelect').value;
                const questionsRes = await fetch('/exams/' + examId + '/questions/with-answers');
                const questions = await questionsRes.json();
                const questionMap = {};
                if (Array.isArray(questions)) {
                    questions.forEach((q, i) => { questionMap[q.question_id] = { text: q.question_text, number: i + 1 }; });
                }
                const answers = Array.isArray(result.answers) ? result.answers : [];
                for (const ans of answers) {
                    const qInfo = questionMap[ans.question_id] || { text: 'Question inconnue', number: '?' };
                    const isCorrect = ans.is_correct;
                    const icon = isCorrect ? '✓' : '✗';
                    const color = isCorrect ? '#28a745' : '#dc3545';
                    html += '<tr>';
                    html += '<td>' + qInfo.number + '</td>';
                    html += '<td style="max-width:300px;">' + qInfo.text.substring(0, 80) + (qInfo.text.length > 80 ? '...' : '') + '</td>';
                    html += '<td><span style="color:' + color + ';">' + (ans.user_answer || '-') + '</span> ';
                    if (!isCorrect) html += '<small style="color:#666;">(correct: ' + ans.correct_answer + ')</small>';
                    html += '</td>';
                    html += '<td style="color:' + color + ';font-size:18px;">' + icon + '</td>';
                    html += '<td>' + (ans.score || 0) + '/' + (ans.max_score || 0) + '</td>';
                    html += '</tr>';
                }
                html += '</tbody></table>';
                content.innerHTML = html;
            } catch (e) { content.innerHTML = '<p style="color:red;">Erreur: ' + e.message + '</p>'; }
        }

        function closeSubmissionDetail() {
            document.getElementById('submissionDetailContainer').classList.add('hidden');
        }
    </script>
</body>
</html>
"""
