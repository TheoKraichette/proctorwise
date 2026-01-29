# ProctorWise - Taches Detaillees

**Derniere mise a jour**: 29 Janvier 2026
**Deadline**: 29 Janvier soir
**Equipe**: 2 personnes (Dev A & Dev B)

---

## Etat Global du Projet

| Composant | Status | Completude |
|-----------|--------|------------|
| Infrastructure Docker | OK (17 containers configures) | 100% |
| UserService | Backend OK, UI OK, Roles OK, CORS OK, JWT OK | 100% |
| ReservationService | Backend OK, UI OK, Exams+Questions+Resultats+Copies OK | 100% |
| CorrectionService | Backend OK, integre via UI Reservation, Auto-grading OK | 100% |
| MonitoringService | Backend OK, ML OK, WebSocket OK, **UI manquante** | 85% |
| NotificationService | Backend OK, Email+WS OK, Kafka OK, **UI manquante** | 85% |
| AnalyticsService | Backend OK, PDF/CSV OK, **UI manquante** | 80% |
| Spark Jobs | 3 jobs implementes, non testes | 90% |
| Airflow DAGs | 4 DAGs configures, non testes | 95% |
| ML (YOLO/MediaPipe) | HybridDetector implemente | 80% |

---

## Fonctionnalites Implementees

### Flux complet Enseignant
- [x] Connexion avec role "teacher"
- [x] Creation d'examens (titre, description, duree)
- [x] Ajout de questions QCM (4 choix)
- [x] Ajout de questions Vrai/Faux
- [x] Visualisation des questions avec reponses
- [x] Suppression de questions
- [x] Onglet Resultats avec liste des soumissions
- [x] Vue detaillee de la copie de chaque etudiant

### Flux complet Etudiant
- [x] Connexion avec role "student"
- [x] Liste des examens disponibles (avec nb questions)
- [x] Reservation d'un creneau (date + heure)
- [x] Passage de l'examen avec timer
- [x] Navigation entre questions
- [x] Barre de progression
- [x] Soumission et correction automatique
- [x] Message de confirmation apres soumission
- [x] Statut "completed" apres soumission (pas de reprise possible)

### Flux Surveillant
- [ ] Dashboard temps reel (UI manquante)
- [x] Backend monitoring complet (sessions, frames, anomalies)
- [x] Detection ML (MediaPipe + YOLO)
- [x] WebSocket pour alertes temps reel

### Flux Admin
- [ ] Dashboard analytics (UI manquante)
- [x] Backend analytics complet (stats, rapports)
- [x] Export PDF/CSV

---

## 1. USERSERVICE (Port 8001) - COMPLET

### Etat Actuel
- **Endpoints**: `POST /users/register`, `POST /users/login`, `GET /users/{user_id}`, `GET /health`
- **JWT**: contient user_id, name, email, role, exp (HS256)
- **Roles**: student, teacher, proctor, admin
- **UI**: Login/Register avec onglets et selection de role (HTML embarque)
- **Redirection**: Vers ReservationService apres login avec token en URL
- **CORS**: Active (permet appels cross-origin)
- **Securite**: bcrypt pour hash des mots de passe

### Taches Restantes

| ID | Tache | Priorite | Status |
|----|-------|----------|--------|
| U1 | Middleware JWT verification | Basse | Non fait |
| U2 | Endpoint liste users (admin) | Basse | Non fait |

> Ces taches sont optionnelles, le service est fonctionnel sans.

---

## 2. RESERVATIONSERVICE (Port 8000) - COMPLET

### Etat Actuel
- **Entites**: Exam, Question, Reservation
- **Endpoints Exams**: CRUD complet (`POST/GET /exams/`, `GET /exams/{id}`, `GET /exams/teacher/{id}`, `DELETE /exams/{id}`)
- **Endpoints Questions**: CRUD complet (`POST /exams/{id}/questions/`, `POST .../bulk`, `GET .../questions`, `GET .../with-answers`)
- **Endpoints Reservations**: CRUD complet (`POST /reservations/`, `GET .../user/{id}`, `PATCH .../status`, `DELETE`)
- **UI par role** (HTML embarque avec CSS/JS inline):
  - Etudiant: Reserver, Passer examen, Voir reservations, Confirmation soumission
  - Enseignant: Creer examen, Gerer questions (QCM + Vrai/Faux), Voir resultats, Consulter copies
  - Surveillant: Lien vers MonitoringService
  - Admin: Grille avec liens vers Analytics et gestion users
- **Integration**: Appels directs vers CorrectionService (port 8004) pour soumission et resultats

### Taches Restantes

| ID | Tache | Priorite | Status |
|----|-------|----------|--------|
| R1 | Validation dates cote serveur | Basse | Non fait |
| R2 | Detection conflits horaires | Basse | Non fait |

> Ces taches sont optionnelles, le flux principal fonctionne.

---

## 3. MONITORINGSERVICE (Port 8003) - UI MANQUANTE

