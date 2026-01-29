# ProctorWise - Architecture & Workflow Complet

---

## 1. Vue d'ensemble : Qui fait quoi ?

```
  ENSEIGNANT (Bob)         ETUDIANT (Alice)        SURVEILLANT (Charlie)      ADMIN (Diana)
       │                        │                        │                        │
       │  Cree examens          │  Reserve un creneau    │  Surveille en          │  Consulte
       │  Ajoute questions      │  Passe l'examen        │  temps reel            │  les stats
       │  Gere creneaux         │  Webcam OBLIGATOIRE    │  Voit les anomalies    │  Exporte
       │  Voit resultats        │  Repond aux questions  │  Voit les frames       │  PDF / CSV
       │                        │                        │                        │
       ▼                        ▼                        ▼                        ▼
  ┌─────────┐            ┌─────────┐              ┌─────────┐            ┌─────────────┐
  │  http:  │            │  http:  │              │  http:  │            │   http:     │
  │  :8001  │            │  :8001  │              │  :8001  │            │   :8001     │
  │  Login  │            │  Login  │              │  Login  │            │   Login     │
  └────┬────┘            └────┬────┘              └────┬────┘            └──────┬──────┘
       │                      │                        │                       │
       ▼                      ▼                        ▼                       ▼
  ┌─────────┐            ┌─────────┐              ┌──────────┐          ┌─────────────┐
  │  :8000  │            │  :8000  │              │  :8003   │          │   :8006     │
  │ Reserv. │            │ Reserv. │              │ Monitor. │          │  Analytics  │
  │ Service │            │ Service │              │ Service  │          │  Service    │
  └─────────┘            └─────────┘              └──────────┘          └─────────────┘
```

---

## 2. Flux complet : De la creation d'examen au rapport

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                        PHASE 1 : PREPARATION (Enseignant)                       ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

  Bob (teacher)
     │
     │ 1. Login (UserService :8001)
     │    → JWT token genere {user_id, name, role:"teacher"}
     │    → Redirect vers ReservationService :8000
     │
     │ 2. Creer un examen
     │    POST /exams/ {title, duration, teacher_id}
     │
     │ 3. Ajouter des creneaux horaires
     │    POST /exams/{id}/slots {start_time}
     │    (end_time = start_time + duration)
     │
     │ 4. Ajouter des questions
     │    POST /exams/{id}/questions/bulk
     │    {questions: [{type:"mcq", text, options, correct_answer, points}, ...]}
     │
     ▼
  ┌──────────────────────────┐         ┌──────────────────────────────────┐
  │   ReservationService     │────────►│          MariaDB                 │
  │        (:8000)           │         │   proctorwise_reservations       │
  └──────────────────────────┘         │                                  │
                                       │  exams ─── exam_slots            │
                                       │    └── questions                  │
                                       │    └── reservations               │
                                       └──────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════════════╗
