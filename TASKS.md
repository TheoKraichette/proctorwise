# ProctorWise - Taches Detaillees

**Date**: 28 Janvier 2026
**Deadline**: 29 Janvier soir
**Equipe**: 2 personnes (Dev A & Dev B)

---

## Etat Global du Projet

| Composant | Status | Completude |
|-----------|--------|------------|
| Infrastructure Docker | OK | 100% |
| UserService | Backend OK, UI OK, Roles OK | 90% |
| ReservationService | Backend OK, UI OK, Exams OK | 90% |
| MonitoringService | Backend OK, ML OK, UI manquante | 85% |
| CorrectionService | Backend OK, UI manquante | 90% |
| NotificationService | Backend OK, UI manquante | 85% |
| AnalyticsService | Backend OK, UI manquante | 80% |
| Spark Jobs | Code OK, non teste | 90% |
| Airflow DAGs | OK, actifs | 95% |
| ML (YOLO/MediaPipe) | Implemente | 80% |

---

## Roles Utilisateurs

4 roles implementes selon le diagramme use case:

| Role | Use Cases |
|------|-----------|
| **Etudiant** | Reserver creneau, Consulter resultats, Passer examen |
| **Enseignant** | Creer examen, Consulter copies, Corriger copie |
| **Surveillant** | Recevoir alertes anomalies, Surveiller temps reel |
| **Administrateur** | Acceder statistiques, Gerer utilisateurs et roles |

---

## 1. USERSERVICE (Port 8001)

### Etat Actuel
- **Endpoints implementes**:
  - `POST /users/register` - Inscription avec bcrypt + role
  - `POST /users/login` - Connexion JWT (24h) avec redirection vers ReservationService
  - `GET /users/{user_id}` - Details utilisateur
  - `GET /` - Interface web login/register avec selection de role
- **JWT contient**: user_id, name, email, role, exp
- **Roles**: student, teacher, proctor, admin
- **Interface Web**: OK (login + register + selection role + redirection auto)

### Taches a Faire

| ID | Tache | Priorite | Temps | Fichiers |
|----|-------|----------|-------|----------|
| U1 | Endpoint PUT /users/{user_id} (modifier profil) | Moyenne | 30min | `user_controller.py`, `update_user.py` |
| U2 | Endpoint DELETE /users/{user_id} (desactiver compte) | Basse | 20min | `user_controller.py` |
| U3 | Endpoint GET /users/ (liste users pour admin) | Moyenne | 30min | `user_controller.py`, `list_users.py` |
| U4 | Middleware JWT verification | HAUTE | 1h | Creer `common/auth.py` |
| U5 | Validation force mot de passe (min 8 chars) | Moyenne | 20min | `register_user.py` |

### Bugs Connus
- Aucun

---

## 2. RESERVATIONSERVICE (Port 8000)

### Etat Actuel
- **Endpoints Reservations**:
  - `POST /reservations/` - Creer reservation + event Kafka
  - `DELETE /reservations/{reservation_id}` - Annuler
  - `GET /reservations/user/{user_id}` - Liste par user
  - `GET /reservations/{reservation_id}` - Details
- **Endpoints Examens** (NOUVEAU):
  - `POST /exams/` - Creer un examen (enseignant)
  - `GET /exams/` - Lister tous les examens actifs
  - `GET /exams/{exam_id}` - Details examen
  - `GET /exams/teacher/{teacher_id}` - Examens d'un enseignant
  - `PUT /exams/{exam_id}` - Modifier examen
  - `DELETE /exams/{exam_id}` - Supprimer examen (soft delete)
- **Kafka Events**: `exam_scheduled`, `exam_cancelled`
- **Interface Web**: OK avec vues par role:
  - **Etudiant**: Dropdown examens, reservation, liste reservations
  - **Enseignant**: Creer examen, voir ses examens
  - **Surveillant**: Lien vers MonitoringService
  - **Admin**: Liens vers Analytics et gestion utilisateurs
- **Auth**: Verifie JWT au chargement, user_id auto depuis token

### Taches a Faire

