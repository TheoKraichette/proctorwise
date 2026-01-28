# ProctorWise

Plateforme de surveillance d'examens en ligne avec détection d'anomalies par intelligence artificielle.

## Présentation

ProctorWise permet d'organiser et surveiller des examens à distance de manière automatisée :

- **Réservation** des créneaux d'examen par les étudiants
- **Surveillance temps réel** avec détection d'anomalies (ML hybride YOLO/MediaPipe)
- **Correction automatique** des QCM et gestion des correcti1ons manuelles
- **Notifications** par email (SMTP) et WebSocket (temps réel)
- **Analytics** avec génération de rapports PDF/CSV et tableaux de bord

## Architecture

### Vue d'ensemble

L'architecture repose sur **6 microservices** structurés selon la **Clean Architecture**, communiquant via **REST** (synchrone) et **Kafka** (asynchrone).

![Vue système C1](images/C1.png)

![Conteneurs C2](images/C2.png)

### Microservices

| Service | Port | Description |
|---------|------|-------------|
| **UserService** | 8001 | Authentification JWT et gestion des utilisateurs |
| **ReservationService** | 8000 | Gestion des créneaux d'examens |
| **MonitoringService** | 8003 | Surveillance temps réel et détection ML |
| **CorrectionService** | 8004 | Correction automatique et manuelle |
| **NotificationService** | 8005 | Notifications email et WebSocket |
| **AnalyticsService** | 8006 | Rapports et métriques |

![Composants C3](images/C3.png)

### Structure des services (Clean Architecture)

Chaque microservice suit une architecture hexagonale en 4 couches :

```
service/
├── domain/          # Entités métier (dataclasses)
├── application/     # Cas d'usage et interfaces (ABCs)
├── infrastructure/  # Implémentations (SQLAlchemy, Kafka, HDFS)
└── interface/       # Contrôleurs FastAPI et schémas Pydantic
```

### Communication inter-services

**Événements Kafka :**

| Producteur | Événements |
|------------|------------|
| ReservationService | `exam_scheduled`, `exam_cancelled` |
| MonitoringService | `monitoring_started`, `monitoring_stopped`, `anomaly_detected`, `high_risk_alert` |
| CorrectionService | `exam_submitted`, `grading_completed`, `manual_review_required` |

**WebSocket** pour le streaming vidéo temps réel (MonitoringService) et les notifications temps réel (NotificationService).

---

## Diagrammes

### Cas d'utilisation

