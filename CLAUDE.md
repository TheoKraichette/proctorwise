# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProctorWise is an online exam proctoring platform built with Python microservices. It handles exam slot reservations, real-time proctoring with anomaly detection (hybrid ML/rule-based), grading, notifications, and analytics reporting.

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
| **student** | Reserve exam slots, take exams, view results |
| **teacher** | Create exams, view submissions, grade exams |
| **proctor** | Receive anomaly alerts, real-time monitoring |
| **admin** | Access statistics, manage users and roles |

## Services

| Service | Port | Database | Description |
|---------|------|----------|-------------|
| **userservice/** | 8001 | proctorwise_users | User auth (JWT, bcrypt), roles, redirect after login |
| **reservationservice/** | 8000 | proctorwise_reservations | Exam CRUD + reservation management, role-based UI |
| **monitoringservice/** | 8003 | proctorwise_monitoring | Real-time proctoring with ML anomaly detection |
| **correctionservice/** | 8004 | proctorwise_corrections | Exam grading (auto MCQ + manual) |
| **notificationservice/** | 8005 | proctorwise_notifications | Email (SMTP) and WebSocket notifications |
| **analyticsservice/** | 8006 | proctorwise_analytics | Reports (PDF/CSV), metrics, dashboards |

## Docker Setup

The project runs entirely with Docker Compose. All 17 containers are configured:

```bash
# Start all services
docker compose up -d

# Rebuild a specific service
docker compose up -d --build <service>

# View logs
docker compose logs -f <service>

# Check status
docker compose ps
```

### Container URLs

| Service | URL |
|---------|-----|
| UserService | http://localhost:8001 |
| ReservationService | http://localhost:8000 |
| MonitoringService | http://localhost:8003 |
| CorrectionService | http://localhost:8004 |
| NotificationService | http://localhost:8005 |
| AnalyticsService | http://localhost:8006 |
| Airflow | http://localhost:8082 (admin/admin) |
| Kafka UI | http://localhost:8080 |
| Adminer (DB) | http://localhost:8083 |
| MailHog | http://localhost:8025 |
| HDFS UI | http://localhost:9870 |
| Spark UI | http://localhost:8081 |

## Authentication Flow

1. User registers/logs in at UserService (http://localhost:8001)
2. JWT token generated with: `user_id`, `name`, `email`, `role`, `exp`
3. After login, automatic redirect to ReservationService with token in URL
4. ReservationService parses JWT and shows role-appropriate UI:
   - **Student**: Exam dropdown, reservation form, my reservations
   - **Teacher**: Create exam form, my exams list
   - **Proctor**: Link to MonitoringService
   - **Admin**: Links to Analytics and user management

## Communication

- **REST (FastAPI)** for synchronous operations
- **Kafka** for async events:
  - `exam_scheduled`, `exam_cancelled` (ReservationService)
  - `monitoring_started`, `monitoring_stopped`, `anomaly_detected`, `high_risk_alert` (MonitoringService)
  - `exam_submitted`, `grading_completed`, `manual_review_required` (CorrectionService)
- **WebSocket** for real-time streaming (MonitoringService) and notifications (NotificationService)

## ReservationService - Exam Management

New endpoints for exam CRUD:
- `POST /exams/` - Create exam (teacher)
- `GET /exams/` - List all active exams
- `GET /exams/{exam_id}` - Get exam details
- `GET /exams/teacher/{teacher_id}` - List exams by teacher
- `PUT /exams/{exam_id}` - Update exam
- `DELETE /exams/{exam_id}` - Soft delete exam

## Anomaly Detection (MonitoringService)

Hybrid ML/rule-based detection system:

| Anomaly Type | Method | Severity |
|--------------|--------|----------|
| Face absent >5s | Rule | high |
| Multiple faces | ML + Rule | critical |
| Forbidden object (phone, book, laptop) | ML (YOLO) | high |
| Tab change | Rule | medium |
| Webcam disabled | Rule | critical |

ML Detectors:
- **MediaPipeFaceDetector** - Face detection (used by default)
- **YOLOObjectDetector** - Object detection (cell phone=67, book=73, laptop=63)
- **HybridDetector** - Combines MediaPipe (faces) + YOLO (objects)

## Big Data Stack

### Storage
- **MariaDB** - Single node (proctorwise_* databases)
- **HDFS** - Frame storage, processed reports, ML models

### Processing
- **Apache Spark** - Batch jobs with MySQL JDBC driver
- Jobs in `spark-jobs/batch/`:
  - `daily_anomaly_aggregation.py` - Daily anomaly aggregation (2h AM)
  - `weekly_grade_analytics.py` - Weekly grade statistics (Sunday 3h AM)
  - `monthly_user_performance.py` - Monthly user performance (1st of month 5h AM)

### Orchestration
- **Apache Airflow** - DAGs in `airflow/dags/proctorwise_spark_jobs.py`
- 4 DAGs: daily_anomaly_aggregation, weekly_grade_analytics, monthly_user_performance, full_analytics_pipeline

## Common Commands

```bash
# Docker commands
docker compose up -d                    # Start all
docker compose up -d --build <service>  # Rebuild service
docker compose logs -f <service>        # View logs
docker compose ps                       # Check status

# Database access
docker exec -it proctorwise-mariadb mysql -uproctorwise -pproctorwise_secret

# Kafka topics
docker exec proctorwise-kafka kafka-topics --list --bootstrap-server localhost:9092

# HDFS
docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise

# Airflow
docker exec proctorwise-airflow airflow dags list
docker exec proctorwise-airflow airflow dags trigger full_analytics_pipeline

# Spark job manual execution
docker exec proctorwise-airflow docker exec proctorwise-spark-master \
  /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars/mysql-connector-j-8.0.33.jar \
  /opt/spark-jobs/batch/daily_anomaly_aggregation.py
```

## Key Dependencies

### All Services
- **FastAPI** + **Uvicorn** - Web framework and ASGI server
- **SQLAlchemy** + **pymysql** - ORM and MySQL driver (synchronous)
- **aiokafka** - Async Kafka client
- **Pydantic** - Request/response validation
- **python-jose** - JWT encoding/decoding
- **bcrypt** - Password hashing

### MonitoringService
- **ultralytics** (YOLO) - Object detection
- **mediapipe** - Face detection
- **opencv-python** - Image processing

### NotificationService
- **aiosmtplib** - Async email
- **websockets** - Real-time notifications

### AnalyticsService
- **reportlab** - PDF generation
- **pandas** - Data processing

## HDFS Structure

```
hdfs:///proctorwise/
├── raw/frames/{year}/{month}/{day}/{session_id}/
├── raw/recordings/{exam_id}/{session_id}/
├── processed/anomaly_reports/{year}/{month}/
├── processed/grading_results/{year}/{month}/
├── processed/user_performance/{year}/{month}/
├── ml/models/{model_type}/model_v{version}.pt
└── archive/{year}/{month}/
```

## Development Notes

- Database driver is **pymysql** (synchronous), not aiomysql
- Repository pattern abstracts data access behind interfaces in `application/interfaces/`
- Use cases receive dependencies via constructor injection
- Each service has its own database (database-per-service pattern)
- Feature flags allow local development without full infrastructure (see `.env.example`)

### Current UI Status
- **UserService**: Web interface OK (login/register with role selection)
- **ReservationService**: Web interface OK (role-based views for student/teacher/proctor/admin)
- **MonitoringService**: Needs web interface for proctor dashboard
- **CorrectionService**: Needs web interface for teacher grading + student results
- **NotificationService**: Needs web interface
- **AnalyticsService**: Needs web interface for admin dashboard

## Environment Variables

Key variables in `docker-compose.yml`:

```bash
DATABASE_URL=mysql+pymysql://proctorwise:proctorwise_secret@mariadb:3306/proctorwise_<service>
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
JWT_SECRET_KEY=proctorwise_jwt_secret_change_in_prod
USE_LOCAL_STORAGE=true       # Use local filesystem instead of HDFS
USE_MOCK_SENDERS=true        # Mock email/WebSocket notifications
ENABLE_KAFKA_CONSUMER=true   # Enable Kafka consumer in NotificationService
```

## Current Tasks

See `TASKS.md` for detailed task breakdown including:
- Per-service tasks and status
- Spark jobs testing
- Airflow DAGs status
- ML testing requirements
- Team task distribution (Dev A / Dev B)
