-- Script d'initialisation des bases de données MariaDB
-- Exécuté automatiquement au premier démarrage du conteneur

-- Création des bases de données pour chaque microservice
CREATE DATABASE IF NOT EXISTS proctorwise_users CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS proctorwise_reservations CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS proctorwise_monitoring CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS proctorwise_corrections CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS proctorwise_notifications CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS proctorwise_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Base de données Airflow
CREATE DATABASE IF NOT EXISTS airflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Création de l'utilisateur applicatif avec tous les privilèges sur les bases
CREATE USER IF NOT EXISTS 'proctorwise'@'%' IDENTIFIED BY 'proctorwise_secret';

-- Attribution des privilèges
GRANT ALL PRIVILEGES ON proctorwise_users.* TO 'proctorwise'@'%';
GRANT ALL PRIVILEGES ON proctorwise_reservations.* TO 'proctorwise'@'%';
GRANT ALL PRIVILEGES ON proctorwise_monitoring.* TO 'proctorwise'@'%';
GRANT ALL PRIVILEGES ON proctorwise_corrections.* TO 'proctorwise'@'%';
GRANT ALL PRIVILEGES ON proctorwise_notifications.* TO 'proctorwise'@'%';
GRANT ALL PRIVILEGES ON proctorwise_analytics.* TO 'proctorwise'@'%';
GRANT ALL PRIVILEGES ON airflow.* TO 'proctorwise'@'%';

FLUSH PRIVILEGES;

-- ============================================================================
-- TABLES POUR USERSERVICE (proctorwise_users)
-- ============================================================================
USE proctorwise_users;

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('student', 'teacher', 'admin', 'proctor') NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- ============================================================================
-- TABLES POUR RESERVATIONSERVICE (proctorwise_reservations)
-- ============================================================================
USE proctorwise_reservations;

CREATE TABLE IF NOT EXISTS exams (
    exam_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INT NOT NULL DEFAULT 60,
    teacher_id VARCHAR(36) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_teacher_id (teacher_id)
);

CREATE TABLE IF NOT EXISTS questions (
    question_id VARCHAR(36) PRIMARY KEY,
    exam_id VARCHAR(36) NOT NULL,
    question_number INT NOT NULL,
    question_type VARCHAR(20) NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(500),
    option_b VARCHAR(500),
    option_c VARCHAR(500),
    option_d VARCHAR(500),
    correct_answer VARCHAR(500) NOT NULL,
    points FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_exam_id (exam_id)
);

CREATE TABLE IF NOT EXISTS exam_slots (
    slot_id VARCHAR(36) PRIMARY KEY,
    exam_id VARCHAR(36) NOT NULL,
    start_time DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_exam_id (exam_id)
);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    exam_id VARCHAR(36) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_exam_id (exam_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
);

-- ============================================================================
-- TABLES POUR MONITORINGSERVICE (proctorwise_monitoring)
-- ============================================================================
USE proctorwise_monitoring;

CREATE TABLE IF NOT EXISTS monitoring_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    reservation_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    exam_id VARCHAR(36) NOT NULL,
    status ENUM('active', 'paused', 'completed', 'terminated', 'stopped') NOT NULL DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    total_frames_processed INT DEFAULT 0,
    anomaly_count INT DEFAULT 0,
    INDEX idx_reservation_id (reservation_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
);

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    anomaly_type ENUM('face_absent', 'multiple_faces', 'forbidden_object', 'tab_change', 'webcam_disabled') NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    detection_method ENUM('rule', 'ml', 'hybrid') NOT NULL,
    confidence FLOAT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    frame_path VARCHAR(512),
    description TEXT,
    metadata JSON,
    INDEX idx_session_id (session_id),
    INDEX idx_anomaly_type (anomaly_type),
    INDEX idx_severity (severity),
    INDEX idx_detected_at (detected_at),
    FOREIGN KEY (session_id) REFERENCES monitoring_sessions(session_id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLES POUR CORRECTIONSERVICE (proctorwise_corrections)
-- ============================================================================
USE proctorwise_corrections;

CREATE TABLE IF NOT EXISTS exam_submissions (
    submission_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    exam_id VARCHAR(36) NOT NULL,
    reservation_id VARCHAR(36) NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('submitted', 'grading', 'graded', 'review_required') NOT NULL DEFAULT 'submitted',
    total_score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    percentage DECIMAL(5,2),
    graded_at TIMESTAMP NULL,
    graded_by VARCHAR(36),
    INDEX idx_user_id (user_id),
    INDEX idx_exam_id (exam_id),
    INDEX idx_status (status),
    INDEX idx_submitted_at (submitted_at)
);

CREATE TABLE IF NOT EXISTS answers (
    answer_id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL,
    question_id VARCHAR(36) NOT NULL,
    question_type ENUM('mcq', 'essay', 'short_answer') NOT NULL,
    answer_content TEXT,
    is_correct BOOLEAN,
    score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    feedback TEXT,
    graded_at TIMESTAMP NULL,
    INDEX idx_submission_id (submission_id),
    INDEX idx_question_id (question_id),
    FOREIGN KEY (submission_id) REFERENCES exam_submissions(submission_id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLES POUR NOTIFICATIONSERVICE (proctorwise_notifications)
-- ============================================================================
USE proctorwise_notifications;

CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    notification_type ENUM('exam_reminder', 'anomaly_detected', 'grade_ready', 'high_risk_alert', 'system') NOT NULL,
    channel ENUM('email', 'websocket', 'both') NOT NULL DEFAULT 'both',
    subject VARCHAR(255),
    body TEXT NOT NULL,
    status ENUM('pending', 'sent', 'failed', 'read') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    error_message TEXT,
    metadata JSON,
    INDEX idx_user_id (user_id),
    INDEX idx_notification_type (notification_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    notification_types JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);

-- ============================================================================
-- TABLES POUR ANALYTICSSERVICE (proctorwise_analytics)
-- ============================================================================
USE proctorwise_analytics;

CREATE TABLE IF NOT EXISTS exam_analytics (
    analytics_id VARCHAR(36) PRIMARY KEY,
    exam_id VARCHAR(36) NOT NULL,
    total_submissions INT DEFAULT 0,
    average_score DECIMAL(5,2),
    highest_score DECIMAL(5,2),
    lowest_score DECIMAL(5,2),
    pass_rate DECIMAL(5,2),
    average_duration_minutes INT,
    total_anomalies INT DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_exam_id (exam_id),
    INDEX idx_calculated_at (calculated_at)
);

CREATE TABLE IF NOT EXISTS user_analytics (
    analytics_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    total_exams_taken INT DEFAULT 0,
    average_score DECIMAL(5,2),
    total_anomalies INT DEFAULT 0,
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    performance_tier ENUM('excellent', 'good', 'average', 'needs_improvement') DEFAULT 'average',
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_calculated_at (calculated_at)
);

CREATE TABLE IF NOT EXISTS platform_metrics (
    metric_id VARCHAR(36) PRIMARY KEY,
    metric_date DATE NOT NULL,
    total_users INT DEFAULT 0,
    total_exams INT DEFAULT 0,
    total_sessions INT DEFAULT 0,
    total_anomalies INT DEFAULT 0,
    average_system_load DECIMAL(5,2),
    peak_concurrent_sessions INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY idx_metric_date (metric_date)
);