![Diagramme de cas d'utilisation](images/use_case.png)

### Diagramme de classes

![Diagramme de classes modulaire](images/DDC_modulaire.png)

### Séquence - Création d'une réservation

![Diagramme de séquence](images/sequence_reservation.png)

### Context Map (Bounded Contexts)

![Services 1-2](images/service-1-2.png)
![Services 3-4](images/service-3-4.png)
![Services 5-6](images/service-5-6.png)

---

## Détection d'anomalies

Le MonitoringService utilise une approche hybride ML/règles :

| Anomalie | Méthode | Sévérité |
|----------|---------|----------|
| Visage absent > 5s | Règle | high |
| Plusieurs visages | ML + Règle | critical |
| Objet interdit (téléphone) | YOLO | high |
| Changement d'onglet | Règle | medium |
| Webcam désactivée | Règle | critical |

Une alerte `high_risk_alert` est déclenchée si 3+ anomalies critiques surviennent en moins d'une minute.

---

## Stack Big Data

### Composants

| Technologie | Rôle |
|-------------|------|
| **MariaDB Galera** | Cluster 3 nœuds, réplication synchrone multi-maître |
| **Apache Kafka** | Bus d'événements asynchrone |
| **HDFS** | Stockage distribué (frames, modèles ML, rapports) |
| **Apache Spark** | Traitement batch et streaming |
| **Apache Airflow** | Orchestration centralisée des workflows |

### Structure HDFS

```
hdfs:///proctorwise/
├── raw/
│   ├── frames/{year}/{month}/{day}/{session_id}/
│   └── recordings/{exam_id}/{session_id}/
├── processed/
│   ├── anomaly_reports/{year}/{month}/
│   └── grading_results/{year}/{month}/
├── ml/models/{model_type}/model_v{version}.pt
└── archive/{year}/{month}/
```

---

## Apache Airflow - Orchestration

Apache Airflow est le **chef d'orchestre** de tous les traitements Big Data de ProctorWise. Il coordonne les jobs Spark, les pipelines ETL, le réentraînement des modèles ML et l'archivage des données.

### Pourquoi Airflow ?

| Avantage | Description |
|----------|-------------|
| **Planification** | Cron-like scheduling avec gestion des dépendances entre tâches |
| **Monitoring** | Interface web pour visualiser l'état des DAGs en temps réel |
| **Retry & Alerting** | Relance automatique en cas d'échec + notifications |
| **Scalabilité** | Exécution distribuée avec CeleryExecutor ou KubernetesExecutor |
| **Idempotence** | Rejouer un DAG sans effets de bord grâce aux dates d'exécution |

### Architecture Airflow

```
┌─────────────────────────────────────────────────────────────┐
│                     AIRFLOW WEBSERVER                        │
│                   (Interface de monitoring)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     AIRFLOW SCHEDULER                        │
│            (Planification et déclenchement des DAGs)         │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Worker 1 │   │ Worker 2 │   │ Worker 3 │
        └──────────┘   └──────────┘   └──────────┘
              │               │               │
              ▼               ▼               ▼
        ┌─────────────────────────────────────────┐
        │            SPARK CLUSTER                 │
        │     (Exécution des jobs de traitement)   │
        └─────────────────────────────────────────┘
```

### DAGs ProctorWise

#### 1. `daily_etl_pipeline` - Pipeline ETL Quotidien
**Planification** : Tous les jours à 02:00

```
[Extract Anomalies] → [Transform Data] → [Load to Analytics DB] → [Invalidate Cache]
         │
         └──→ [Spark: daily_anomaly_aggregation.py]
```

**Tâches :**
- Extraction des anomalies détectées (dernières 24h)
- Agrégation par type, sévérité, examen
- Chargement dans la base Analytics
- Invalidation du cache des métriques

#### 2. `weekly_grade_analytics` - Statistiques Hebdomadaires
**Planification** : Dimanche à 03:00

```
[Fetch Grades] → [Spark Processing] → [Generate Stats] → [Store Results]
                        │
                        └──→ [Spark: weekly_grade_analytics.py]
```

**Tâches :**
- Calcul des moyennes, médianes, distributions
- Identification des questions problématiques
- Comparaison avec les semaines précédentes

#### 3. `ml_training_pipeline` - Réentraînement ML
**Planification** : Dimanche à 04:00

```
[Collect Training Data] → [Validate Data] → [Train Model] → [Evaluate] → [Deploy if Better]
         │                                        │                │
         └── HDFS: raw/frames/                    │                └── HDFS: ml/models/
                                                  │
                                            [Spark MLlib]
```

**Tâches :**
- Collecte des frames annotées (dernière semaine)
- Validation de la qualité des données
- Entraînement YOLO/MediaPipe
- Évaluation sur jeu de test
- Déploiement conditionnel (si accuracy > seuil)

#### 4. `monthly_performance_report` - Rapports Mensuels
**Planification** : 1er du mois à 05:00

```
[Aggregate User Data] → [Spark Processing] → [Generate PDF] → [Send Notifications]
         │                      │
         └── All services       └──→ [Spark: monthly_user_performance.py]
```

**Tâches :**
- Agrégation des performances utilisateurs
- Génération des rapports PDF individuels
- Envoi par email aux administrateurs

#### 5. `data_archival_pipeline` - Archivage des Données
**Planification** : 1er du mois à 06:00

```
[Identify Old Data] → [Compress] → [Move to Archive] → [Clean Source] → [Update Metadata]
         │                                │
         └── Data > 90 jours              └── HDFS: archive/{year}/{month}/
```

**Tâches :**
- Identification des données > 90 jours
- Compression (gzip/snappy)
- Déplacement vers zone d'archive HDFS
- Nettoyage des sources
- Mise à jour des métadonnées

#### 6. `data_quality_monitoring` - Contrôle Qualité
**Planification** : Toutes les heures

```
[Check Data Freshness] → [Validate Schema] → [Check Anomalies] → [Alert if Issues]
```

**Tâches :**
- Vérification de la fraîcheur des données
- Validation des schémas de données
- Détection des anomalies dans les flux
- Alertes Slack/Email en cas de problème

### Sensors et Triggers

| Sensor | Rôle |
|--------|------|
| `KafkaSensor` | Attend un événement Kafka avant de démarrer |
| `HdfsSensor` | Vérifie la présence d'un fichier HDFS |
| `ExternalTaskSensor` | Attend la fin d'un autre DAG |
| `SqlSensor` | Vérifie une condition en base de données |

### Commandes Airflow

```bash
# Initialiser la base de données Airflow
airflow db init

# Créer un utilisateur admin
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@proctorwise.com

# Démarrer le webserver (port 8080)
airflow webserver --port 8080

# Démarrer le scheduler
airflow scheduler

# Lister les DAGs
airflow dags list

# Déclencher un DAG manuellement
airflow dags trigger daily_etl_pipeline

# Voir l'état d'un DAG
airflow dags state daily_etl_pipeline 2024-01-15

# Tester une tâche spécifique
airflow tasks test daily_etl_pipeline extract_anomalies 2024-01-15
```

### Configuration Airflow

```python
# airflow.cfg (extrait)
[core]
executor = LocalExecutor  # ou CeleryExecutor pour la production
sql_alchemy_conn = mysql+pymysql://proctorwise:password@mariadb-1:3306/airflow
load_examples = False

[webserver]
web_server_port = 8080
rbac = True

[scheduler]
dag_dir_list_interval = 300
min_file_process_interval = 30

[smtp]
smtp_host = smtp.example.com
smtp_port = 587
smtp_mail_from = airflow@proctorwise.com
```

### Jobs Spark (orchestrés par Airflow)

| Job | Planification | Description |
|-----|---------------|-------------|
| `daily_anomaly_aggregation.py` | 02:00 | Agrégation quotidienne des anomalies |
| `weekly_grade_analytics.py` | Dimanche | Statistiques hebdomadaires des notes |
| `monthly_user_performance.py` | 1er du mois | Profils de performance utilisateurs |

---

## Installation

### Prérequis

- Python 3.11+
- MariaDB Galera Cluster
- Apache Kafka + Zookeeper
- HDFS (Hadoop)

### Dépendances

```bash
# Installer les dépendances de chaque service
pip install -r userservice/requirements.txt
pip install -r reservationservice/requirements.txt
pip install -r monitoringservice/requirements.txt
pip install -r correctionservice/requirements.txt
pip install -r notificationservice/requirements.txt
pip install -r analyticsservice/requirements.txt
```

### Configuration

Copier `.env.example` vers `.env` et configurer les variables :

```bash
cp .env.example .env
```

Variables principales :
- `DATABASE_URL_*` - Connexions MariaDB Galera par service
- `KAFKA_BOOTSTRAP_SERVERS` - Serveurs Kafka
- `HDFS_URL` - URL du NameNode HDFS

### Lancement des services

```bash
# Démarrer chaque service individuellement
uvicorn userservice.main:app --reload --port 8001
uvicorn reservationservice.main:app --reload --port 8000
uvicorn monitoringservice.main:app --reload --port 8003
uvicorn correctionservice.main:app --reload --port 8004
uvicorn notificationservice.main:app --reload --port 8005
uvicorn analyticsservice.main:app --reload --port 8006
```

### Migrations

```bash
# Depuis le répertoire d'un service
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Jobs Spark

```bash
spark-submit --master spark://spark-master:7077 spark-jobs/batch/daily_anomaly_aggregation.py
```

---

## Technologies

### Backend

| Technologie | Usage |
|-------------|-------|
| FastAPI | Framework web asynchrone |
| SQLAlchemy | ORM avec support async (aiomysql) |
| Pydantic | Validation des données |
| aiokafka | Client Kafka asynchrone |

### ML / Vision

| Technologie | Usage |
|-------------|-------|
| YOLO (ultralytics) | Détection d'objets |
| MediaPipe | Détection de visages |
| OpenCV | Traitement d'images |

### Notifications

| Technologie | Usage |
|-------------|-------|
| aiosmtplib | Envoi d'emails asynchrone |
| WebSocket | Notifications temps réel |
| Jinja2 | Templates d'emails |

### Analytics

| Technologie | Usage |
|-------------|-------|
| pandas | Traitement des données |
| ReportLab | Génération PDF |

---

## Choix architecturaux

| Choix | Justification |
|-------|---------------|
| **Microservices** | Découpage métier, déploiement indépendant, scalabilité horizontale |
| **Clean Architecture** | Séparation des responsabilités, testabilité, indépendance des frameworks |
| **MariaDB Galera** | Cohérence forte, haute disponibilité, failover automatique |
| **Kafka** | Découplage des services, fiabilité, rejeu possible des événements |
| **HDFS + Spark** | Stockage et traitement Big Data scalables |
| **Détection hybride** | Précision du ML combinée à la fiabilité des règles déterministes |

---

## Haute disponibilité

### MariaDB Galera

- Cluster 3 nœuds en réplication synchrone multi-maître
- Failover automatique sans perte de données
- Reconnexion automatique via SQLAlchemy

### Services

- Chaque microservice peut être répliqué horizontalement
- Load balancing possible devant chaque service
- Health checks disponibles sur `/health`

---

## Licence

Projet académique - Tous droits réservés.
