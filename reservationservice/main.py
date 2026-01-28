from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from interface.api.controllers import reservation_controller

app = FastAPI(title="ReservationService", version="1.0.0")
app.include_router(reservation_controller.router)


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
        .container { max-width: 900px; margin: 0 auto; }
        h1 { text-align: center; color: white; margin-bottom: 30px; font-size: 32px; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { color: #333; margin-bottom: 20px; font-size: 20px; border-bottom: 2px solid #11998e; padding-bottom: 10px; }
        .form-row { display: flex; gap: 15px; margin-bottom: 15px; }
        .form-group { flex: 1; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input, select { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        input:focus, select:focus { outline: none; border-color: #11998e; }
        button { padding: 12px 24px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(17, 153, 142, 0.4); }
        .btn-danger { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .btn-danger:hover { box-shadow: 0 5px 20px rgba(235, 51, 73, 0.4); }
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
        .status-confirmed { background: #d4edda; color: #155724; }
        .actions { display: flex; gap: 8px; }
        .btn-small { padding: 6px 12px; font-size: 12px; }
        .search-box { display: flex; gap: 10px; margin-bottom: 15px; }
        .search-box input { flex: 1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ProctorWise - Reservations</h1>

        <div class="card">
            <h2>Nouvelle Reservation</h2>
            <form id="createForm" onsubmit="createReservation(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label for="userId">User ID</label>
                        <input type="text" id="userId" required placeholder="UUID de l'utilisateur">
                    </div>
                    <div class="form-group">
                        <label for="examId">Exam ID</label>
                        <input type="text" id="examId" required placeholder="UUID de l'examen">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="startTime">Date et Heure de debut</label>
                        <input type="datetime-local" id="startTime" required>
                    </div>
                    <div class="form-group">
                        <label for="endTime">Date et Heure de fin</label>
                        <input type="datetime-local" id="endTime" required>
                    </div>
                </div>
                <button type="submit">Creer la reservation</button>
            </form>
            <div id="createMessage" class="message hidden"></div>
        </div>

        <div class="card">
            <h2>Mes Reservations</h2>
            <div class="search-box">
                <input type="text" id="searchUserId" placeholder="Entrez votre User ID pour voir vos reservations">
                <button onclick="loadReservations()">Rechercher</button>
            </div>
            <div id="reservationsList">
                <p style="color: #666; text-align: center;">Entrez votre User ID pour voir vos reservations</p>
            </div>
            <div id="listMessage" class="message hidden"></div>
        </div>
    </div>

    <script>
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

        async function createReservation(e) {
            e.preventDefault();
            const userId = document.getElementById('userId').value;
            const examId = document.getElementById('examId').value;
            const startTime = document.getElementById('startTime').value;
            const endTime = document.getElementById('endTime').value;

            try {
                const res = await fetch('/reservations/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        exam_id: examId,
                        start_time: new Date(startTime).toISOString(),
                        end_time: new Date(endTime).toISOString()
                    })
                });
                const data = await res.json();

                if (res.ok) {
                    showMessage('createMessage', 'Reservation creee avec succes! ID: ' + data.reservation_id);
                    document.getElementById('createForm').reset();
                    if (document.getElementById('searchUserId').value === userId) {
                        loadReservations();
                    }
                } else {
                    showMessage('createMessage', data.detail || 'Erreur lors de la creation', true);
                }
            } catch (err) {
                showMessage('createMessage', 'Erreur de connexion au serveur', true);
            }
        }

        async function loadReservations() {
            const userId = document.getElementById('searchUserId').value;
            if (!userId) {
                showMessage('listMessage', 'Veuillez entrer un User ID', true);
                return;
            }

            try {
                const res = await fetch('/reservations/user/' + encodeURIComponent(userId));
                const data = await res.json();

                if (res.ok) {
                    if (data.length === 0) {
                        document.getElementById('reservationsList').innerHTML = '<p style="color: #666; text-align: center;">Aucune reservation trouvee</p>';
                    } else {
                        let html = '<table><thead><tr><th>ID</th><th>Exam ID</th><th>Debut</th><th>Fin</th><th>Statut</th><th>Actions</th></tr></thead><tbody>';
                        data.forEach(r => {
                            const statusClass = 'status-' + r.status;
                            html += '<tr>';
                            html += '<td title="' + r.reservation_id + '">' + r.reservation_id.substring(0, 8) + '...</td>';
                            html += '<td title="' + r.exam_id + '">' + r.exam_id.substring(0, 8) + '...</td>';
                            html += '<td>' + formatDateTime(r.start_time) + '</td>';
                            html += '<td>' + formatDateTime(r.end_time) + '</td>';
                            html += '<td><span class="status ' + statusClass + '">' + r.status + '</span></td>';
                            html += '<td class="actions">';
                            if (r.status === 'scheduled') {
                                html += '<button class="btn-small btn-danger" onclick="cancelReservation(\\'' + r.reservation_id + '\\')">Annuler</button>';
                            }
                            html += '</td>';
                            html += '</tr>';
                        });
                        html += '</tbody></table>';
                        document.getElementById('reservationsList').innerHTML = html;
                    }
                    document.getElementById('listMessage').classList.add('hidden');
                } else {
                    showMessage('listMessage', data.detail || 'Erreur lors du chargement', true);
                }
            } catch (err) {
                showMessage('listMessage', 'Erreur de connexion au serveur', true);
            }
        }

        async function cancelReservation(reservationId) {
            if (!confirm('Voulez-vous vraiment annuler cette reservation?')) return;

            try {
                const res = await fetch('/reservations/' + reservationId, {
                    method: 'DELETE'
                });
                const data = await res.json();

                if (res.ok) {
                    showMessage('listMessage', 'Reservation annulee avec succes');
                    document.getElementById('listMessage').classList.remove('hidden');
                    loadReservations();
                } else {
                    showMessage('listMessage', data.detail || 'Erreur lors de l\\'annulation', true);
                }
            } catch (err) {
                showMessage('listMessage', 'Erreur de connexion au serveur', true);
            }
        }
    </script>
</body>
</html>
"""
