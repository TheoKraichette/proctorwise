from datetime import datetime
from typing import Dict, Any

from application.use_cases.send_notification import SendNotification
from infrastructure.templates.notification_templates import NotificationTemplates


class ProcessExamScheduledEvent:
    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()

    async def execute(self, event: Dict[str, Any]):
        user_id = event.get("user_id")
        exam_id = event.get("exam_id")
        start_time = event.get("start_time")
        reservation_id = event.get("reservation_id")

        subject, body = self.templates.get_exam_scheduled_template(
            exam_id=exam_id,
            start_time=start_time
        )

        await self.send_notification.execute(
            user_id=user_id,
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


class ProcessAnomalyDetectedEvent:
    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()

    async def execute(self, event: Dict[str, Any]):
        user_id = event.get("user_id")
        anomaly_type = event.get("anomaly_type")
        severity = event.get("severity")
        exam_id = event.get("exam_id")
        session_id = event.get("session_id")

        if severity not in ["high", "critical"]:
            return

        subject, body = self.templates.get_anomaly_detected_template(
            anomaly_type=anomaly_type,
            severity=severity,
            exam_id=exam_id
        )

        await self.send_notification.execute(
            user_id=user_id,
            notification_type="anomaly_detected",
            subject=subject,
            body=body,
            channel="push",
            metadata={
                "anomaly_type": anomaly_type,
                "severity": severity,
                "exam_id": exam_id,
                "session_id": session_id
            }
        )


class ProcessGradingCompletedEvent:
    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()

    async def execute(self, event: Dict[str, Any]):
        user_id = event.get("user_id")
        exam_id = event.get("exam_id")
        total_score = event.get("total_score")
        max_score = event.get("max_score")
        percentage = event.get("percentage")
        submission_id = event.get("submission_id")

        subject, body = self.templates.get_grade_ready_template(
            exam_id=exam_id,
            score=total_score,
            max_score=max_score,
            percentage=percentage
        )

        await self.send_notification.execute(
            user_id=user_id,
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


class ProcessHighRiskAlertEvent:
    def __init__(self, send_notification: SendNotification):
        self.send_notification = send_notification
        self.templates = NotificationTemplates()

    async def execute(self, event: Dict[str, Any]):
        user_id = event.get("user_id")
        exam_id = event.get("exam_id")
        session_id = event.get("session_id")
        critical_count = event.get("critical_anomalies_last_minute", 0)
        message = event.get("message", "High risk activity detected")

        subject, body = self.templates.get_high_risk_alert_template(
            exam_id=exam_id,
            critical_count=critical_count,
            message=message
        )

        await self.send_notification.execute(
            user_id=user_id,
            notification_type="high_risk_alert",
            subject=subject,
            body=body,
            channel="push",
            metadata={
                "exam_id": exam_id,
                "session_id": session_id,
                "critical_count": critical_count
            }
        )