║                    PHASE 2 : PASSAGE D'EXAMEN (Etudiant)                        ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

  Alice (student)
     │
     │ 1. Login → Redirect :8000
     │
     │ 2. Reserver un creneau
     │    POST /reservations/ {user_id, exam_id, start_time, end_time}
     │
     │ 3. Cliquer "Passer" (seulement pendant le creneau)
     │    │
     │    ├──► POST :8003/monitoring/sessions
     │    │    → Cree une session de monitoring
     │    │
     │    ├──► Demande acces webcam (OBLIGATOIRE)
     │    │    ✓ Accepte → examen demarre
     │    │    ✗ Refuse  → BLOQUE, alerte, retour vue etudiante
     │    │
     │    │   ┌─────────────────────────────────────────────────────────┐
     │    │   │              PENDANT L'EXAMEN                          │
     │    │   │                                                         │
     │    │   │  [Timer]  Decompte minutes restantes                   │
     │    │   │                                                         │
     │    │   │  [Webcam]  Capture frame toutes les 2 secondes         │
     │    │   │     │                                                   │
     │    │   │     └──► POST :8003/sessions/{id}/frame                │
     │    │   │          {frame_data: base64 JPEG, frame_number}       │
     │    │   │              │                                          │
     │    │   │              ▼                                          │
     │    │   │     ┌─────────────────────┐                            │
     │    │   │     │  MonitoringService  │                            │
     │    │   │     │                     │                            │
     │    │   │     │  1. Sauvegarde frame│──► local_storage/          │
     │    │   │     │     (JPEG sur disk) │    {year}/{month}/{day}/   │
     │    │   │     │                     │    {session}/frame_XXX.jpg │
     │    │   │     │  2. Analyse YOLO    │                            │
     │    │   │     │     → telephone ?   │                            │
     │    │   │     │     → livre ?       │                            │
     │    │   │     │     → laptop ?      │                            │
     │    │   │     │                     │                            │
     │    │   │     │  3. Analyse Face    │                            │
     │    │   │     │     (MediaPipe)     │                            │
     │    │   │     │     → absent >5s ?  │                            │
     │    │   │     │     → plusieurs ?   │                            │
     │    │   │     │                     │                            │
     │    │   │     │  4. Si anomalie     │──► MariaDB (anomalies)    │
     │    │   │     │     detectee :      │──► Kafka (event)          │
     │    │   │     │     → sauvegarde    │──► WebSocket (proctor)    │
     │    │   │     └─────────────────────┘                            │
     │    │   │                                                         │
     │    │   │  [Tab change] → envoie event "tab_change"              │
     │    │   │  [Webcam off] → envoie event "webcam_disabled"         │
     │    │   │                                                         │
     │    │   └─────────────────────────────────────────────────────────┘
     │    │
     │    │ 4. Cliquer "Terminer"
     │    │
     │    ├──► PUT :8003/sessions/{id}/stop
     │    │    → Arrete le monitoring
     │    │
     │    ├──► POST :8004/corrections/submissions
     │    │    {user_id, exam_id, answers: [{question_id, answer}, ...]}
     │    │
     │    └──► POST :8004/corrections/submissions/{id}/grade
     │         → Correction automatique QCM + Vrai/Faux
     │         → Score calcule, resultat sauvegarde
     │
     ▼
  ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ ReservationService│      │ CorrectionService│      │ MonitoringService│
  │ reservation:      │      │ exam_submissions │      │ sessions         │
  │ status=completed  │      │ answers          │      │ anomalies        │
  └──────────────────┘      └──────────────────┘      └──────────────────┘


╔═══════════════════════════════════════════════════════════════════════════════════╗
║                    PHASE 3 : SURVEILLANCE (Surveillant)                          ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

  Charlie (proctor) → :8003 Dashboard
     │
     │  ┌──────────────────────────────────────────────────────────────┐
     │  │                  DASHBOARD PROCTOR                           │
     │  │                                                              │
     │  │  ┌─────────────────────────────────────────────────────┐    │
     │  │  │ Stats: 3 actives | 12 total | 47 anomalies | 5 crit│    │
     │  │  └─────────────────────────────────────────────────────┘    │
     │  │                                                              │
     │  │  [Sessions actives]  (auto-refresh 10s)                     │
     │  │  ┌──────────┬────────┬────────┬──────────┬─────────┐       │
     │  │  │ Session  │ Exam   │ User   │ Anomalies│ Actions │       │
     │  │  │ abc-123  │ Maths  │ Alice  │ 5        │ Details │       │
     │  │  │ def-456  │ Python │ Marc   │ 2        │ Details │       │
     │  │  └──────────┴────────┴────────┴──────────┴─────────┘       │
     │  │                                                              │
     │  │  [Clic "Details"]                                            │
     │  │  ┌──────────────────────────────────────────────────┐       │
     │  │  │ Modal Session abc-123                            │       │
     │  │  │                                                  │       │
     │  │  │ Resume: 2 critical, 1 high, 2 medium            │       │
     │  │  │                                                  │       │
     │  │  │ Anomalie 1: [CRITICAL] multiple_faces            │       │
     │  │  │ ┌──────────────────────┐                         │       │
     │  │  │ │ 📷 Frame webcam     │  ← NOUVEAU : thumbnail  │       │
     │  │  │ │ (clic = fullscreen) │  GET /monitoring/frames  │       │
     │  │  │ └──────────────────────┘                         │       │
     │  │  │                                                  │       │
     │  │  │ Anomalie 2: [HIGH] forbidden_object (phone)      │       │
     │  │  │ ┌──────────────────────┐                         │       │
     │  │  │ │ 📷 Frame webcam     │                          │       │
     │  │  │ └──────────────────────┘                         │       │
     │  │  │                                                  │       │
     │  │  │ [Voir en direct]  ← WebSocket live video feed   │       │
     │  │  │ [Arreter]         ← Stop session                │       │
     │  │  └──────────────────────────────────────────────────┘       │
     │  │                                                              │
     │  │  [Toast notifications]  Anomalie critique detectee !        │
     │  │                                                              │
     │  └──────────────────────────────────────────────────────────────┘
     │
     │  Flux temps reel :
     │
     │  MonitoringService ──WebSocket──► Dashboard proctor
     │       │                               │
     │       │  frame + anomalies            │  Affiche frame live
     │       │  en temps reel                │  + overlay anomalies
     │       ▼                               ▼
