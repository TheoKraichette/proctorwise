from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from interface.api.controllers import user_controller

app = FastAPI(title="UserService", version="1.0.0")
app.include_router(user_controller.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "userservice"}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProctorWise - User Service</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 100%; max-width: 450px; }
        h1 { text-align: center; color: #333; margin-bottom: 30px; font-size: 28px; }
        .tabs { display: flex; margin-bottom: 30px; }
        .tab { flex: 1; padding: 15px; text-align: center; cursor: pointer; border: none; background: #f0f0f0; font-size: 16px; transition: all 0.3s; }
        .tab:first-child { border-radius: 10px 0 0 10px; }
        .tab:last-child { border-radius: 0 10px 10px 0; }
        .tab.active { background: #667eea; color: white; }
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
        .user-info { background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 20px; }
        .user-info h3 { margin-bottom: 15px; color: #333; }
        .user-info p { margin: 8px 0; color: #666; }
        .user-info strong { color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ProctorWise</h1>
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
                </select>
            </div>
            <button type="submit">S'inscrire</button>
        </form>

        <div id="message" class="message hidden"></div>
        <div id="userInfo" class="user-info hidden"></div>
    </div>

    <script>
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`.tab:${tab === 'login' ? 'first-child' : 'last-child'}`).classList.add('active');
            document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
            document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');
            document.getElementById('message').classList.add('hidden');
            document.getElementById('userInfo').classList.add('hidden');
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
                    localStorage.setItem('token', data.access_token);
                    showMessage('Connexion reussie!');
                    document.getElementById('userInfo').innerHTML = `
                        <h3>Bienvenue, ${data.user.name}!</h3>
                        <p><strong>Email:</strong> ${data.user.email}</p>
                        <p><strong>Role:</strong> ${data.user.role}</p>
                        <p><strong>ID:</strong> ${data.user.user_id}</p>
                    `;
                    document.getElementById('userInfo').classList.remove('hidden');
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
                    setTimeout(() => showTab('login'), 2000);
                } else {
                    showMessage(data.detail || 'Erreur d\\'inscription', true);
                }
            } catch (err) {
                showMessage('Erreur de connexion au serveur', true);
            }
        }
    </script>
</body>
</html>
"""
