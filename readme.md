# ProctorWise

Plateforme de surveillance d'examens en ligne avec detection d'anomalies par intelligence artificielle.

## Fonctionnalites

- **Reservation** des creneaux d'examen par les etudiants
- **Surveillance temps reel** avec detection d'anomalies (ML hybride YOLO/MediaPipe)
- **Correction automatique** des QCM et gestion des corrections manuelles
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

### URLs

| Service | URL | Description |
|---------|-----|-------------|
| UserService | http://localhost:8001 | Login/Register |
| ReservationService | http://localhost:8000 | Gestion reservations |
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
│  └──────┬───────┘ │     │      │ └──────┬───────┘ └──────────────────────────┘  │
│         │         │     ▼      │        │                                        │
│         │         │ Zookeeper  │        │                                        │
│         │         │   :2181    │        │                                        │
│         │         └────────────┘        │                                        │
│         │                               │                                        │
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
│  │  │  │         │                       │   │ │                                 │
│  │  │  │         ▼ spark-submit          │   │ │                                 │
│  │  │  │  ┌───────────────────────────┐  │   │ │                                 │
│  │  │  │  │     SPARK JOBS            │  │   │ │                                 │
│  │  │  │  │ - daily_anomaly_agg       │  │   │ │                                 │
│  │  │  │  │ - weekly_grade_analytics  │  │   │ │                                 │
│  │  │  │  │ - monthly_user_perf       │  │   │ │                                 │
│  │  │  │  └───────────────────────────┘  │   │ │                                 │
│  │  │  └─────────────────────────────────┘   │ │                                 │
│  │  └────────────────────────────────────────┘ │                                 │
│  │                    │                        │                                 │
│  │          lecture/ecriture batch             │                                 │
│  │                    ▼                        │                                 │
│  │         MariaDB + HDFS (aggregats)          │                                 │
│  └─────────────────────────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Flux de donnees

```
┌─────────────┐     REST      ┌─────────────────┐     SQL      ┌─────────────┐
│   Client    │ ────────────► │  Microservice   │ ───────────► │   MariaDB   │
└─────────────┘               └─────────────────┘              └─────────────┘
                                      │
                                      │ Kafka events
                                      ▼
                              ┌─────────────────┐
                              │     Kafka       │
                              │  (async events) │
                              └─────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │  Notif      │   │  Monitoring │   │  Correction │
            │  (consume)  │   │  (consume)  │   │  (consume)  │
            └─────────────┘   └─────────────┘   └─────────────┘


┌─────────────┐   schedule    ┌─────────────┐  spark-submit  ┌─────────────┐
│   Airflow   │ ────────────► │   Spark     │ ─────────────► │  Spark Job  │
│   (DAGs)    │               │   Master    │                │  (Python)   │
└─────────────┘               └─────────────┘                └─────────────┘
                                                                    │
                                                          read/write batch
                                                    ┌───────────────┼───────────────┐
                                                    ▼               ▼               ▼
                                              ┌─────────┐     ┌─────────┐     ┌─────────┐
                                              │ MariaDB │     │  HDFS   │     │ (output)│
                                              └─────────┘     └─────────┘     └─────────┘
```

### Structure des services (Clean Architecture)

```
service/
├── domain/          # Entites metier (dataclasses)
├── application/     # Cas d'usage et interfaces (ABCs)
├── infrastructure/  # Implementations (SQLAlchemy, Kafka, HDFS)
└── interface/       # Controleurs FastAPI et schemas Pydantic
```

## Detection d'Anomalies (ML)

Le MonitoringService utilise une approche hybride ML/regles :

| Anomalie | Methode | Severite |
|----------|---------|----------|
| Visage absent > 5s | Regle | high |
| Plusieurs visages | ML + Regle | critical |
| Objet interdit (telephone, livre, laptop) | YOLO | high |
| Changement d'onglet | Regle | medium |
| Webcam desactivee | Regle | critical |

**Detecteurs ML:**
- MediaPipe Face Detection (visages)
- YOLO Object Detection (objets interdits)
- HybridDetector (combine les deux)

## Big Data Stack

### Composants

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

### DAGs Airflow

Tous les DAGs sont actifs et accessibles via http://localhost:8082 (admin/admin).

## Commandes Utiles

```bash
# Status des containers
docker compose ps

# Logs d'un service
docker compose logs -f userservice

# Rebuild un service
docker compose up -d --build userservice

# Acces base de donnees
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret

# Lister les topics Kafka
docker exec proctorwise-kafka kafka-topics --list --bootstrap-server localhost:9092

# Verifier HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise

# Trigger un DAG Airflow
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline

# Executer un job Spark manuellement
docker exec proctorwise-airflow docker exec proctorwise-spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars/mysql-connector-j-8.0.33.jar \
  /opt/spark-jobs/batch/daily_anomaly_aggregation.py
```

## API Endpoints

### UserService (8001)
- `POST /users/register` - Inscription
- `POST /users/login` - Connexion (retourne JWT)
- `GET /users/{user_id}` - Details utilisateur

### ReservationService (8000)
- `POST /reservations/` - Creer reservation
- `GET /reservations/user/{user_id}` - Liste reservations
- `DELETE /reservations/{reservation_id}` - Annuler

### MonitoringService (8003)
- `POST /monitoring/sessions` - Demarrer session
- `POST /monitoring/sessions/{session_id}/frame` - Envoyer frame
- `GET /monitoring/sessions/{session_id}/anomalies` - Liste anomalies
- `WebSocket /monitoring/sessions/{session_id}/stream` - Streaming temps reel

### CorrectionService (8004)
- `POST /corrections/submissions` - Soumettre examen
- `POST /corrections/submissions/{submission_id}/grade` - Correction auto
- `GET /corrections/submissions/{submission_id}/result` - Resultats

### NotificationService (8005)
- `POST /notifications/` - Envoyer notification
- `GET /notifications/user/{user_id}` - Historique
- `WebSocket /notifications/ws/{user_id}` - Temps reel

### AnalyticsService (8006)
- `GET /analytics/exams/{exam_id}` - Stats examen
- `GET /analytics/users/{user_id}` - Stats utilisateur
- `GET /analytics/platform` - Metriques plateforme
- `GET /analytics/dashboards/admin` - Dashboard admin

## Technologies

| Categorie | Technologies |
|-----------|--------------|
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **ML/Vision** | YOLO (ultralytics), MediaPipe, OpenCV |
| **Messaging** | Apache Kafka, WebSocket |
| **Data** | MariaDB, HDFS, Apache Spark |
| **Orchestration** | Apache Airflow |
| **Infra** | Docker, Docker Compose |

## Documentation

- `CLAUDE.md` - Guide pour Claude Code
- `TASKS.md` - Liste detaillee des taches et etat du projet
- `.env.example` - Variables d'environnement

## Licence

Projet academique - Tous droits reserves.