```


## 3. Pipeline Big Data : Airflow orchestre Spark vers HDFS

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                        PIPELINE BIG DATA                                        ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

                           ┌─────────────────────┐
                           │     AIRFLOW          │
                           │    (:8082)           │
                           │                     │
                           │  8 DAGs configures   │
                           └──────────┬──────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │   DAG Daily      │  │   DAG Weekly     │  │   DAG Monthly    │
   │   (2h00)         │  │   (Dim 3h00)     │  │   (1er 5h00)     │
   │                  │  │                  │  │                  │
   │  Anomalies par   │  │  Stats notes     │  │  Performance     │
   │  exam/user/heure │  │  par examen      │  │  utilisateurs    │
   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
            │                     │                      │
            │    Airflow execute : docker exec spark-master spark-submit ...
            │                     │                      │
            ▼                     ▼                      ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │                    SPARK CLUSTER                              │
   │                                                              │
   │   ┌──────────────┐         ┌──────────────────────┐         │
   │   │ Spark Master │────────►│    Spark Worker      │         │
   │   │   (:7077)    │         │  2 cores / 2 GB RAM  │         │
   │   └──────────────┘         └──────────┬───────────┘         │
   │                                        │                     │
   │                            ┌───────────┼───────────┐        │
   │                            │           │           │        │
   │                            ▼           ▼           ▼        │
   │                       ┌────────┐ ┌────────┐ ┌────────┐     │
   │           Lit via     │ Job 1  │ │ Job 2  │ │ Job 3  │     │
   │           JDBC ──────►│Anomaly │ │ Grade  │ │ User   │     │
   │                       │Aggreg. │ │Analyt. │ │Perform.│     │
   │                       └───┬────┘ └───┬────┘ └───┬────┘     │
   │                           │          │          │           │
   └───────────────────────────┼──────────┼──────────┼───────────┘
                               │          │          │
       ┌───────────────────────┘          │          └───────────────────┐
       │                                  │                              │
       ▼                                  ▼                              ▼
  ┌──────────┐                     ┌──────────┐                   ┌──────────┐
  │ MariaDB  │                     │ MariaDB  │                   │ MariaDB  │
  │monitoring│                     │corrections│                  │correct.+ │
  │          │                     │          │                   │monitori. │
  │sessions +│ ◄── Lecture via     │submissio.│                   │          │
  │anomalies │     JDBC            │+ answers │                   │          │
  └──────────┘                     └──────────┘                   └──────────┘
       │                                │                              │
       │         Spark ecrit les resultats en Parquet                  │
       │                                │                              │
       ▼                                ▼                              ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                                                                        │
  │                          HDFS (Hadoop)                                 │
  │                  hdfs://namenode:9000                                  │
  │                                                                        │
  │   NameNode (:9870) ──────► DataNode                                   │
  │                                                                        │
  │   /proctorwise/processed/                                              │
  │   │                                                                    │
  │   ├── anomaly_reports/           ◄── Job 1 (Daily)                    │
  │   │   └── 2026/01/                                                     │
  │   │       ├── by_exam/29/        Anomalies par examen (parquet)       │
  │   │       ├── by_user/29/        Anomalies par user (parquet)         │
  │   │       └── hourly/29/         Anomalies par heure (parquet)        │
  │   │                                                                    │
  │   ├── grading_results/           ◄── Job 2 (Weekly)                   │
  │   │   └── 2026/week_04/                                                │
  │   │       ├── exam_statistics/   Stats par examen (parquet)           │
  │   │       ├── question_difficulty/ Difficulte questions (parquet)     │
  │   │       ├── daily_trends/      Tendances journalieres (parquet)     │
  │   │       └── grading_efficiency/ Efficacite correction (parquet)     │
  │   │                                                                    │
  │   └── user_performance/          ◄── Job 3 (Monthly)                  │
  │       └── 2026/01/                                                     │
  │           ├── user_profiles/     Profils complets (parquet)           │
  │           ├── top_performers/    Top 100 etudiants (parquet)          │
  │           ├── at_risk_users/     Etudiants a risque (parquet)         │
  │           ├── most_improved/     Plus ameliores (parquet)             │
  │           ├── tier_summary/      Repartition niveaux (parquet)        │
  │           └── risk_summary/      Repartition risques (parquet)        │
  │                                                                        │
  └────────────────────────────────────────────────────────────────────────┘
```


