from datetime import datetime
from typing import Dict, Any

from application.use_cases.send_notification import SendNotification
from infrastructure.templates.notification_templates import NotificationTemplates
from infrastructure.services.user_service_client import UserServiceClient, ReservationServiceClient


class ProcessExamScheduledEvent:
    """Notify student AND teacher when an exam is reserved."""

    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()

    async def execute(self, event: Dict[str, Any]):
        student_id = event.get("user_id")
        student_name = event.get("student_name") or "Un etudiant"
        exam_id = event.get("exam_id")
        exam_title = event.get("exam_title") or exam_id[:8]
        teacher_id = event.get("teacher_id")
        start_time = event.get("start_time")
        reservation_id = event.get("reservation_id")

        # 1. Notify the student (confirmation)
        subject, body = self.templates.get_exam_scheduled_template(
            exam_id=exam_id,
            start_time=start_time
        )

        await self.send_notification.execute(
            user_id=student_id,
            notification_type="exam_reminder",
            subject=subject,
            body=body,
            channel="both",
            metadata={
                "exam_id": exam_id,
                "reservation_id": reservation_id,
                "start_time": start_time
            }
        )

        # 2. Notify the teacher (info about new reservation)
        if teacher_id:
            teacher_subject = f"Nouvelle inscription: {exam_title}"
            teacher_body = f"{student_name} s'est inscrit a votre examen '{exam_title}' pour le {start_time[:10] if start_time else 'date non definie'}."

            await self.send_notification.execute(
                user_id=teacher_id,
                notification_type="exam_reminder",
                subject=teacher_subject,
                body=teacher_body,
                channel="both",
                metadata={
                    "exam_id": exam_id,
                    "reservation_id": reservation_id,
                    "student_id": student_id,
                    "start_time": start_time
                }
            )


class ProcessAnomalyDetectedEvent:
    """Notify proctors when anomaly is detected (not the student)."""

    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()
        self.user_client = UserServiceClient()

    async def execute(self, event: Dict[str, Any]):
        student_id = event.get("user_id")
        anomaly_type = event.get("anomaly_type")
        severity = event.get("severity")
        exam_id = event.get("exam_id")
        session_id = event.get("session_id")

        # Only notify for high/critical severity
        if severity not in ["high", "critical"]:
            return

        subject, body = self.templates.get_anomaly_detected_template(
            anomaly_type=anomaly_type,
            severity=severity,
            exam_id=exam_id
        )

        # Get all proctors and notify them
        proctors = await self.user_client.get_proctors()

        for proctor in proctors:
            await self.send_notification.execute(
                user_id=proctor["user_id"],
                notification_type="anomaly_detected",
                subject=subject,
                body=f"{body} (Etudiant: {student_id[:8]}...)",
                channel="push",
                metadata={
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "exam_id": exam_id,
                    "session_id": session_id,
                    "student_id": student_id
                }
            )

        # Also notify admins for critical anomalies
        if severity == "critical":
            admins = await self.user_client.get_admins()
            for admin in admins:
                await self.send_notification.execute(
                    user_id=admin["user_id"],
                    notification_type="anomaly_detected",
                    subject=f"[CRITICAL] {subject}",
                    body=f"{body} (Etudiant: {student_id[:8]}...)",
                    channel="push",
                    metadata={
                        "anomaly_type": anomaly_type,
                        "severity": severity,
                        "exam_id": exam_id,
                        "session_id": session_id,
                        "student_id": student_id
                    }
                )


class ProcessGradingCompletedEvent:
    """Notify student AND teacher when an exam is graded."""

    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()
        self.reservation_client = ReservationServiceClient()
        self.user_client = UserServiceClient()

    async def execute(self, event: Dict[str, Any]):
        student_id = event.get("user_id")
        exam_id = event.get("exam_id")
        total_score = event.get("total_score")
        max_score = event.get("max_score")
        percentage = event.get("percentage")
        submission_id = event.get("submission_id")

        # 1. Notify the student
        subject, body = self.templates.get_grade_ready_template(
            exam_id=exam_id,
            score=total_score,
            max_score=max_score,
            percentage=percentage
        )

        await self.send_notification.execute(
            user_id=student_id,
            notification_type="grade_ready",
            subject=subject,
            body=body,
            channel="both",
            metadata={
                "exam_id": exam_id,
                "submission_id": submission_id,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": percentage
            }
        )

        # 2. Notify the teacher
        exam = await self.reservation_client.get_exam(exam_id)
        if exam and exam.get("teacher_id"):
            teacher_id = exam["teacher_id"]
            exam_title = exam.get("title", exam_id[:8])

            # Get student name
            student = await self.user_client.get_user(student_id)
            student_name = student.get("name", student_id[:8]) if student else student_id[:8]

            teacher_subject = f"Copie corrigee: {exam_title}"
            teacher_body = f"{student_name} a termine l'examen '{exam_title}' avec un score de {percentage:.1f}% ({total_score}/{max_score})."

            await self.send_notification.execute(
                user_id=teacher_id,
                notification_type="grade_ready",
                subject=teacher_subject,
                body=teacher_body,
                channel="push",
                metadata={
                    "exam_id": exam_id,
                    "submission_id": submission_id,
                    "student_id": student_id,
                    "total_score": total_score,
                    "max_score": max_score,
                    "percentage": percentage
                }
            )


class ProcessHighRiskAlertEvent:
    """Notify proctors and admins when high risk activity is detected."""

    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()
        self.user_client = UserServiceClient()

    async def execute(self, event: Dict[str, Any]):
        student_id = event.get("user_id")
        exam_id = event.get("exam_id")
        session_id = event.get("session_id")
        critical_count = event.get("critical_anomalies_last_minute", 0)
        message = event.get("message", "High risk activity detected")

        subject, body = self.templates.get_high_risk_alert_template(
            exam_id=exam_id,
            critical_count=critical_count,
            message=message
        )

        # Notify all proctors
        proctors = await self.user_client.get_proctors()
        for proctor in proctors:
            await self.send_notification.execute(
                user_id=proctor["user_id"],
                notification_type="high_risk_alert",
                subject=subject,
                body=f"{body} (Etudiant: {student_id[:8]}...)",
                channel="push",
                metadata={
                    "exam_id": exam_id,
                    "session_id": session_id,
                    "critical_count": critical_count,
                    "student_id": student_id
                }
            )

        # Notify all admins
        admins = await self.user_client.get_admins()
        for admin in admins:
            await self.send_notification.execute(
                user_id=admin["user_id"],
                notification_type="high_risk_alert",
                subject=subject,
                body=f"{body} (Etudiant: {student_id[:8]}...)",
                channel="push",
                metadata={
                    "exam_id": exam_id,
                    "session_id": session_id,
                    "critical_count": critical_count,
                    "student_id": student_id
                }
            )