### Etat Actuel
- **Backend**: Complet (sessions, frames, anomalies)
- **Endpoints**:
  - `POST /monitoring/sessions` - Demarrer session
  - `POST /monitoring/sessions/{id}/frame` - Traiter frame
  - `PUT /monitoring/sessions/{id}/stop` - Arreter session
  - `GET /monitoring/sessions/{id}` - Details session
  - `GET /monitoring/sessions/{id}/anomalies` - Liste anomalies
  - `GET /monitoring/sessions/{id}/anomalies/summary` - Resume anomalies
  - `WS /monitoring/sessions/{id}/stream` - WebSocket temps reel
- **ML**: MediaPipe (visages) + YOLO/ultralytics (objets) + regles
- **Detection**: Face absente, multiples visages, objets interdits (telephone, livre, laptop), changement onglet, webcam desactivee
- **Severites**: critical, high, medium, low
- **Stockage**: HDFS ou local pour les frames
- **Kafka**: Publisher pour evenements anomalies
- **UI**: **MANQUANTE** - Pas de dashboard web pour le surveillant

### Taches Restantes

| ID | Tache | Priorite | Status |
|----|-------|----------|--------|
| **M1** | **Interface Web dashboard surveillant** | **HAUTE** | **Non fait** |
| **M2** | **Liste des sessions en cours** | **HAUTE** | **Non fait** |
| **M3** | **Affichage alertes temps reel** | **HAUTE** | **Non fait** |

---

## 4. CORRECTIONSERVICE (Port 8004) - COMPLET

### Etat Actuel
- **Backend**: Complet (submissions, auto-grading, results)
- **Endpoints**:
  - `POST /corrections/submissions` - Soumettre reponses
  - `POST /corrections/submissions/{id}/grade` - Corriger auto
  - `GET /corrections/submissions/{id}/result` - Resultat detaille
  - `GET /corrections/submissions/exam/{exam_id}` - Soumissions par examen
  - `GET /corrections/submissions/user/{user_id}` - Soumissions par user
  - `PUT /corrections/submissions/{id}/answers/{answer_id}` - Correction manuelle