## 4. DAGs Airflow : Planning complet

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                     TOUS LES DAGS AIRFLOW (8 au total)                          ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

  ──── SPARK ANALYTICS (4 DAGs) ──────────────────────────────────────────────────

  daily_anomaly_aggregation          Tous les jours a 2h00
  ┌───────┐    ┌───────────────────┐    ┌─────┐
  │ start │───►│ spark-submit      │───►│ end │
  └───────┘    │ daily_anomaly_    │    └─────┘
               │ aggregation.py    │
               └───────────────────┘

  weekly_grade_analytics             Dimanche a 3h00
  ┌───────┐    ┌───────────────────┐    ┌─────┐
  │ start │───►│ spark-submit      │───►│ end │
  └───────┘    │ weekly_grade_     │    └─────┘
               │ analytics.py      │
               └───────────────────┘

  monthly_user_performance           1er du mois a 5h00
  ┌───────┐    ┌───────────────────┐    ┌─────┐
  │ start │───►│ spark-submit      │───►│ end │
  └───────┘    │ monthly_user_     │    └─────┘
               │ performance.py    │
               └───────────────────┘

  full_analytics_pipeline            MANUEL uniquement
  ┌───────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────┐
  │ start │───►│ anomaly  │───►│  grade   │───►│   user   │───►│ end │
  └───────┘    │   job    │    │   job    │    │   job    │    └─────┘
               └──────────┘    └──────────┘    └──────────┘

  ──── MAINTENANCE (4 DAGs) ──────────────────────────────────────────────────────

  daily_mariadb_backup               Tous les jours a 1h00
  ┌───────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────┐
  │ start │───►│ mysqldump    │───►│ cleanup backups  │───►│ end │
  └───────┘    │ all databases│    │ older than 7 days│    └─────┘
               └──────────────┘    └─────────────────┘

  weekly_hdfs_cleanup                Dimanche a 4h00
  ┌───────┐    ┌──────────┐    ┌──────────────────┐    ┌─────┐
  │ start │───►│ check    │───►│ cleanup anomaly  │───►│ end │
  └───────┘    │ hdfs     │    │ reports >90 days │    └─────┘
               │ usage    │    │ + grading >6 mois│
               └──────────┘    └──────────────────┘

  system_health_check                Toutes les 6 heures
  ┌───────┐    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐    ┌─────┐
  │ start │───►│ disk     │ │containers│ │ services │ │ hdfs │───►│ end │
  └───────┘    │ space    │ │ health   │ │ HTTP 200 │ │health│    └─────┘
               └──────────┘ └──────────┘ └──────────┘ └──────┘
                        (en parallele)

  init_hdfs_structure                MANUEL (une seule fois)
  ┌───────┐    ┌──────────────┐    ┌──────────────────┐    ┌─────┐
  │ start │───►│ wait HDFS    │───►│ create all dirs   │───►│ end │
  └───────┘    │ safe mode OFF│    │ + chmod 755       │    └─────┘
               └──────────────┘    └──────────────────┘


  ──── TIMELINE JOURNALIERE ──────────────────────────────────────────────────────

  00h    01h    02h    03h    04h    05h    06h   ...  12h   ...  18h   ...
   │      │      │      │      │      │      │         │         │
   │      │      │      │      │      │      │         │         │
   │   BACKUP  ANOMALY  │      │   MONTHLY  HEALTH    HEALTH   HEALTH
   │    BDD    SPARK    │      │   SPARK    CHECK     CHECK    CHECK
   │      │      │      │      │   (1er)     │         │         │
   │      │      │    WEEKLY   │      │      │         │         │
   │      │      │    SPARK   WEEKLY  │      │         │         │
   │      │      │   (dim)    HDFS    │      │         │         │
   │      │      │    (dim)  CLEANUP  │      │         │         │
   │      │      │            (dim)   │      │         │         │
