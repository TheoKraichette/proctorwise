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
| **admin** | Access statistics, manage users and roles |

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
| **analyticsservice/** | 8006 | proctorwise_analytics | Reports (PDF/CSV), metrics, dashboards |

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

## Exam Flow

### Teacher creates exam with questions:
1. Login as teacher (bob@teacher.com)
2. "Creer examen" tab -> Create exam (title, duration) + add time slots (creneaux)
3. "Mes examens" tab -> Click "Creneaux" to manage slots (add/remove) for existing exams
4. "Gerer questions" tab -> Select exam -> Add questions (QCM or True/False)
5. "Resultats" tab -> Select exam -> View student submissions -> Click "Details" for full breakdown

### Student takes exam:
1. Login as student (alice@student.com)
2. "Reserver" tab -> Select exam -> Choose from predefined slots (dropdown)
3. "Mes Reservations" tab -> "Passer" button only active during scheduled time slot
   - Before slot: button disabled with "Disponible le [date]"
   - During slot (between start_time and end_time): "Passer" button active
   - After slot: "Creneau expire" message
4. Answer questions (timer counting down)
5. Click "Terminer" -> Automatic grading -> Confirmation message
6. Reservation status changes to "completed" (cannot retake)

### Proctor monitors exams:
1. Login as proctor (charlie@proctor.com)
2. Redirected to MonitoringService dashboard (http://localhost:8003)
3. View active sessions with auto-refresh (10s)
4. Click "Details" to open session modal with anomaly summary
5. WebSocket live feed for real-time anomaly alerts
6. Toast notifications for critical/high severity anomalies
7. "Arreter" button to stop a monitoring session

## ReservationService - Data Model

### Exam
- `exam_id`, `title`, `description`, `duration_minutes`, `teacher_id`, `status`

### ExamSlot
- `slot_id`, `exam_id`, `start_time`, `created_at`
- Teachers define available slots; students pick from them when reserving
- `end_time` is computed at reservation time: `start_time + exam.duration_minutes`

### Question
- `question_id`, `exam_id`, `question_number`, `question_type` (mcq/true_false)
- `question_text`, `option_a`, `option_b`, `option_c`, `option_d`
- `correct_answer`, `points`

### Reservation
- `reservation_id`, `user_id`, `exam_id`, `start_time`, `end_time`, `status`

## MonitoringService - Data Model

### MonitoringSession
- `session_id`, `reservation_id`, `user_id`, `exam_id`, `status`, `started_at`, `stopped_at`, `total_frames_processed`, `anomaly_count`
- DB column `ended_at` maps to Python attr `stopped_at`

### Anomaly
- `anomaly_id`, `session_id`, `anomaly_type`, `severity`, `detection_method`, `confidence`, `detected_at`, `frame_path`, `description`, `metadata`
- DB column `metadata` maps to Python model attr `extra_data`, domain entity uses `metadata`

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
WS   /monitoring/sessions/{id}/stream  - WebSocket real-time stream
```

### CorrectionService (8004)
```
POST /corrections/submissions          - Submit exam answers
POST /corrections/submissions/{id}/grade - Auto-grade submission
GET  /corrections/submissions/{id}/result - Get detailed results
GET  /corrections/submissions/exam/{exam_id} - List submissions by exam
GET  /corrections/submissions/user/{user_id} - List submissions by user
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

## Big Data Stack

- **MariaDB** - Single node (proctorwise_* databases)
- **HDFS** - Frame storage, processed reports
- **Apache Spark** - Batch jobs with MySQL JDBC driver
- **Apache Airflow** - DAGs orchestration

### Spark Jobs
- `daily_anomaly_aggregation.py` - Daily at 2h AM
- `weekly_grade_analytics.py` - Sunday at 3h AM
- `monthly_user_performance.py` - 1st of month at 5h AM

## Common Commands

```bash
# Database access
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret

# Kafka topics
docker exec proctorwise-kafka kafka-topics --list --bootstrap-server localhost:9092

# HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise

# Airflow
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline
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

## Current UI Status

- **UserService**: Web interface OK (login/register with role selection, CORS enabled)
- **ReservationService**: Web interface OK (full exam flow for student/teacher with results view)
- **MonitoringService**: Web interface OK (proctor dashboard with sessions, alerts, WebSocket live feed)
- **CorrectionService**: Backend only (integrated via ReservationService UI for grading + results)
- **NotificationService**: Needs web interface
- **AnalyticsService**: Needs web interface for admin dashboard

## Recent Features

- **Predefined exam slots**: Teachers define time slots when creating an exam; students pick from a dropdown instead of free date picking
- **Slot management**: Teachers can add/remove slots from "Mes examens" tab via a slot manager panel
- **Time-gated exam access**: Students can only start an exam during the reserved time slot (button disabled before/after)
- Monitoring proctor dashboard with stats bar, 3 tabs, session detail modal, WebSocket live feed
- ProcessFrame singleton for persistent face-absent detection across requests
- Kafka producer lifecycle management (startup/shutdown)
- Auto DB table creation on service start
- Timer properly stops when exam is submitted
- Confirmation message after submission (no score alert)
- Reservation marked as "completed" after submission (prevents retake)
- Teacher "Resultats" tab with student submissions list
- Teacher can view detailed breakdown of each student's answers

## Current Tasks

See `TASKS.md` for detailed task breakdown.
