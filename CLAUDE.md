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
| **student** | Reserve exam slots, take exams with timer, view confirmation after submission |
| **teacher** | Create exams, add QCM/True-False questions, view results, consult detailed student submissions |
| **proctor** | Receive anomaly alerts, real-time monitoring |
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
| **monitoringservice/** | 8003 | proctorwise_monitoring | Real-time proctoring with ML anomaly detection |
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

## Exam Flow

### Teacher creates exam with questions:
1. Login as teacher (bob@teacher.com)
2. "Creer examen" tab → Create exam (title, duration)
3. "Gerer questions" tab → Select exam → Add questions (QCM or True/False)
4. "Resultats" tab → Select exam → View student submissions → Click "Details" for full breakdown

### Student takes exam:
1. Login as student (alice@student.com)
2. "Reserver" tab → Select exam → Choose date/time
3. "Mes Reservations" tab → Click "Passer" to start
4. Answer questions (timer counting down)
5. Click "Terminer" → Automatic grading → Confirmation message
6. Reservation status changes to "completed" (cannot retake)

## ReservationService - Data Model

### Exam
- `exam_id`, `title`, `description`, `duration_minutes`, `teacher_id`, `status`

### Question
- `question_id`, `exam_id`, `question_number`, `question_type` (mcq/true_false)
- `question_text`, `option_a`, `option_b`, `option_c`, `option_d`
- `correct_answer`, `points`

### Reservation
- `reservation_id`, `user_id`, `exam_id`, `start_time`, `end_time`, `status`

## Key Endpoints

### ReservationService (8000)
```
POST /exams/                           - Create exam (teacher)
GET  /exams/                           - List all active exams
GET  /exams/{exam_id}                  - Get exam details
GET  /exams/teacher/{teacher_id}       - List teacher's exams
POST /exams/{exam_id}/questions/       - Add question
POST /exams/{exam_id}/questions/bulk   - Add multiple questions
GET  /exams/{exam_id}/questions        - List questions (no answers)
GET  /exams/{exam_id}/questions/with-answers - List with answers (teacher)
POST /reservations/                    - Create reservation
GET  /reservations/user/{user_id}      - List user's reservations
PATCH /reservations/{id}/status?status=X - Update reservation status
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

## Current UI Status

- **UserService**: Web interface OK (login/register with role selection, CORS enabled)
- **ReservationService**: Web interface OK (full exam flow for student/teacher with results view)
- **MonitoringService**: Needs web interface for proctor dashboard
- **CorrectionService**: Backend only (integrated via ReservationService UI for grading + results)
- **NotificationService**: Needs web interface
- **AnalyticsService**: Needs web interface for admin dashboard

## Recent Features

- Timer properly stops when exam is submitted
- Confirmation message after submission (no score alert)
- Reservation marked as "completed" after submission (prevents retake)
- Teacher "Resultats" tab with student submissions list
- Teacher can view detailed breakdown of each student's answers

## Current Tasks

See `TASKS.md` for detailed task breakdown.