```


## 5. Infrastructure Docker : Les 17 containers

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                     17 CONTAINERS DOCKER                                        ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                        RESEAU : proctorwise (bridge)                       │
  │                                                                             │
  │  ┌─── MICROSERVICES (6) ──────────────────────────────────────────────┐    │
  │  │                                                                     │    │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    │
  │  │  │ UserService  │  │ Reservation  │  │ Monitoring   │             │    │
  │  │  │    :8001     │  │   :8000      │  │   :8003      │             │    │
  │  │  │  Login/JWT   │  │ Exams/Slots  │  │ YOLO/Face    │             │    │
  │  │  └──────────────┘  └──────────────┘  │ WebSocket    │             │    │
  │  │                                       │ Frames       │             │    │
  │  │  ┌──────────────┐  ┌──────────────┐  └──────────────┘             │    │
  │  │  │ Correction   │  │ Notification │  ┌──────────────┐             │    │
  │  │  │   :8004      │  │   :8005      │  │ Analytics    │             │    │
  │  │  │ Auto-grading │  │ Email/WS     │  │   :8006      │             │    │
  │  │  └──────────────┘  └──────────────┘  │ Dashboard    │             │    │
  │  │                                       │ PDF/CSV      │             │    │
  │  │                                       └──────────────┘             │    │
  │  └─────────────────────────────────────────────────────────────────────┘    │
  │                                                                             │
  │  ┌─── DATA & STREAMING (5) ───────────────────────────────────────────┐    │
  │  │                                                                     │    │
  │  │  ┌──────────────────────┐  ┌─────────────┐  ┌─────────────┐       │    │
  │  │  │      MariaDB         │  │  Zookeeper  │  │    Kafka    │       │    │
  │  │  │      :3306           │  │   :2181     │  │    :9092    │       │    │
  │  │  │                      │  └──────┬──────┘  └──────┬──────┘       │    │
  │  │  │  7 bases de donnees: │         │    coordonne    │              │    │
  │  │  │  - users             │         └────────────────►│              │    │
  │  │  │  - reservations      │                                          │    │
  │  │  │  - monitoring        │  ┌─────────────┐  ┌─────────────┐       │    │
  │  │  │  - corrections       │  │  NameNode   │  │  DataNode   │       │    │
  │  │  │  - notifications     │  │ :9870/:9000 │  │  (stockage) │       │    │
  │  │  │  - analytics         │  │   HDFS      │──│   blocs     │       │    │
  │  │  │  - airflow           │  └─────────────┘  └─────────────┘       │    │
  │  │  └──────────────────────┘                                          │    │
  │  └─────────────────────────────────────────────────────────────────────┘    │
  │                                                                             │
  │  ┌─── PROCESSING & ORCHESTRATION (3) ─────────────────────────────────┐    │
  │  │                                                                     │    │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐     │    │
  │  │  │ Spark Master │  │ Spark Worker │  │      Airflow         │     │    │
  │  │  │   :7077      │──│ 2 cores/2GB  │  │      :8082           │     │    │
  │  │  │              │  │              │  │                      │     │    │
  │  │  │  Coordonne   │  │  Execute les │  │  Orchestre tout :    │     │    │
  │  │  │  les jobs    │  │  jobs Spark  │  │  - 4 DAGs Spark     │     │    │
  │  │  │              │  │              │  │  - 4 DAGs Maint.    │     │    │
  │  │  └──────────────┘  └──────────────┘  │                      │     │    │
  │  │                                       │  Execute via :       │     │    │
  │  │                                       │  docker exec         │     │    │
  │  │                                       │  spark-master        │     │    │
  │  │                                       │  spark-submit ...    │     │    │
  │  │                                       └──────────────────────┘     │    │
  │  └─────────────────────────────────────────────────────────────────────┘    │
  │                                                                             │
  │  ┌─── OUTILS (3) ────────────────────────────────────────────────────┐     │
  │  │                                                                    │     │
  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │     │
  │  │  │  Kafka UI    │  │   MailHog    │  │   Adminer    │            │     │
  │  │  │   :8080      │  │ :1025/:8025  │  │    :8083     │            │     │
  │  │  │ Debug topics │  │ Fake SMTP    │  │ DB explorer  │            │     │
  │  │  └──────────────┘  └──────────────┘  └──────────────┘            │     │
  │  └────────────────────────────────────────────────────────────────────┘     │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘
```


