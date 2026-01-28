# ProctorWise - Taches Detaillees

**Date**: 28 Janvier 2026
**Deadline**: 29 Janvier soir
**Equipe**: 2 personnes (Dev A & Dev B)

---

## Etat Global du Projet

| Composant | Status | Completude |
|-----------|--------|------------|
| Infrastructure Docker | OK | 100% |
| UserService | Backend OK, UI OK, Roles OK, CORS OK | 100% |
| ReservationService | Backend OK, UI OK, Exams+Questions+Resultats OK | 100% |
| MonitoringService | Backend OK, ML OK, UI manquante | 85% |
| CorrectionService | Backend OK, integre via UI Reservation, Resultats OK | 100% |
| NotificationService | Backend OK, UI manquante | 85% |
| AnalyticsService | Backend OK, UI manquante | 80% |
| Spark Jobs | Code OK, non teste | 90% |
| Airflow DAGs | OK, actifs | 95% |
| ML (YOLO/MediaPipe) | Implemente | 80% |

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
- [x] Reservation d'un creneau
- [x] Passage de l'examen avec timer
- [x] Navigation entre questions
- [x] Barre de progression
- [x] Soumission et correction automatique
- [x] Message de confirmation apres soumission
- [x] Statut "completed" apres soumission (pas de reprise possible)

---

## 1. USERSERVICE (Port 8001)

### Etat Actuel
- **Endpoints**: register, login, get_user
- **JWT**: contient user_id, name, email, role
- **Roles**: student, teacher, proctor, admin
- **UI**: Login/Register avec selection de role
- **Redirection**: Vers ReservationService apres login
- **CORS**: Active (permet appels cross-origin)

### Taches Restantes

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| U1 | Middleware JWT verification | Moyenne | 1h |
| U2 | Endpoint liste users (admin) | Basse | 30min |

---

## 2. RESERVATIONSERVICE (Port 8000)

### Etat Actuel
- **Entites**: Exam, Question, Reservation
- **Endpoints Exams**: CRUD complet
- **Endpoints Questions**: CRUD complet
- **Endpoints Reservations**: CRUD complet + PATCH status
- **UI par role**:
  - Etudiant: Reserver, Passer examen, Voir reservations, Confirmation soumission
  - Enseignant: Creer examen, Gerer questions, Voir resultats, Consulter copies
  - Surveillant: Lien vers monitoring
  - Admin: Liens vers analytics

### Taches Restantes

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| R1 | Validation dates cote serveur | Moyenne | 30min |
| R2 | Detection conflits horaires | Moyenne | 45min |

---

## 3. MONITORINGSERVICE (Port 8003)

### Etat Actuel
- **Backend**: Complet (sessions, frames, anomalies)
- **ML**: MediaPipe + YOLO + HybridDetector
- **UI**: MANQUANTE

### Taches Restantes

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| M1 | Interface Web dashboard surveillant | HAUTE | 2h |
| M2 | Liste des sessions en cours | HAUTE | 30min |
| M3 | Affichage alertes temps reel | HAUTE | 1h |

---

## 4. CORRECTIONSERVICE (Port 8004)

### Etat Actuel
- **Backend**: Complet (submissions, auto-grading, results)
- **Integration**: Via UI ReservationService
- **Auto-grading**: MCQ, True/False, Short answer
- **Endpoints resultats**: Par examen, par utilisateur, details complets
- **CORS**: Active

### Taches Restantes

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| C1 | ~~Interface resultats detailles pour etudiant~~ | ~~Moyenne~~ | ~~1h~~ FAIT |

---

## 5. NOTIFICATIONSERVICE (Port 8005)

### Etat Actuel
- **Backend**: Complet
- **Canaux**: Email (SMTP), WebSocket
- **Kafka**: Consumer actif
- **UI**: MANQUANTE

### Taches Restantes

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| N1 | Interface historique notifications | Moyenne | 1h |

---

## 6. ANALYTICSSERVICE (Port 8006)

### Etat Actuel
- **Backend**: Complet (stats, rapports PDF/CSV)
- **UI**: MANQUANTE

### Taches Restantes

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| A1 | Interface dashboard admin | HAUTE | 2h |
| A2 | Graphiques statistiques | Moyenne | 1h |

---

## 7. SPARK JOBS & AIRFLOW

### Etat Actuel
- 3 jobs Spark implementes et corriges
- 4 DAGs Airflow actifs
- Non testes avec donnees reelles

### Taches Restantes

| ID | Tache | Priorite | Temps |
|----|-------|----------|-------|
| S1 | Tester avec donnees reelles | HAUTE | 1h |

---

## 8. REPARTITION FINALE

### DEV A - Backend & Tests

| Tache | Temps |
|-------|-------|
| S1 - Tester Spark jobs | 1h |
| M1 - Interface MonitoringService | 2h |
| Tests E2E du flux complet | 2h |

### DEV B - Interfaces & Documentation

| Tache | Temps |
|-------|-------|
| A1 - Interface AnalyticsService | 2h |
| Screenshots demo | 30min |
| Tests manuels | 1h30 |

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
- [x] Ajout questions QCM/Vrai-Faux
- [x] Reservation examen par etudiant
- [x] Passage examen avec timer
- [x] Correction automatique
- [x] Confirmation soumission (sans affichage score)
- [x] Statut "completed" empeche reprise examen
- [x] Enseignant voit liste resultats par examen
- [x] Enseignant consulte copie detaillee etudiant
- [ ] Dashboard monitoring (surveillant)
- [ ] Dashboard analytics (admin)
- [ ] Spark jobs testes

### Documentation
- [x] README avec guide utilisation
- [x] CLAUDE.md a jour
- [x] TASKS.md a jour
- [x] Comptes de test documentes

---

## 11. Commandes Utiles

```bash
# Status
docker compose ps

# Rebuild un service
docker compose up -d --build reservationservice

# Logs
docker compose logs -f reservationservice

# Base de donnees
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret

# Trigger Airflow
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline
```
