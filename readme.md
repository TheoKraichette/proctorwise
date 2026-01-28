# ProctorWise

Plateforme de surveillance d'examens en ligne avec detection d'anomalies par intelligence artificielle.

## Fonctionnalites

- **Gestion des examens** : Creation d'examens avec questions QCM par les enseignants
- **Reservation** des creneaux d'examen par les etudiants
- **Passage d'examen** : Interface interactive avec timer et navigation
- **Correction automatique** des QCM avec score instantane
- **Surveillance temps reel** avec detection d'anomalies (ML hybride YOLO/MediaPipe)
- **Notifications** par email (SMTP) et WebSocket (temps reel)
- **Analytics** avec generation de rapports PDF/CSV et tableaux de bord
- **Big Data** avec Spark, Airflow et HDFS

## Quick Start

### Prerequis

- Docker Desktop
- Git

### Installation

```bash
# Cloner le repository
git clone <repo-url>
cd proctorwise

# Demarrer tous les services
docker compose up -d

# Verifier que tout est lance
docker compose ps
```

### Comptes de test

| Role | Email | Mot de passe |
|------|-------|--------------|
| Etudiant | alice@student.com | password123 |
| Enseignant | bob@teacher.com | password123 |
| Surveillant | charlie@proctor.com | password123 |
| Admin | diana@admin.com | password123 |

### URLs

| Service | URL | Description |
|---------|-----|-------------|
| UserService | http://localhost:8001 | Login/Register |
| ReservationService | http://localhost:8000 | Examens et reservations |
| MonitoringService | http://localhost:8003 | Surveillance examens |
| CorrectionService | http://localhost:8004 | Correction examens |
| NotificationService | http://localhost:8005 | Notifications |
| AnalyticsService | http://localhost:8006 | Rapports/Analytics |
| Airflow | http://localhost:8082 | Orchestration (admin/admin) |
| Kafka UI | http://localhost:8080 | Monitoring Kafka |
| Adminer | http://localhost:8083 | Admin base de donnees |
| MailHog | http://localhost:8025 | Emails de test |
| HDFS UI | http://localhost:9870 | Stockage distribue |
| Spark UI | http://localhost:8081 | Jobs Spark |

## Guide d'utilisation

### Enseignant (bob@teacher.com)

1. Se connecter sur http://localhost:8001
2. Onglet "Creer examen" : Creer un nouvel examen
3. Onglet "Gerer questions" :
   - Selectionner l'examen
   - Ajouter des questions QCM (4 choix) ou Vrai/Faux
   - Definir la bonne reponse et les points
4. Onglet "Resultats" :
   - Selectionner un examen
   - Voir la liste des etudiants avec leurs scores
   - Cliquer "Details" pour voir la copie complete d'un etudiant

### Etudiant (alice@student.com)

1. Se connecter sur http://localhost:8001
2. Onglet "Reserver" : Choisir un examen et une date
3. Onglet "Mes Reservations" :
   - Cliquer "Passer" pour demarrer l'examen
   - Repondre aux questions (timer en haut a droite)
   - Cliquer "Terminer" pour soumettre
   - Confirmation de soumission affichee
   - L'examen passe au statut "completed" (non repassable)

## Architecture

### Vue d'ensemble (Docker Compose - 17 containers)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   DOCKER                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                              CLIENTS                                       │  │
│  │                       (Web Browser / Mobile App)                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                                      ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      MICROSERVICES (FastAPI)                               │  │
│  │  ┌─────────┐ ┌─────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐  │  │
│  │  │  User   │ │ Reservation │ │ Monitoring │ │ Correction │ │   Notif   │  │  │
│  │  │  :8001  │ │    :8000    │ │   :8003    │ │   :8004    │ │   :8005   │  │  │
│  │  └────┬────┘ └──────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬─────┘  │  │
│  │       │             │              │              │              │        │  │
│  │  ┌────┴─────────────┴──────────────┴──────────────┴──────────────┴────┐   │  │
│  │  │                        Analytics :8006                             │   │  │
│  │  └────────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                          │                │                │                     │
│            ┌─────────────┼────────────────┼────────────────┼─────────────┐       │
│            ▼             ▼                ▼                ▼             ▼       │
│  ┌──────────────┐ ┌────────────┐ ┌──────────────┐ ┌──────────────────────────┐  │
│  │   MariaDB    │ │   Kafka    │ │     HDFS     │ │      OUTILS DEV          │  │
│  │    :3306     │ │   :9092    │ │ NameNode:9870│ │  Kafka UI  :8080         │  │
│  │              │ │     │      │ │ DataNode     │ │  Adminer   :8083         │  │
│  │  (6 schemas) │ │     │      │ │              │ │  MailHog   :8025         │  │
│  └──────┬───────┘ │     ▼      │ └──────┬───────┘ └──────────────────────────┘  │
│         │         │ Zookeeper  │        │                                        │
│         │         │   :2181    │        │                                        │
│         │         └────────────┘        │                                        │
│  ┌──────┴───────────────────────────────┴──────┐                                 │
│  │              BIG DATA / BATCH               │                                 │
│  │  ┌────────────────────────────────────────┐ │                                 │
│  │  │            AIRFLOW :8082               │ │                                 │
│  │  │  (Orchestration des jobs Spark)        │ │                                 │
│  │  │         │                              │ │                                 │
│  │  │         ▼ trigger via docker exec      │ │                                 │
│  │  │  ┌─────────────────────────────────┐   │ │                                 │
│  │  │  │      SPARK CLUSTER              │   │ │                                 │
│  │  │  │  Master :7077 (UI :8081)        │   │ │                                 │
│  │  │  │  Worker (2 cores, 2GB)          │   │ │                                 │
│  │  │  └─────────────────────────────────┘   │ │                                 │
│  │  └────────────────────────────────────────┘ │                                 │
│  └─────────────────────────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Structure des services (Clean Architecture)

