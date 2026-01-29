# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProctorWise is an online exam proctoring platform built with Python microservices. It handles exam creation with questions, slot reservations, exam taking with auto-grading, real-time proctoring with anomaly detection, and analytics reporting.

## Architecture

**Pattern:** Microservices with Clean Architecture (Hexagonal Architecture)

Each microservice follows a 4-layer structure:
- **domain/** - Pure business entities (dataclasses)
- **application/** - Use cases with dependency injection, repository interfaces (ABCs)
- **infrastructure/** - SQLAlchemy repositories, Kafka publishers/consumers, MariaDB connections
- **interface/** - FastAPI controllers, Pydantic request/response schemas

## User Roles

4 roles implemented based on use case diagram:

| Role | Capabilities |
|------|-------------|
| **student** | Reserve predefined exam slots, take exams only at scheduled time, view confirmation after submission |
| **teacher** | Create exams with time slots, manage slots, add QCM/True-False questions, view results, consult detailed student submissions |
| **proctor** | Real-time monitoring dashboard, anomaly alerts, session management |
| **admin** | Access analytics dashboard, statistics, manage users and roles |

## Test Accounts

| Role | Email | Password |
|------|-------|----------|
| Student | alice@student.com | password123 |
| Teacher | bob@teacher.com | password123 |
| Proctor | charlie@proctor.com | password123 |
| Admin | diana@admin.com | password123 |

## Services

| Service | Port | Database | Description |
|---------|------|----------|-------------|
| **userservice/** | 8001 | proctorwise_users | User auth (JWT, bcrypt), roles, redirect after login |
| **reservationservice/** | 8000 | proctorwise_reservations | Exams, Questions, Reservations, role-based UI |
| **monitoringservice/** | 8003 | proctorwise_monitoring | Real-time proctoring with ML anomaly detection, proctor dashboard |
| **correctionservice/** | 8004 | proctorwise_corrections | Exam grading (auto MCQ + manual) |
| **notificationservice/** | 8005 | proctorwise_notifications | Email (SMTP) and WebSocket notifications |
| **analyticsservice/** | 8006 | proctorwise_analytics | Reports (PDF/CSV), metrics, admin dashboard |

## Docker Setup

The project runs entirely with Docker Compose. All 17 containers are configured:

```bash
docker compose up -d                    # Start all
docker compose up -d --build <service>  # Rebuild service
docker compose logs -f <service>        # View logs
docker compose ps                       # Check status
```

## Authentication Flow

1. User registers/logs in at UserService (http://localhost:8001)
2. JWT token generated with: `user_id`, `name`, `email`, `role`, `exp`
3. After login, automatic redirect to ReservationService with token in URL
4. ReservationService parses JWT and shows role-appropriate UI
5. Proctor role links to MonitoringService (http://localhost:8003) with token
6. Admin role links to AnalyticsService (http://localhost:8006) with token

## Exam Flow

### Teacher creates exam with questions:
1. Login as teacher (bob@teacher.com)
2. "Creer examen" tab -> Create exam (title, duration) + add time slots (creneaux)
3. "Mes examens" tab -> Click "Creneaux" to manage slots (add/remove) for existing exams
4. "Gerer questions" tab -> Select exam -> Add questions (QCM or True/False)
5. "Resultats" tab -> Select exam -> View student submissions -> Click "Details" for full breakdown

### Student takes exam (with mandatory webcam monitoring):
1. Login as student (alice@student.com)
2. "Reserver" tab -> Select exam -> Choose from predefined slots (dropdown)
3. "Mes Reservations" tab -> "Passer" button only active during scheduled time slot
   - Before slot: button disabled with "Disponible le [date]"
   - During slot (between start_time and end_time): "Passer" button active
   - After slot: "Creneau expire" message
4. Clicking "Passer" triggers:
   - Monitoring session created (POST to MonitoringService)
   - **Webcam permission requested (MANDATORY)** — if refused, exam is blocked with alert and monitoring session stopped
   - Webcam activated via getUserMedia() (small preview top-right)
   - Frame capture loop starts (every 2 seconds, base64 JPEG sent to monitoring)
   - Tab change detection (visibilitychange event)
   - Webcam disabled detection (track.onended)
5. Answer questions (timer counting down, webcam active in background)
6. Click "Terminer" -> Stop monitoring + stop webcam -> Automatic grading -> Confirmation
7. Reservation status changes to "completed" (cannot retake)

### Proctor monitors exams:
1. Login as proctor (charlie@proctor.com)
2. Redirected to MonitoringService dashboard (http://localhost:8003)
3. View active sessions with auto-refresh (10s) - sessions appear when students start exams
4. Click "Details" to open session modal with anomaly summary
5. **Each anomaly displays the associated webcam frame thumbnail** (click to view fullscreen)
6. Click "Voir en direct" to see live webcam feed via WebSocket
7. WebSocket live feed for real-time anomaly alerts with overlay banners
8. Toast notifications for critical/high severity anomalies
9. "Arreter" button to stop a monitoring session

### Admin views analytics:
1. Login as admin (diana@admin.com)
2. Access AnalyticsService dashboard (http://localhost:8006)
3. View KPIs (users, exams, submissions, sessions, anomalies)
4. View recent submissions and anomalies tables
5. View top performers ranking
6. Export PDF/CSV reports per exam or user

## Data Models

### ReservationService
- **Exam**: exam_id, title, description, duration_minutes, teacher_id, status
- **ExamSlot**: slot_id, exam_id, start_time, created_at (end_time computed: start_time + duration)
- **Question**: question_id, exam_id, question_number, question_type (mcq/true_false), question_text, options, correct_answer, points
- **Reservation**: reservation_id, user_id, exam_id, start_time, end_time, status

### MonitoringService
- **MonitoringSession**: session_id, reservation_id, user_id, exam_id, status, started_at, stopped_at, total_frames_processed, anomaly_count
  - DB column `ended_at` maps to Python attr `stopped_at`
- **Anomaly**: anomaly_id, session_id, anomaly_type, severity, detection_method, confidence, detected_at, frame_path, metadata
  - DB column `metadata` maps to Python model attr `extra_data`, domain entity uses `metadata`

### CorrectionService
- **ExamSubmission**: submission_id, user_id, exam_id, reservation_id, submitted_at, status, total_score, max_score, percentage, graded_at, graded_by
- **Answer**: answer_id, submission_id, question_id, question_type, answer_content, is_correct, score, max_score, feedback

### Key design decisions
- **ProcessFrame is a singleton** in the controller to preserve `_face_absent_start` state across requests
- **Kafka lifecycle** managed via FastAPI lifespan (start on startup, stop on shutdown)
- **DB tables auto-created** via `Base.metadata.create_all()` on startup
- **Frame storage** defaults to `./local_storage` (maps to Docker volume `/app/local_storage`)

## Key Endpoints

### ReservationService (8000)
```
POST /exams/                           - Create exam (teacher)
GET  /exams/                           - List all active exams
GET  /exams/{exam_id}                  - Get exam details
GET  /exams/teacher/{teacher_id}       - List teacher's exams
POST /exams/{exam_id}/slots            - Add a time slot (teacher)
GET  /exams/{exam_id}/slots            - List slots for an exam
DELETE /exams/{exam_id}/slots/{slot_id} - Remove a slot
POST /exams/{exam_id}/questions/       - Add question
POST /exams/{exam_id}/questions/bulk   - Add multiple questions
GET  /exams/{exam_id}/questions        - List questions (no answers)
GET  /exams/{exam_id}/questions/with-answers - List with answers (teacher)
POST /reservations/                    - Create reservation
GET  /reservations/user/{user_id}      - List user's reservations
PATCH /reservations/{id}/status?status=X - Update reservation status
```

### MonitoringService (8003)
```
GET  /monitoring/sessions              - List sessions (?status=active)
POST /monitoring/sessions              - Start monitoring session
GET  /monitoring/sessions/{id}         - Get session details
POST /monitoring/sessions/{id}/frame   - Process frame (base64)
PUT  /monitoring/sessions/{id}/stop    - Stop monitoring session
GET  /monitoring/sessions/{id}/anomalies - List anomalies (?severity=)
GET  /monitoring/sessions/{id}/anomalies/summary - Anomaly summary
GET  /monitoring/frames?path=...       - Serve stored frame image (JPEG)
WS   /monitoring/sessions/{id}/stream  - WebSocket real-time stream (anomaly alerts)
WS   /monitoring/sessions/{id}/live    - WebSocket live video feed (frames + anomalies)
```

### CorrectionService (8004)
```
POST /corrections/submissions          - Submit exam answers
POST /corrections/submissions/{id}/grade - Auto-grade submission
GET  /corrections/submissions/{id}/result - Get detailed results
GET  /corrections/submissions/exam/{exam_id} - List submissions by exam
GET  /corrections/submissions/user/{user_id} - List submissions by user
```

### AnalyticsService (8006)
```
GET  /                                 - Admin dashboard UI (HTML)
GET  /analytics/exams/{exam_id}        - Exam analytics (JSON)
GET  /analytics/exams/{exam_id}/report/pdf - Export PDF
GET  /analytics/exams/{exam_id}/report/csv - Export CSV
GET  /analytics/users/{user_id}        - User analytics (JSON)
GET  /analytics/users/{user_id}/report/pdf - Export PDF
GET  /analytics/users/{user_id}/report/csv - Export CSV
GET  /analytics/platform               - Platform metrics (JSON)
GET  /analytics/dashboards/admin       - Admin dashboard data (JSON)
```

## Anomaly Detection (MonitoringService)

Hybrid ML/rule-based detection system:

| Anomaly Type | Method | Severity |
|--------------|--------|----------|
| Face absent >5s | Rule | high |
| Multiple faces | ML + Rule | critical |
| Forbidden object (phone, book, laptop) | ML (YOLO) | high |
| Tab change | Rule | medium |
| Webcam disabled | Rule | critical |

**YOLO model**: Pre-downloaded at Docker build time (`RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"` in Dockerfile).

## Big Data Stack

- **MariaDB** - Single node, 7 databases (6 services + airflow)
- **HDFS** - NameNode + DataNode, stores Spark output as Parquet
- **Apache Spark** - Master + Worker, batch jobs with MySQL JDBC driver
- **Apache Airflow** - LocalExecutor, 4 DAGs for job orchestration

### Spark Jobs (in `spark-jobs/batch/`)
| Job | Schedule | Input | Output |
|-----|----------|-------|--------|
| `daily_anomaly_aggregation.py` | Daily 2AM | MariaDB monitoring (anomalies + sessions) | HDFS `/proctorwise/processed/anomaly_reports/{year}/{month}/` |
| `weekly_grade_analytics.py` | Sunday 3AM | MariaDB corrections (submissions + answers) | HDFS `/proctorwise/processed/grading_results/{year}/week_{num}/` |
| `monthly_user_performance.py` | 1st of month 5AM | MariaDB corrections + monitoring | HDFS `/proctorwise/processed/user_performance/{year}/{month}/` |

### Airflow DAGs (in `airflow/dags/`)
| DAG | Schedule | Tasks |
|-----|----------|-------|
| `daily_anomaly_aggregation` | `0 2 * * *` | start -> spark_submit -> end |
| `weekly_grade_analytics` | `0 3 * * 0` | start -> spark_submit -> end |
| `monthly_user_performance` | `0 5 1 * *` | start -> spark_submit -> end |
| `full_analytics_pipeline` | Manual | start -> anomaly -> grade -> user -> end |

### Known Big Data Issues
1. **Error masking**: `|| echo` in `spark_submit_cmd()` (DAG file line 33) prevents Airflow from detecting Spark failures. Retries never trigger.
2. **Worker memory mismatch**: Worker has 2g, monthly job asks for 4g executor memory. Job can't allocate.
3. **Data truncation**: `weekly_grade_analytics.py` line 195 limits to 1000 submission IDs.
4. **collect() bottleneck**: `weekly_grade_analytics.py` line 193 loads all IDs into driver memory.
5. **Hardcoded credentials**: All Spark jobs have MariaDB user/password in source code.
6. **No validation tasks**: DAGs don't check pre-conditions (DB up, HDFS writable) or post-conditions (output exists).
7. **No HDFS init DAG**: `init-hdfs.sh` must be run manually.
8. **No retention/cleanup**: Parquet files accumulate indefinitely.
9. **No sync to analytics DB**: Spark results stay in HDFS, not fed into AnalyticsService tables.

### HDFS Structure
```
/proctorwise/
  raw/frames/              (reserved, unused)
  raw/recordings/          (reserved, unused)
  processed/
    anomaly_reports/       (daily Spark output)
    grading_results/       (weekly Spark output)
    user_performance/      (monthly Spark output)
  ml/models/               (reserved for ML models)
  archive/                 (reserved for archival)
```

### Docker Configs
- **Spark** (`docker/spark/Dockerfile`): Apache Spark 3.5.0 + MySQL JDBC connector 8.0.33
- **Airflow** (`docker/airflow/Dockerfile`): Airflow 2.8.0 + Python 3.11 + Docker CLI 27.4.1 + pymysql
- **Airflow executes Spark jobs** via `docker exec proctorwise-spark-master spark-submit ...` (BashOperator)

## Common Commands

```bash
# Database access
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret

# Kafka topics
docker exec proctorwise-kafka kafka-topics --list --bootstrap-server localhost:9092

# HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise

# Init HDFS structure (manual, run once)
bash scripts/init-hdfs.sh

# Airflow
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline
docker exec proctorwise-airflow airflow dags list

# Spark Master UI: http://localhost:8081
# Airflow UI: http://localhost:8082 (admin/admin)
# Kafka UI: http://localhost:8080
# MailHog: http://localhost:8025
# Adminer: http://localhost:8083
```

## Key Dependencies

### All Services
- **FastAPI** + **Uvicorn** - Web framework
- **SQLAlchemy** + **pymysql** - ORM (synchronous)
- **Pydantic** - Validation
- **python-jose** + **bcrypt** - Auth

### MonitoringService
- **ultralytics** (YOLO) - Object detection
- **mediapipe** - Face detection
- **opencv-python** - Image processing
- **aiokafka** - Async Kafka producer

### AnalyticsService
- **reportlab** - PDF generation
- **pandas** - Data processing

## Current UI Status

- **UserService**: Web interface OK (login/register with role selection, CORS enabled)
- **ReservationService**: Web interface OK (full exam flow for student/teacher with results view)
- **MonitoringService**: Web interface OK (proctor dashboard with sessions, alerts, WebSocket live feed, live video viewer)
- **CorrectionService**: Backend only (integrated via ReservationService UI for grading + results)
- **NotificationService**: Web interface OK (notification history, preferences, real-time WebSocket)
- **AnalyticsService**: Web interface OK (admin dashboard with KPIs, tables, export PDF/CSV)

## Current Tasks

See `TASKS.md` for detailed task breakdown. Main focus: Spark/Airflow/HDFS improvements (fix bugs, add validation DAGs, better worker config).

## Recent Changes

- **Webcam mandatory**: Student webcam is now **required** to start an exam — if permission is denied, exam is blocked and monitoring session stopped
- **Proctor frame viewing**: Anomaly list in proctor dashboard now displays the associated webcam frame thumbnail with fullscreen overlay on click
- **Frame serving endpoint**: New `GET /monitoring/frames?path=...` endpoint serves stored frame images as JPEG
- **Airflow DB init fix**: Startup command uses `(airflow db migrate || airflow db init)` fallback for fresh databases
- **Webcam integration**: Student webcam activates during exams, frames sent to MonitoringService every 2s
- **Live video viewer**: Proctor can watch student webcam in real-time via WebSocket
- **Browser event detection**: Tab change and webcam disabled detected and sent as anomalies
- **YOLO pre-download**: Model downloaded at Docker build time (no more missing .pt files)
- **MediaPipe pinned**: Version 0.10.14 for stability
- **DB schema update**: Added questions, exam_slots tables, description column on anomalies, 'stopped' status
- **Browser events without frame**: MonitoringService handles browser-only events (no image required)
