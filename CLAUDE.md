# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProctorWise is an online exam proctoring platform built with Python microservices. It handles exam slot reservations, real-time proctoring with anomaly detection (hybrid ML/rule-based), grading, notifications, and analytics reporting.

## Architecture

**Pattern:** Microservices with Clean Architecture (Hexagonal Architecture)

Each microservice follows a 4-layer structure:
- **domain/** - Pure business entities (dataclasses)
- **application/** - Use cases with dependency injection, repository interfaces (ABCs)
- **infrastructure/** - SQLAlchemy repositories, Kafka publishers/consumers, MariaDB Galera connections
- **interface/** - FastAPI controllers, Pydantic request/response schemas

## Services

| Service | Port | Database | Description |
|---------|------|----------|-------------|
| **userservice/** | 8001 | proctorwise_users | User registration and authentication (JWT, bcrypt) |
| **reservationservice/** | 8000 | proctorwise_reservations | Exam reservation management with Kafka events |
| **monitoringservice/** | 8003 | proctorwise_monitoring | Real-time proctoring with ML anomaly detection (YOLO/MediaPipe) |
| **correctionservice/** | 8004 | proctorwise_corrections | Exam grading (auto MCQ + manual essays) |
| **notificationservice/** | 8005 | proctorwise_notifications | Email (SMTP) and WebSocket notifications |
| **analyticsservice/** | 8006 | proctorwise_analytics | Reports (PDF/CSV), metrics, dashboards |

## Communication

- **REST (FastAPI)** for synchronous operations
- **Kafka** for async events:
  - `exam_scheduled`, `exam_cancelled` (ReservationService)
  - `monitoring_started`, `monitoring_stopped`, `anomaly_detected`, `high_risk_alert` (MonitoringService)
  - `exam_submitted`, `grading_completed`, `manual_review_required` (CorrectionService)
- **WebSocket** for real-time streaming (MonitoringService) and notifications (NotificationService)

## Anomaly Detection (MonitoringService)

Hybrid ML/rule-based detection system:

| Anomaly Type | Method | Severity |
|--------------|--------|----------|
| Face absent >5s | Rule | high |
| Multiple faces | ML + Rule | critical |
| Forbidden object (phone) | ML (YOLO) | high |
| Tab change | Rule | medium |
| Webcam disabled | Rule | critical |

## Big Data Stack

### Storage
- **MariaDB Galera** - 3 nodes, synchronous multi-master replication
- **HDFS** - Frame storage, processed reports, ML models

### Processing
- **Apache Spark** - Batch jobs in `spark-jobs/batch/`:
  - `daily_anomaly_aggregation.py` - Daily anomaly aggregation (2h AM)
  - `weekly_grade_analytics.py` - Weekly grade statistics (Sunday)
  - `monthly_user_performance.py` - Monthly user performance (1st of month)

### Orchestration
- **Apache Airflow** - Workflow orchestration (DAGs to be implemented)

## Common Commands

```bash
# Install dependencies (per service)
pip install -r userservice/requirements.txt
pip install -r reservationservice/requirements.txt
pip install -r monitoringservice/requirements.txt
pip install -r correctionservice/requirements.txt
pip install -r notificationservice/requirements.txt
pip install -r analyticsservice/requirements.txt

# Run services individually
uvicorn userservice.main:app --reload --port 8001
uvicorn reservationservice.main:app --reload --port 8000
uvicorn monitoringservice.main:app --reload --port 8003
uvicorn correctionservice.main:app --reload --port 8004
uvicorn notificationservice.main:app --reload --port 8005
uvicorn analyticsservice.main:app --reload --port 8006

# Database migrations (run from service directory)
alembic upgrade head
alembic revision --autogenerate -m "description"

# Submit Spark job
spark-submit --master spark://spark-master:7077 spark-jobs/batch/daily_anomaly_aggregation.py
```

## Key Dependencies

### All Services
- **FastAPI** + **Uvicorn** - Web framework and ASGI server
- **SQLAlchemy** + **aiomysql** - Async ORM and MySQL driver
- **aiokafka** - Async Kafka client
- **Pydantic** - Request/response validation

### MonitoringService
- **ultralytics** (YOLO) - Object detection
- **mediapipe** - Face detection
- **opencv-python** - Image processing
- **hdfs** - HDFS client

### NotificationService
- **aiosmtplib** - Async email
- **jinja2** - Email templates
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
├── ml/models/{model_type}/model_v{version}.pt
└── archive/{year}/{month}/
```

## Development Notes

- All database and Kafka operations are async-ready
- Repository pattern abstracts data access behind interfaces in `application/interfaces/`
- Use cases receive dependencies via constructor injection
- Each service has its own database (database-per-service pattern)
- Feature flags allow local development without full infrastructure (see `.env.example`)

## Environment Variables

See `.env.example` for full configuration. Key variables:

```bash
# Feature flags for local development
USE_LOCAL_STORAGE=false    # Use local filesystem instead of HDFS
USE_MOCK_SENDERS=true      # Mock email/WebSocket notifications
ENABLE_KAFKA_CONSUMER=false
```