```
service/
├── domain/          # Entites metier (dataclasses)
├── application/     # Cas d'usage et interfaces (ABCs)
├── infrastructure/  # Implementations (SQLAlchemy, Kafka, HDFS)
└── interface/       # Controleurs FastAPI et schemas Pydantic
```

## Roles Utilisateurs

| Role | Fonctionnalites |
|------|-----------------|
| **Etudiant** | Reserver examen, Passer examen, Voir resultats |
| **Enseignant** | Creer examen, Ajouter questions, Corriger copies |
| **Surveillant** | Surveiller en temps reel, Recevoir alertes |
| **Admin** | Statistiques, Gestion utilisateurs |

## Detection d'Anomalies (ML)

Le MonitoringService utilise une approche hybride ML/regles :

| Anomalie | Methode | Severite |
|----------|---------|----------|
| Visage absent > 5s | Regle | high |
| Plusieurs visages | ML + Regle | critical |
| Objet interdit (telephone, livre, laptop) | YOLO | high |
| Changement d'onglet | Regle | medium |
| Webcam desactivee | Regle | critical |

## Big Data Stack

| Technologie | Role |
|-------------|------|
| **MariaDB** | Base de donnees principale |
| **Apache Kafka** | Bus d'evenements asynchrone |
| **HDFS** | Stockage distribue (frames, rapports) |
| **Apache Spark** | Traitement batch |
| **Apache Airflow** | Orchestration des workflows |

### Jobs Spark

| Job | Schedule | Description |
|-----|----------|-------------|
| daily_anomaly_aggregation | 2h AM | Agregation quotidienne des anomalies |
| weekly_grade_analytics | Dimanche 3h AM | Statistiques hebdomadaires des notes |
| monthly_user_performance | 1er du mois 5h AM | Profils de performance utilisateurs |

## API Endpoints

### UserService (8001)
- `POST /users/register` - Inscription (avec role)
- `POST /users/login` - Connexion (retourne JWT, redirige)
- `GET /users/{user_id}` - Details utilisateur

### ReservationService (8000)
- `POST /exams/` - Creer examen
- `GET /exams/` - Liste examens
- `GET /exams/teacher/{teacher_id}` - Liste examens d'un enseignant
- `POST /exams/{exam_id}/questions/` - Ajouter question
- `GET /exams/{exam_id}/questions` - Liste questions (sans reponses)
- `GET /exams/{exam_id}/questions/with-answers` - Liste questions (avec reponses)
- `POST /reservations/` - Creer reservation
- `GET /reservations/user/{user_id}` - Liste reservations
- `PATCH /reservations/{id}/status` - Mettre a jour statut

### CorrectionService (8004)
- `POST /corrections/submissions` - Soumettre examen
- `POST /corrections/submissions/{id}/grade` - Correction auto
- `GET /corrections/submissions/{id}/result` - Resultats detailles
- `GET /corrections/submissions/exam/{exam_id}` - Soumissions par examen
- `GET /corrections/submissions/user/{user_id}` - Soumissions par utilisateur

### MonitoringService (8003)
- `POST /monitoring/sessions` - Demarrer session
- `POST /monitoring/sessions/{id}/frame` - Envoyer frame
- `GET /monitoring/sessions/{id}/anomalies` - Liste anomalies

## Commandes Utiles

```bash
# Status des containers
docker compose ps

# Logs d'un service
docker compose logs -f userservice

# Rebuild un service
docker compose up -d --build reservationservice

# Acces base de donnees
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret
```

## Technologies

| Categorie | Technologies |
|-----------|--------------|
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Auth** | JWT, bcrypt |
| **ML/Vision** | YOLO (ultralytics), MediaPipe, OpenCV |
| **Messaging** | Apache Kafka, WebSocket |
| **Data** | MariaDB, HDFS, Apache Spark |
| **Orchestration** | Apache Airflow |
| **Infra** | Docker, Docker Compose |

## Documentation

- `CLAUDE.md` - Guide pour Claude Code
- `TASKS.md` - Liste detaillee des taches et etat du projet

## Licence

Projet academique - Tous droits reserves.