## 6. Deploiement VPS (production)

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                        VPS OVH (Production)                                     ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

   Internet
      │
      │ HTTPS (port 443)
      │
      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                           NGINX (Reverse Proxy)                         │
  │                                                                          │
  │   proctorwise.domaine.fr      ──────►  localhost:8001 (UserService)     │
  │   app.proctorwise.domaine.fr  ──────►  localhost:8000 (Reservation)     │
  │   monitor.proctorwise.domaine.fr ───►  localhost:8003 (Monitoring+WS)   │
  │   analytics.proctorwise.domaine.fr ─►  localhost:8006 (Analytics)       │
  │   airflow.proctorwise.domaine.fr  ──►  localhost:8082 (Airflow UI)      │
  │                                                                          │
  │   SSL/TLS : Certbot (Let's Encrypt, renouvellement auto)               │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘
      │
      │ Ports internes seulement (pas exposes)
      │
      ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                        DOCKER COMPOSE (17 containers)                    │
  │                                                                          │
  │   Voir section 5 ci-dessus                                              │
  │                                                                          │
  │   Ports internes NON exposes sur Internet :                             │
  │   - MariaDB :3306                                                        │
  │   - Kafka :9092                                                          │
  │   - HDFS :9870 / :9000                                                   │
  │   - Spark :7077                                                          │
  │   - Zookeeper :2181                                                      │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘
      │
      │
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                           FIREWALL (UFW)                                 │
  │                                                                          │
  │   OUVERT :  22 (SSH)  |  80 (HTTP→HTTPS)  |  443 (HTTPS)               │
  │   FERME  :  Tout le reste                                                │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘
```


## 7. Flux des donnees : Vue complete

```
  ETUDIANT                                                          PROCTOR
  passe examen                                                      surveille
      │                                                                 ▲
      │                                                                 │
      ▼                                                                 │
  ReservationService ───► CorrectionService ───► MariaDB            WebSocket
  (reponses)              (auto-grading)         corrections       temps reel
      │                                              │                  │
      │                                              │                  │
      └──► MonitoringService ───► MariaDB            │           MonitoringService
           (frames webcam)        monitoring          │           (dashboard)
           (YOLO + Face)              │               │                 │
                │                     │               │                 │
                └──► Kafka ──► NotificationService    │                 │
                     (events)  (email alerts)         │                 │
                                                      │                 │
                                                      ▼                 │
  ┌──────────────────────────────────────────────────────────────────────┘
  │
  │  NUIT : Airflow declenche Spark
  │
  │  ┌──────────┐     ┌───────────┐     ┌──────────┐
  │  │ MariaDB  │────►│   Spark   │────►│   HDFS   │
  │  │monitoring│     │ (3 jobs)  │     │ (parquet) │
  │  │corrections│    └───────────┘     └──────────┘
  │  └──────────┘
  │
  │  JOUR : Admin consulte les resultats
  │
  │  ┌──────────────┐
  └─►│ Analytics    │ ◄── Admin (Diana)
     │ Service      │     Dashboard + Export PDF/CSV
     │ (:8006)      │
     └──────────────┘
```