- **Auto-grading**: MCQ, True/False, Short answer
- **Integration**: Via UI ReservationService (pas d'UI propre necessaire)
- **CORS**: Active
- **Kafka**: Publisher pour evenements de notation

### Taches Restantes
Aucune - service complet et integre.

---

## 5. NOTIFICATIONSERVICE (Port 8005) - UI MANQUANTE

### Etat Actuel
- **Backend**: Complet
- **Endpoints**:
  - `POST /notifications/` - Envoyer notification
  - `GET /notifications/user/{user_id}` - Historique user
  - `GET /notifications/preferences/{user_id}` - Preferences
  - `PUT /notifications/preferences/{user_id}` - Modifier preferences
  - `WS /notifications/ws/{user_id}` - WebSocket temps reel
- **Canaux**: Email (SMTP via MailHog), WebSocket
- **Kafka**: Consumer actif pour evenements
- **Templates**: Templates email dans `infrastructure/templates/`
- **UI**: **MANQUANTE** - Pas d'interface pour voir l'historique

### Taches Restantes

| ID | Tache | Priorite | Status |
|----|-------|----------|--------|
| N1 | Interface historique notifications | Moyenne | Non fait |

---

## 6. ANALYTICSSERVICE (Port 8006) - UI MANQUANTE

### Etat Actuel
- **Backend**: Complet (stats, rapports PDF/CSV)
- **Endpoints**:
  - `GET /analytics/exams/{exam_id}` - Stats examen
  - `GET /analytics/exams/{exam_id}/report/pdf` - Export PDF
  - `GET /analytics/exams/{exam_id}/report/csv` - Export CSV
  - `GET /analytics/users/{user_id}` - Stats utilisateur
  - `GET /analytics/users/{user_id}/report/pdf` - Export PDF user
  - `GET /analytics/users/{user_id}/report/csv` - Export CSV user
  - `GET /analytics/platform` - Metriques plateforme
  - `GET /analytics/dashboards/admin` - Donnees dashboard admin
- **Fonctionnalites**: Distribution des scores, analytics par question, taux de reussite, metriques plateforme
- **Rapports**: PDFReportGenerator, CSVExporter
- **Cache**: InMemoryCacheStore
- **UI**: **MANQUANTE** - Pas de dashboard web pour l'admin

### Taches Restantes

| ID | Tache | Priorite | Status |
|----|-------|----------|--------|
| **A1** | **Interface dashboard admin** | **HAUTE** | **Non fait** |
| **A2** | **Graphiques statistiques** | **Moyenne** | **Non fait** |

---

## 7. SPARK JOBS & AIRFLOW

### Etat Actuel
- 3 jobs Spark implementes avec connexion MariaDB JDBC
- 4 DAGs Airflow configures
- Non testes avec donnees reelles

### DAGs Airflow
| DAG | Schedule | Description |
|-----|----------|-------------|
| `daily_anomaly_aggregation` | Tous les jours a 2h | Agregation anomalies par examen/user/heure |
| `weekly_grade_analytics` | Dimanche a 3h | Stats notes de la semaine |
| `monthly_user_performance` | 1er du mois a 5h | Performance utilisateurs |
| `full_analytics_pipeline` | Manuel | Execute les 3 jobs en sequence |

### Spark Jobs
| Job | Input | Output |
|-----|-------|--------|
| `daily_anomaly_aggregation.py` | MariaDB monitoring | HDFS parquet |
| `weekly_grade_analytics.py` | MariaDB corrections | HDFS parquet |
| `monthly_user_performance.py` | MariaDB corrections | HDFS parquet |

### Taches Restantes

| ID | Tache | Priorite | Status |
|----|-------|----------|--------|
| S1 | Tester avec donnees reelles | Moyenne | Non fait |

---

## 8. INFRASTRUCTURE DOCKER

### Containers (17 au total)

**Microservices (6)**:
- `proctorwise-userservice` (port 8001)
- `proctorwise-reservationservice` (port 8000)
- `proctorwise-monitoringservice` (port 8003)
- `proctorwise-correctionservice` (port 8004)
- `proctorwise-notificationservice` (port 8005)
- `proctorwise-analyticsservice` (port 8006)

**Data & Streaming (5)**:
- `proctorwise-mariadb` (port 3306)
- `proctorwise-zookeeper`
- `proctorwise-kafka` (port 9092)
- `proctorwise-namenode` (ports 9870, 9000)
- `proctorwise-datanode`

**Processing & Orchestration (3)**:
- `proctorwise-spark-master` (ports 7077, 8080, 6066)
- `proctorwise-spark-worker`
- `proctorwise-airflow` (port 8082)

**Outils (3)**:
- `proctorwise-kafka-ui` (port 8080)
- `proctorwise-mailhog` (ports 1025, 8025)
- `proctorwise-adminer` (port 8083)

---

## 9. Comptes de Test

| Role | Email | Password |
|------|-------|----------|
| Etudiant | alice@student.com | password123 |
| Enseignant | bob@teacher.com | password123 |
| Surveillant | charlie@proctor.com | password123 |
| Admin | diana@admin.com | password123 |

---

## 10. Checklist Finale

### Fonctionnel
- [x] Login/Register avec roles
- [x] Creation examen par enseignant
- [x] Ajout questions QCM
- [x] Ajout questions Vrai/Faux
- [x] Reservation examen par etudiant
- [x] Passage examen avec timer
- [x] Correction automatique
- [x] Confirmation soumission (sans affichage score)
- [x] Statut "completed" empeche reprise examen
- [x] Enseignant voit liste resultats par examen
- [x] Enseignant consulte copie detaillee etudiant
- [ ] **Dashboard monitoring (surveillant) - UI MANQUANTE**
- [ ] **Dashboard analytics (admin) - UI MANQUANTE**
- [ ] Historique notifications (UI manquante)
- [ ] Spark jobs testes avec donnees reelles

### Infrastructure
- [x] Docker Compose avec 17 containers
- [x] MariaDB avec 6 bases de donnees
- [x] Kafka + Zookeeper
- [x] HDFS (NameNode + DataNode)
- [x] Spark (Master + Worker)
- [x] Airflow avec 4 DAGs
- [x] MailHog pour emails
- [x] Adminer pour BDD
- [x] CORS entre services

### Documentation
- [x] README avec guide utilisation
- [x] CLAUDE.md a jour
- [x] TASKS.md a jour
- [x] Comptes de test documentes

---

## 11. Resume des Taches Restantes (par priorite)

### Priorite HAUTE
| ID | Service | Tache |
|----|---------|-------|
| M1 | MonitoringService | Interface Web dashboard surveillant |
| M2 | MonitoringService | Liste des sessions en cours |
| M3 | MonitoringService | Affichage alertes temps reel |
| A1 | AnalyticsService | Interface dashboard admin |

### Priorite Moyenne
| ID | Service | Tache |
|----|---------|-------|
| A2 | AnalyticsService | Graphiques statistiques |
| N1 | NotificationService | Interface historique notifications |
| S1 | Spark/Airflow | Tester avec donnees reelles |

### Priorite Basse (optionnel)
| ID | Service | Tache |
|----|---------|-------|
| U1 | UserService | Middleware JWT verification |
| U2 | UserService | Endpoint liste users (admin) |
| R1 | ReservationService | Validation dates cote serveur |
| R2 | ReservationService | Detection conflits horaires |

---

## 12. Commandes Utiles

```bash
# Status
docker compose ps

# Rebuild un service
docker compose up -d --build reservationservice

# Logs
docker compose logs -f reservationservice

# Base de donnees
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret

# Kafka topics
docker exec proctorwise-kafka kafka-topics --list --bootstrap-server localhost:9092

# HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise

# Trigger Airflow
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline
```