| ID | Tache | Priorite | Temps | Fichiers |
|----|-------|----------|-------|----------|
| R1 | Validation start_time < end_time | HAUTE | 15min | `reservation_request.py` |
| R2 | Detection conflits horaires (meme user, meme creneau) | HAUTE | 45min | `create_reservation.py` |
| R3 | Proteger endpoints avec JWT cote serveur | HAUTE | 30min | `main.py` |
| R4 | Afficher nom examen au lieu de ID dans reservations | Moyenne | 30min | `main.py` (JS) |

### Bugs Connus
- Pas de validation des dates cote serveur

---

## 3. MONITORINGSERVICE (Port 8003)

### Etat Actuel
- **Endpoints implementes**:
  - `POST /monitoring/sessions` - Demarrer session
  - `POST /monitoring/sessions/{session_id}/frame` - Traiter frame (base64)
  - `PUT /monitoring/sessions/{session_id}/stop` - Arreter
  - `GET /monitoring/sessions/{session_id}` - Details session
  - `GET /monitoring/sessions/{session_id}/anomalies` - Liste anomalies
  - `GET /monitoring/sessions/{session_id}/anomalies/summary` - Stats
  - `WebSocket /monitoring/sessions/{session_id}/stream` - Streaming temps reel
- **ML Detecteurs**:
  - MediaPipe Face Detection (visages)
  - YOLO Object Detection (objets interdits: phone, book, laptop)
  - HybridDetector (combine les deux)
- **Anomalies detectees**:
  - `face_absent` (>5s sans visage) - high
  - `multiple_faces` (plusieurs visages) - critical
  - `forbidden_object` (telephone, livre, laptop) - high
  - `tab_change` (changement onglet) - medium
  - `webcam_disabled` - critical
- **Kafka Events**: `monitoring_started`, `monitoring_stopped`, `anomaly_detected`, `high_risk_alert`
- **Stockage**: HDFS + fallback local
- **Interface Web**: MANQUANTE

### Taches a Faire

| ID | Tache | Priorite | Temps | Fichiers |
|----|-------|----------|-------|----------|
| M1 | Interface Web dashboard monitoring (surveillant) | HAUTE | 2h | `main.py` |
| M2 | Proteger endpoints avec JWT | HAUTE | 30min | `main.py` |
| M3 | Rate limiting sur /frame (max 30 fps) | Moyenne | 30min | `monitoring_controller.py` |
| M4 | Endpoint GET /monitoring/sessions (liste toutes sessions) | Moyenne | 20min | `monitoring_controller.py` |

### Bugs Connus
- `_face_absent_start` ne persiste pas entre requetes
- Modeles YOLO telecharges au premier lancement (peut etre lent)

---

## 4. CORRECTIONSERVICE (Port 8004)

### Etat Actuel
- **Endpoints implementes**:
  - `POST /corrections/submissions` - Soumettre examen
  - `POST /corrections/submissions/{submission_id}/grade` - Correction auto MCQ
  - `PUT /corrections/submissions/{submission_id}/answers/{answer_id}` - Correction manuelle
  - `GET /corrections/submissions/{submission_id}/result` - Resultats complets
  - `GET /corrections/submissions/user/{user_id}` - Soumissions par user
  - `GET /corrections/submissions/exam/{exam_id}` - Soumissions par exam
- **Auto-grading**:
  - MCQ (choix multiples)
  - True/False
  - Short answer (fuzzy matching 85%)
  - Fill-in-blank
  - Multiple select (credit partiel)
- **Kafka Events**: `exam_submitted`, `grading_completed`, `manual_review_required`
- **Interface Web**: MANQUANTE

### Taches a Faire

| ID | Tache | Priorite | Temps | Fichiers |
|----|-------|----------|-------|----------|
| C1 | Interface Web correction (enseignant) | HAUTE | 2h | `main.py` |
| C2 | Interface consultation resultats (etudiant) | HAUTE | 1h | `main.py` |
| C3 | Proteger endpoints avec JWT | HAUTE | 30min | `main.py` |
| C4 | Export resultats CSV/PDF | Moyenne | 1h | Nouveau use case |

### Bugs Connus
- Threshold fuzzy match hardcode a 85%

---

## 5. NOTIFICATIONSERVICE (Port 8005)

