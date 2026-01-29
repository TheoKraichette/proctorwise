# ProctorWise - Guide Production & Pipeline Big Data

**Date**: 29 Janvier 2026
**Cible**: VPS OVH (8 GB RAM min, 4 vCPU, 80 GB SSD)

---

## Table des matieres

1. [Etat actuel & ce qui manque](#1-etat-actuel--ce-qui-manque)
2. [Schema pipeline Big Data](#2-schema-pipeline-big-data)
3. [Corrections critiques avant prod](#3-corrections-critiques-avant-prod)
4. [Guide deploiement VPS](#4-guide-deploiement-vps)
5. [Configuration production](#5-configuration-production)
6. [Base de donnees](#6-base-de-donnees)
7. [Securite](#7-securite)
8. [Maintenance & monitoring](#8-maintenance--monitoring)

---

## 1. Etat actuel & ce qui manque

### 1.1 Vue d'ensemble

| Composant | Etat | Pret pour prod ? |
|-----------|------|------------------|
| 6 Microservices | Fonctionnels, testes | Presque (URLs hardcodees) |
| MariaDB | Fonctionnel, 7 bases | Presque (credentials, backup) |
| Kafka + Zookeeper | Fonctionnel | Presque (single broker) |
| HDFS (NameNode + DataNode) | Fonctionnel | Non (permissions, single node) |
| Spark (Master + Worker) | Fonctionnel | Non (memory mismatch, bugs) |
| Airflow | Fonctionnel | Non (error masking, secrets) |
| YOLO / MediaPipe | Fonctionnel | Oui |

### 1.2 Bugs critiques a corriger

#### BUG 1 : Error masking dans les DAGs Airflow
- **Fichier** : `airflow/dags/proctorwise_spark_jobs.py` ligne 33
- **Probleme** : `|| echo "Spark job completed"` masque les erreurs Spark
- **Impact** : Les retries Airflow ne se declenchent jamais, les echecs sont invisibles
- **Fix** : Supprimer le `|| echo`, laisser Airflow voir le code retour reel

#### BUG 2 : Memory mismatch Spark Worker vs Monthly Job
- **Fichier** : DAG ligne 101 demande `--executor-memory 4g`
- **Config** : Worker configure a `2g` (docker-compose.yml ligne 141)
- **Impact** : Le job monthly_user_performance ne peut jamais s'executer
- **Fix** : Reduire executor-memory a `1g` ou augmenter worker a `4g`

#### BUG 3 : Troncature donnees weekly_grade_analytics
- **Fichier** : `spark-jobs/batch/weekly_grade_analytics.py` ligne 195
- **Probleme** : `submission_ids[:1000]` limite a 1000 soumissions
- **Impact** : Donnees incompletes si plus de 1000 soumissions/semaine
- **Fix** : Utiliser un JOIN Spark au lieu de collect() + filtre Python

#### BUG 4 : collect() en memoire driver
- **Fichier** : `spark-jobs/batch/weekly_grade_analytics.py` ligne 193
- **Probleme** : `collect()` charge tous les IDs dans le driver
- **Impact** : OOM (Out of Memory) si gros volume
- **Fix** : Remplacer par un JOIN direct entre DataFrames Spark

#### BUG 5 : Credentials hardcodes
- **Fichiers** : Tous les Spark jobs + docker-compose.yml
- **Probleme** : `user=proctorwise, password=proctorwise_secret` en clair dans le code
- **Fix** : Variables d'environnement via fichier `.env`

### 1.3 Ce qui manque pour la prod

| Categorie | Manquant | Priorite |
|-----------|----------|----------|
| **Pipeline** | Pas de validation pre/post job (DB up ? HDFS dispo ? Output existe ?) | HAUTE |
| **Pipeline** | Pas de sync HDFS → AnalyticsService (resultats Spark restent dans HDFS) | HAUTE |
| **Pipeline** | init-hdfs.sh doit etre lance manuellement | MOYENNE |
| **Securite** | Credentials hardcodes partout | HAUTE |
| **Securite** | HDFS permissions 777 (tout le monde peut ecrire) | HAUTE |
| **Securite** | Pas de SSL/TLS entre services | MOYENNE |
| **Infra** | Pas de restart policy sur les services | HAUTE |
| **Infra** | Ports internes exposes (3306, 9092, 9870) | HAUTE |
| **Infra** | Pas de backup BDD automatise | HAUTE |
| **Infra** | Pas de retention/cleanup HDFS (parquet accumule) | MOYENNE |
| **Monitoring** | Pas d'alertes email Airflow en cas d'echec | MOYENNE |
| **Monitoring** | Pas de monitoring espace disque HDFS | BASSE |
| **URLs** | URLs `localhost:800X` hardcodees dans le JS client | HAUTE |

---

## 2. Schema pipeline Big Data

### 2.1 Architecture globale

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   VPS OVH                          │
                    │                                                     │
   Utilisateurs     │  ┌─────────┐    ┌──────────────┐                   │
   ────────────────►│  │  Nginx  │───►│ UserService  │                   │
   (HTTPS)          │  │ Reverse │    │   (8001)     │                   │
                    │  │  Proxy  │    └──────────────┘                   │
                    │  │  (443)  │    ┌──────────────┐                   │
                    │  │         │───►│ Reservation  │──┐                │
                    │  │         │    │   (8000)     │  │                │
                    │  │         │    └──────────────┘  │                │
                    │  │         │    ┌──────────────┐  │  ┌───────────┐ │
                    │  │         │───►│ Monitoring   │──┼─►│  Kafka    │ │
                    │  │         │    │   (8003)     │  │  │  (9092)   │ │
                    │  │         │    └──────┬───────┘  │  └─────┬─────┘ │
                    │  │         │           │          │        │       │
                    │  │         │    ┌──────────────┐  │  ┌─────▼─────┐ │
                    │  │         │───►│ Analytics    │  │  │Notification│ │
                    │  │         │    │   (8006)     │  │  │  (8005)   │ │
                    │  └─────────┘    └──────────────┘  │  └───────────┘ │
                    │                                    │                │
                    │                 ┌──────────────┐  │                │
                    │                 │ Correction   │◄─┘                │
                    │                 │   (8004)     │                   │
                    │                 └──────────────┘                   │
                    └─────────────────────────────────────────────────────┘
```

### 2.2 Pipeline de donnees (Airflow orchestre)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     SOURCES DE DONNEES (MariaDB)                        │
│                                                                          │
│  proctorwise_monitoring     proctorwise_corrections                      │
│  ┌────────────────────┐     ┌──────────────────────┐                     │
│  │ monitoring_sessions │     │ exam_submissions     │                     │
│  │ anomalies           │     │ answers              │                     │
│  └────────┬───────────┘     └──────────┬───────────┘                     │
│           │                             │                                 │
└───────────┼─────────────────────────────┼─────────────────────────────────┘
            │                             │
            ▼                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     AIRFLOW - ORCHESTRATION                              │
│                                                                          │
│  DAG 1: daily_anomaly_aggregation        Tous les jours a 2h00          │
│  ┌───────┐    ┌─────────────────┐    ┌─────────┐                        │
│  │ start │───►│ spark-submit    │───►│   end   │                        │
│  └───────┘    │ daily_anomaly.. │    └─────────┘                        │
│               └─────────────────┘                                        │
│                                                                          │
│  DAG 2: weekly_grade_analytics           Dimanche a 3h00                │
│  ┌───────┐    ┌─────────────────┐    ┌─────────┐                        │
│  │ start │───►│ spark-submit    │───►│   end   │                        │
│  └───────┘    │ weekly_grade..  │    └─────────┘                        │
│               └─────────────────┘                                        │
│                                                                          │
│  DAG 3: monthly_user_performance         1er du mois a 5h00            │
│  ┌───────┐    ┌─────────────────┐    ┌─────────┐                        │
│  │ start │───►│ spark-submit    │───►│   end   │                        │
│  └───────┘    │ monthly_user..  │    └─────────┘                        │
│               └─────────────────┘                                        │
│                                                                          │
│  DAG 4: full_analytics_pipeline          Declenchement manuel           │
│  ┌───────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  ┌───────┐  │
│  │ start │───►│ anomaly  │───►│  grade   │───►│   user   │─►│  end  │  │
│  └───────┘    │   job    │    │   job    │    │   job    │  └───────┘  │
│               └──────────┘    └──────────┘    └──────────┘             │
│                                                                          │
│  Execution : docker exec spark-master spark-submit --master spark://..  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     SPARK - TRAITEMENT                                    │
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────────────────────────────┐  │
│  │   Spark Master   │     │              Spark Worker                │  │
│  │     (7077)       │────►│  2 cores / 2 GB RAM                     │  │
│  └──────────────────┘     │                                          │  │
│                            │  Job 1: Lit anomalies + sessions MariaDB │  │
│                            │         → Agregation par exam/user/heure │  │
│                            │                                          │  │
│                            │  Job 2: Lit submissions + answers MariaDB│  │
│                            │         → Stats notes, difficulte quest. │  │
│                            │                                          │  │
│                            │  Job 3: Lit corrections + monitoring     │  │
│                            │         → Profils user, rankings, risque │  │
│                            └──────────────────┬───────────────────────┘  │
│                                                │                         │
└────────────────────────────────────────────────┼─────────────────────────┘
                                                 │
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     HDFS - STOCKAGE DISTRIBUE                            │
│                                                                          │
│  hdfs://namenode:9000/proctorwise/                                       │
│  │                                                                       │
│  ├── raw/frames/                    (frames webcam - reserve)            │
│  │                                                                       │
│  ├── processed/                                                          │
│  │   ├── anomaly_reports/           (Spark daily output)                 │
│  │   │   └── {YYYY}/{MM}/                                               │
│  │   │       ├── by_exam/{DD}/      → Anomalies par examen (parquet)    │
│  │   │       ├── by_user/{DD}/      → Anomalies par user (parquet)      │
│  │   │       └── hourly/{DD}/       → Anomalies par heure (parquet)     │
│  │   │                                                                   │
│  │   ├── grading_results/           (Spark weekly output)                │
│  │   │   └── {YYYY}/week_{WW}/                                          │
│  │   │       ├── exam_statistics/   → Stats par examen (parquet)        │
│  │   │       ├── question_difficulty/→ Difficulte questions (parquet)   │
│  │   │       ├── daily_trends/      → Tendances journalieres (parquet)  │
│  │   │       └── grading_efficiency/→ Efficacite correction (parquet)   │
│  │   │                                                                   │
│  │   └── user_performance/          (Spark monthly output)               │
│  │       └── {YYYY}/{MM}/                                                │
│  │           ├── user_profiles/     → Profils complets (parquet)        │
│  │           ├── top_performers/    → Top 100 etudiants (parquet)       │
│  │           ├── at_risk_users/     → Etudiants a risque (parquet)      │
│  │           ├── most_improved/     → Plus grande progression (parquet) │
│  │           ├── tier_summary/      → Repartition par niveau (parquet)  │
│  │           └── risk_summary/      → Repartition par risque (parquet)  │
│  │                                                                       │
│  ├── ml/models/                     (reserve pour modeles ML)            │
│  └── archive/                       (reserve pour archivage)             │
│                                                                          │
│  NameNode (9870) ──► DataNode (stockage blocs)                           │
│  Replication: 1 (single node)                                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Flux de donnees complet (de l'etudiant au rapport)

```
Etudiant passe examen
        │
        ├──► ReservationService ──► CorrectionService ──► MariaDB (corrections)
        │    (reponses)              (auto-grading)        exam_submissions
        │                                                   answers
        │
        └──► MonitoringService ──► MariaDB (monitoring)
             (frames webcam)       monitoring_sessions
             (anomalies YOLO)      anomalies
                    │
                    └──► Kafka ──► NotificationService ──► Email/WebSocket
                         (events)   (alertes proctor)

                              ╔═══════════════════════════╗
                              ║   AIRFLOW DECLENCHE       ║
                              ║   LES JOBS SPARK          ║
                              ╚═══════════╦═══════════════╝
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
             Daily (2h)           Weekly (dim 3h)        Monthly (1er 5h)
             Anomalies            Notes                  Performance
             MariaDB → HDFS      MariaDB → HDFS         MariaDB → HDFS
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          │
                                          ▼
                              HDFS (fichiers Parquet)
                                          │
                                          ▼
                              AnalyticsService (8006)
                              Dashboard admin + PDF/CSV
```

---

## 3. Corrections critiques avant prod

### 3.1 Fix error masking dans les DAGs

**Fichier** : `airflow/dags/proctorwise_spark_jobs.py`

Remplacer ligne 33 :
```python
# AVANT (bug)
f'{spark_submit_cmd} || echo "Spark job completed (check logs for details)"'

# APRES (fix)
f'{spark_submit_cmd}'
```

### 3.2 Fix memory mismatch

**Option A** : Reduire la demande du job monthly (recommande pour 8 GB VPS)
```python
# Dans le DAG, ligne 101, changer :
--executor-memory 4g
# En :
--executor-memory 1g
```

**Option B** : Augmenter le worker (si VPS 16 GB)
```yaml
# docker-compose.yml, spark-worker
SPARK_WORKER_MEMORY=4g
```

### 3.3 Fix data truncation weekly job

**Fichier** : `spark-jobs/batch/weekly_grade_analytics.py`

Remplacer le pattern collect() + filtre par un JOIN Spark :
```python
# AVANT (bug lignes 193-195)
submission_ids = [row.submission_id for row in submissions_df.select("submission_id").collect()]
answers_df = load_answers_data(spark, submission_ids[:1000])

# APRES (fix)
answers_df = spark.read.jdbc(url, "answers", properties=props)
answers_df = answers_df.join(submissions_df.select("submission_id"), "submission_id")
```

### 3.4 Externaliser les credentials

Creer un fichier `.env` a la racine :
```bash
# .env (NE PAS COMMITTER - ajouter au .gitignore)
DB_ROOT_PASSWORD=un_mot_de_passe_fort_root
DB_USER=proctorwise
DB_PASSWORD=un_mot_de_passe_fort_app
JWT_SECRET=une_cle_jwt_longue_et_aleatoire
AIRFLOW_FERNET_KEY=81HqDtbqAywKSOumSha3BhWNOdQ26slT6K0YaZeZyPs=
AIRFLOW_SECRET_KEY=une_cle_secrete_airflow
```

Puis dans docker-compose.yml utiliser `${DB_PASSWORD}` au lieu des valeurs en dur.

---

## 4. Guide deploiement VPS

### 4.1 Commander le VPS

Sur OVH : **VPS Essential** minimum (8 GB RAM, 4 vCPU, 80 GB SSD)
- OS : **Ubuntu 22.04 LTS** ou **Debian 12**
- Localisation : Gravelines ou Strasbourg (France)

### 4.2 Setup initial

```bash
# 1. Connexion SSH
ssh root@IP_DU_VPS

# 2. Creer un user non-root
adduser proctorwise
usermod -aG sudo proctorwise
su - proctorwise

# 3. Update systeme
sudo apt update && sudo apt upgrade -y

# 4. Installer Docker + Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker proctorwise
# IMPORTANT: se reconnecter pour que le groupe prenne effet
exit
ssh proctorwise@IP_DU_VPS

# 5. Verifier Docker
docker --version
docker compose version

# 6. Installer Nginx + Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# 7. Installer Git
sudo apt install -y git

# 8. Cloner le projet
git clone https://github.com/TheoKraichette/proctorwise.git
cd proctorwise
```

### 4.3 Configurer le DNS (sous-domaine)

Sur le panel DNS de ton domaine, ajouter les enregistrements A :

```
proctorwise.tondomaine.fr      A    IP_DU_VPS
app.proctorwise.tondomaine.fr  A    IP_DU_VPS
monitor.proctorwise.tondomaine.fr  A    IP_DU_VPS
analytics.proctorwise.tondomaine.fr A  IP_DU_VPS
airflow.proctorwise.tondomaine.fr  A   IP_DU_VPS
```

### 4.4 Creer le fichier .env

```bash
cd ~/proctorwise

cat > .env << 'EOF'
# Base de donnees
DB_ROOT_PASSWORD=ChangerCeMotDePasse123!
DB_USER=proctorwise
DB_PASSWORD=ChangerCeMotDePasse456!

# JWT
JWT_SECRET=ChangerCetteCleJWT789SuperLongue

# Airflow
AIRFLOW_FERNET_KEY=81HqDtbqAywKSOumSha3BhWNOdQ26slT6K0YaZeZyPs=
AIRFLOW_SECRET_KEY=ChangerCetteCleAirflow

# URLs publiques (pour le JS client)
PUBLIC_URL=https://proctorwise.tondomaine.fr
MONITORING_URL=https://monitor.proctorwise.tondomaine.fr
ANALYTICS_URL=https://analytics.proctorwise.tondomaine.fr
EOF

chmod 600 .env
```

### 4.5 Lancer les containers

```bash
cd ~/proctorwise

# Build + demarrage
docker compose up -d --build

# Verifier les 17 containers
docker compose ps

# Initialiser HDFS (une seule fois)
bash scripts/init-hdfs.sh

# Creer les users de test
curl -s http://localhost:8001/users/register -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Student","email":"alice@student.com","password":"password123","role":"student"}'

curl -s http://localhost:8001/users/register -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob Teacher","email":"bob@teacher.com","password":"password123","role":"teacher"}'

curl -s http://localhost:8001/users/register -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie Proctor","email":"charlie@proctor.com","password":"password123","role":"proctor"}'

curl -s http://localhost:8001/users/register -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Diana Admin","email":"diana@admin.com","password":"password123","role":"admin"}'
```

### 4.6 Configurer Nginx (reverse proxy + SSL)

```bash
sudo tee /etc/nginx/sites-available/proctorwise << 'NGINX'
# UserService - Login/Register
server {
    server_name proctorwise.tondomaine.fr;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ReservationService - App principale
server {
    server_name app.proctorwise.tondomaine.fr;

    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# MonitoringService - Proctor (avec WebSocket)
server {
    server_name monitor.proctorwise.tondomaine.fr;

    location / {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}

# AnalyticsService - Admin
server {
    server_name analytics.proctorwise.tondomaine.fr;

    location / {
        proxy_pass http://localhost:8006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Airflow UI (admin seulement)
server {
    server_name airflow.proctorwise.tondomaine.fr;

    location / {
        proxy_pass http://localhost:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

# Activer le site
sudo ln -sf /etc/nginx/sites-available/proctorwise /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# SSL avec Certbot (apres propagation DNS)
sudo certbot --nginx \
  -d proctorwise.tondomaine.fr \
  -d app.proctorwise.tondomaine.fr \
  -d monitor.proctorwise.tondomaine.fr \
  -d analytics.proctorwise.tondomaine.fr \
  -d airflow.proctorwise.tondomaine.fr
```

### 4.7 Firewall

```bash
sudo ufw allow 22     # SSH
sudo ufw allow 80     # HTTP (redirect vers HTTPS)
sudo ufw allow 443    # HTTPS
sudo ufw enable

# Verifier - seuls 22, 80, 443 sont exposes
sudo ufw status
```

**Les ports internes (3306, 9092, 9870, 7077, 8080, 8081, 8083, etc.) ne sont PAS exposes.**
Docker les rend accessibles entre containers via le reseau interne `proctorwise`.

---

## 5. Configuration production

### 5.1 docker-compose.prod.yml (override)

Creer ce fichier pour surcharger la config dev :

```yaml
# docker-compose.prod.yml
services:
  # === MICROSERVICES : restart always ===
  userservice:
    restart: always

  reservationservice:
    restart: always

  monitoringservice:
    restart: always

  correctionservice:
    restart: always

  notificationservice:
    restart: always

  analyticsservice:
    restart: always

  # === DATA : restart always ===
  mariadb:
    restart: always
    ports: []  # Ne pas exposer 3306

  kafka:
    restart: always
    ports: []  # Ne pas exposer 9092

  zookeeper:
    restart: always

  # === HDFS ===
  namenode:
    restart: always
    ports:
      - "127.0.0.1:9870:9870"  # WebUI local seulement

  datanode:
    restart: always

  # === SPARK ===
  spark-master:
    restart: always
    ports:
      - "127.0.0.1:8081:8080"  # WebUI local seulement

  spark-worker:
    restart: always
    environment:
      SPARK_WORKER_MEMORY: "2g"
      SPARK_WORKER_CORES: "2"

  # === AIRFLOW ===
  airflow:
    restart: always

  # === OUTILS (desactiver en prod si inutiles) ===
  kafka-ui:
    profiles: ["debug"]  # Ne demarre qu'avec --profile debug
    ports:
      - "127.0.0.1:8080:8080"

  adminer:
    profiles: ["debug"]
    ports:
      - "127.0.0.1:8083:8080"

  mailhog:
    restart: always
```

**Lancement prod** :
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Si besoin des outils de debug :
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile debug up -d
```

### 5.2 URLs JS a corriger

Le code JS dans les templates HTML fait des appels a `http://localhost:800X`.
En prod, les utilisateurs accedent via le navigateur, donc ces URLs doivent pointer
vers les sous-domaines publics.

**Fichiers a modifier** :
- `reservationservice/main.py` : remplacer `http://localhost:8003` et `http://localhost:8004`
- `monitoringservice/main.py` : verifier les URLs internes
- `userservice/main.py` : remplacer la redirection post-login

**Approche recommandee** : injecter les URLs via variables d'environnement Python,
puis les passer au HTML template.

---

## 6. Base de donnees

### 6.1 Les 7 bases MariaDB

| Base | Service | Tables principales |
|------|---------|-------------------|
| `proctorwise_users` | UserService | users |
| `proctorwise_reservations` | ReservationService | exams, exam_slots, questions, reservations |
| `proctorwise_monitoring` | MonitoringService | monitoring_sessions, anomalies |
| `proctorwise_corrections` | CorrectionService | exam_submissions, answers |
| `proctorwise_notifications` | NotificationService | notifications, preferences |
| `proctorwise_analytics` | AnalyticsService | (tables analytics) |
| `airflow` | Airflow | (metadata, DAG runs, task instances) |

### 6.2 Backup automatise

```bash
# Creer le script de backup
cat > ~/backup-db.sh << 'SCRIPT'
#!/bin/bash
BACKUP_DIR=~/backups/mariadb
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker exec proctorwise-mariadb mysqldump \
  -uproctorwise -pproctorwise_secret \
  --all-databases --single-transaction \
  > "$BACKUP_DIR/backup_$DATE.sql"

# Garder les 7 derniers jours
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup done: backup_$DATE.sql"
SCRIPT
chmod +x ~/backup-db.sh

# Cron : backup tous les jours a 1h00
(crontab -l 2>/dev/null; echo "0 1 * * * ~/backup-db.sh >> ~/backups/backup.log 2>&1") | crontab -
```

### 6.3 Restauration

```bash
# Restaurer un backup
cat ~/backups/mariadb/backup_XXXXXXXX.sql | \
  docker exec -i proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret
```

---

## 7. Securite

### 7.1 Checklist securite prod

- [ ] Changer tous les mots de passe par defaut (DB, Airflow admin/admin, JWT secret)
- [ ] Fichier `.env` avec `chmod 600` (lisible uniquement par le owner)
- [ ] `.env` dans `.gitignore` (ne jamais committer)
- [ ] Firewall UFW actif (ports 22, 80, 443 uniquement)
- [ ] SSL/TLS via Certbot (renouvellement auto)
- [ ] Ports internes non exposes (MariaDB, Kafka, HDFS, Spark)
- [ ] Kafka-UI et Adminer desactives en prod (ou local-only)
- [ ] HDFS : ne pas utiliser permissions 777
- [ ] User non-root pour le serveur
- [ ] SSH par cle (desactiver password auth)

### 7.2 Hardening SSH

```bash
# Generer une cle SSH (sur ta machine locale)
ssh-keygen -t ed25519 -C "proctorwise-vps"
ssh-copy-id proctorwise@IP_DU_VPS

# Desactiver password auth
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

---

## 8. Maintenance & monitoring

### 8.1 Commandes utiles en prod

```bash
# Status de tous les containers
docker compose ps

# Logs d'un service (suivre en temps reel)
docker compose logs -f monitoringservice
docker compose logs -f airflow

# Redemarrer un service
docker compose restart reservationservice

# Rebuild + redemarrer un service
docker compose up -d --build monitoringservice

# Espace disque Docker
docker system df

# Nettoyer les images/containers inutilises
docker system prune -f

# Verifier HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise/processed/
docker exec proctorwise-namenode hdfs dfs -du -h /proctorwise/

# Trigger Airflow manuellement
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline

# Verifier les DAG runs
docker exec proctorwise-airflow airflow dags list-runs -d daily_anomaly_aggregation

# Acces BDD
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret
```

### 8.2 Verifier que Airflow + Spark fonctionnent

```bash
# 1. Verifier que Airflow voit les DAGs
docker exec proctorwise-airflow airflow dags list

# 2. Trigger le pipeline complet manuellement
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline

# 3. Suivre l'execution
docker exec proctorwise-airflow airflow dags list-runs -d full_analytics_pipeline

# 4. Verifier les logs Spark
docker compose logs spark-master
docker compose logs spark-worker

# 5. Verifier la sortie HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise/processed/
```

### 8.3 Monitoring espace disque

```bash
# Script de monitoring
cat > ~/check-disk.sh << 'SCRIPT'
#!/bin/bash
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -gt 85 ]; then
  echo "ALERTE: Disque a ${USAGE}% - nettoyage necessaire"
  docker system prune -f
  find ~/backups/mariadb -name "*.sql" -mtime +3 -delete
fi
SCRIPT
chmod +x ~/check-disk.sh

# Cron : verifier toutes les 6 heures
(crontab -l 2>/dev/null; echo "0 */6 * * * ~/check-disk.sh >> ~/check-disk.log 2>&1") | crontab -
```

### 8.4 Restart auto apres reboot VPS

Docker avec `restart: always` gere ca automatiquement.
Verifier que Docker demarre au boot :

```bash
sudo systemctl enable docker
```

---

## Resume rapide

```
1. Commander VPS OVH Essential (8 GB RAM, 4 vCPU)
2. Installer Docker + Nginx + Git
3. Cloner le repo + creer .env
4. Corriger les 5 bugs critiques (voir section 3)
5. docker compose up -d --build
6. bash scripts/init-hdfs.sh
7. Creer les users de test
8. Configurer DNS + Nginx + SSL
9. Activer le firewall UFW
10. Configurer les backups cron
11. Tester : login → creer examen → passer examen → verifier Airflow
```