### Etat Actuel
- **Endpoints implementes**:
  - `POST /notifications/` - Envoyer notification
  - `GET /notifications/user/{user_id}` - Historique (limit 50)
  - `GET /notifications/preferences/{user_id}` - Preferences
  - `PUT /notifications/preferences/{user_id}` - Modifier preferences
  - `WebSocket /notifications/ws/{user_id}` - Notifications temps reel
- **Canaux**:
  - Email (SMTP async avec aiosmtplib)
  - WebSocket (temps reel)
  - Mock senders pour dev
- **Kafka Consumer**: Ecoute `exam_scheduled`, `anomaly_detected`, `grading_completed`, `high_risk_alert`
- **Interface Web**: MANQUANTE

### Taches a Faire

| ID | Tache | Priorite | Temps | Fichiers |
|----|-------|----------|-------|----------|
| N1 | Interface Web notifications | Moyenne | 1h30 | `main.py` |
| N2 | Proteger endpoints avec JWT | HAUTE | 30min | `main.py` |
| N3 | Mark notification as read | Moyenne | 30min | `notification_controller.py` |

### Bugs Connus
- WebSocketManager stocke 1 seul websocket par user_id

---

## 6. ANALYTICSSERVICE (Port 8006)

### Etat Actuel
- **Endpoints implementes**:
  - `GET /analytics/exams/{exam_id}` - Stats examen
  - `GET /analytics/exams/{exam_id}/report/pdf` - Rapport PDF
  - `GET /analytics/exams/{exam_id}/report/csv` - Export CSV
  - `GET /analytics/users/{user_id}` - Stats utilisateur
  - `GET /analytics/users/{user_id}/report/pdf` - Rapport PDF
  - `GET /analytics/users/{user_id}/report/csv` - Export CSV
  - `GET /analytics/platform` - Metriques plateforme
  - `GET /analytics/dashboards/admin` - Dashboard admin
- **Cache**: In-memory avec TTL
- **Interface Web**: MANQUANTE

### Taches a Faire

| ID | Tache | Priorite | Temps | Fichiers |
|----|-------|----------|-------|----------|
| A1 | Interface Web dashboard admin | HAUTE | 2h | `main.py` |
| A2 | Proteger endpoints avec JWT (role admin) | HAUTE | 30min | `main.py` |
| A3 | Filtres par date sur analytics | Moyenne | 45min | `analytics_controller.py` |

---

## 7. SPARK JOBS

### Etat Actuel
Les 3 jobs sont implementes et corriges (URLs DB, credentials).

#### daily_anomaly_aggregation.py
- **Schedule**: Tous les jours a 2h
- **Input**: Table `anomalies` + `monitoring_sessions` (proctorwise_monitoring)
- **Output**: HDFS `/proctorwise/processed/anomaly_reports/{year}/{month}/`

#### weekly_grade_analytics.py
- **Schedule**: Dimanche a 3h
- **Input**: Tables `exam_submissions`, `answers` (proctorwise_corrections)
- **Output**: HDFS `/proctorwise/processed/grading_results/{year}/week_{num}/`

#### monthly_user_performance.py
- **Schedule**: 1er du mois a 5h
- **Input**: Tables `exam_submissions`, `anomalies`
- **Output**: HDFS `/proctorwise/processed/user_performance/{year}/{month}/`

### Taches a Faire

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| S1 | Tester daily_anomaly_aggregation avec donnees reelles | HAUTE | 30min |
| S2 | Tester weekly_grade_analytics avec donnees reelles | HAUTE | 30min |
| S3 | Tester monthly_user_performance avec donnees reelles | HAUTE | 30min |

### Comment Tester
```bash
docker exec proctorwise-airflow docker exec proctorwise-spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars/mysql-connector-j-8.0.33.jar \
  /opt/spark-jobs/batch/daily_anomaly_aggregation.py --date 2026-01-27
```

---

## 8. AIRFLOW DAGs

### Etat Actuel
4 DAGs implementes et actifs.

| DAG | Schedule | Status |
|-----|----------|--------|
| `daily_anomaly_aggregation` | `0 2 * * *` | Actif |
| `weekly_grade_analytics` | `0 3 * * 0` | Actif |
| `monthly_user_performance` | `0 5 1 * *` | Actif |
| `full_analytics_pipeline` | Manuel | Actif |

### Taches a Faire

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| D1 | Tester trigger manuel full_analytics_pipeline | HAUTE | 15min |
| D2 | Ajouter alertes email sur echec | Moyenne | 30min |

---

## 9. ML (Machine Learning)

### Etat Actuel

| Detecteur | Fichier | Status |
|-----------|---------|--------|
| MediaPipe Face Detection | `face_detector.py` | OK |
| YOLO Object Detection | `object_detector.py` | OK |
| Hybrid Detector | `object_detector.py` | OK (par defaut) |

### Taches a Faire

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| ML1 | Tester detection visages avec vraie webcam | HAUTE | 30min |
| ML2 | Tester detection objets interdits | HAUTE | 30min |
| ML3 | Pre-telecharger modeles YOLO dans Dockerfile | Moyenne | 30min |

---

## 10. REPARTITION FINALE

### DEV A - Backend, Securite, Tests

**Jour 1 (Aujourd'hui)**
| Tache | Temps |
|-------|-------|
| U4 - Middleware JWT | 1h |
| R1, R2 - Validation reservations | 1h |
| R3, M2, C3, N2, A2 - Proteger endpoints | 2h |
| S1, S2, S3 - Tester Spark jobs | 1h30 |

**Jour 2 (Demain)**
| Tache | Temps |
|-------|-------|
| ML1, ML2 - Tester ML | 1h |
| D1 - Tester Airflow pipeline | 30min |
| Tests integration E2E | 2h |
| Fix bugs | 2h |

### DEV B - Interfaces Web, Documentation

**Jour 1 (Aujourd'hui)**
| Tache | Temps |
|-------|-------|
| M1 - Interface MonitoringService | 2h |
| C1, C2 - Interface CorrectionService | 2h |

**Jour 2 (Demain)**
| Tache | Temps |
|-------|-------|
| A1 - Interface AnalyticsService (Dashboard) | 2h |
| N1 - Interface NotificationService | 1h30 |
| Tests manuels interfaces | 1h30 |

---

## 11. URLs de Test

| Service | URL | Credentials |
|---------|-----|-------------|
| UserService | http://localhost:8001 | - |
| ReservationService | http://localhost:8000 | Requiert login |
| MonitoringService | http://localhost:8003 | - |
| CorrectionService | http://localhost:8004 | - |
| NotificationService | http://localhost:8005 | - |
| AnalyticsService | http://localhost:8006 | - |
| Airflow | http://localhost:8082 | admin/admin |
| Kafka UI | http://localhost:8080 | - |
| Adminer (DB) | http://localhost:8083 | proctorwise/proctorwise_secret |
| MailHog | http://localhost:8025 | - |
| HDFS UI | http://localhost:9870 | - |
| Spark UI | http://localhost:8081 | - |

---

## 12. Checklist Finale

### Fonctionnel
- [x] Login/Register fonctionne
- [x] Roles utilisateurs (etudiant, enseignant, surveillant, admin)
- [x] Creation examen par enseignant
- [x] Reservation examen par etudiant (dropdown)
- [x] Redirection apres login
- [ ] Demarrer session monitoring fonctionne
- [ ] Detection ML (visages, objets) fonctionne
- [ ] Soumission examen fonctionne
- [ ] Correction auto MCQ fonctionne
- [ ] Notifications email arrivent (MailHog)
- [ ] Dashboard analytics affiche des donnees
- [ ] Spark jobs executent sans erreur
- [ ] DAGs Airflow executent sans erreur

### Securite
- [ ] Tous les endpoints proteges par JWT
- [x] Mots de passe hashes (bcrypt)
- [x] Pas de credentials en dur dans le code (sauf docker-compose dev)

### Documentation
- [x] README a jour
- [x] TASKS.md complete
- [x] Instructions d'installation

---

## 13. Commandes Utiles

```bash
# Status tous les containers
docker compose ps

# Logs d'un service
docker compose logs -f userservice

# Rebuild un service
docker compose up -d --build userservice

# Acceder a MariaDB
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret

# Verifier Kafka topics
docker exec proctorwise-kafka kafka-topics --list --bootstrap-server localhost:9092

# Verifier HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise

# Trigger DAG Airflow
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline
```
