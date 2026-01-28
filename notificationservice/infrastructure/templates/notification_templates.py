from typing import Tuple
from jinja2 import Template


class NotificationTemplates:
    EXAM_SCHEDULED_TEMPLATE = """
Your exam has been scheduled!

Exam ID: {{ exam_id }}
Start Time: {{ start_time }}

Please make sure you are ready at least 15 minutes before the scheduled time.

Best regards,
ProctorWise Team
"""

    EXAM_REMINDER_TEMPLATE = """
Reminder: Your exam is coming up!

Exam ID: {{ exam_id }}
Starts in: {{ hours }} hour(s)
Start Time: {{ start_time }}

Make sure to:
- Test your webcam and microphone
- Find a quiet, well-lit environment
- Have your ID ready for verification

Good luck!
ProctorWise Team
"""

    ANOMALY_DETECTED_TEMPLATE = """
Alert: Anomaly detected during your exam

Exam ID: {{ exam_id }}
Type: {{ anomaly_type }}
Severity: {{ severity }}

Please ensure you are following all exam guidelines. Multiple anomalies may affect your exam results.

ProctorWise Team
"""

    GRADE_READY_TEMPLATE = """
Your exam has been graded!

Exam ID: {{ exam_id }}
Score: {{ score }}/{{ max_score }} ({{ percentage }}%)

You can view your detailed results in your dashboard.

ProctorWise Team
"""

    HIGH_RISK_ALERT_TEMPLATE = """
URGENT: High risk activity detected

Exam ID: {{ exam_id }}
Critical anomalies in last minute: {{ critical_count }}

{{ message }}

This alert has been logged and will be reviewed by our proctoring team.

ProctorWise Team
"""

    def get_exam_scheduled_template(self, exam_id: str, start_time: str) -> Tuple[str, str]:
        subject = f"Exam Scheduled - {exam_id}"
        body = Template(self.EXAM_SCHEDULED_TEMPLATE).render(
            exam_id=exam_id,
            start_time=start_time
        )
        return subject, body

    def get_exam_reminder_template(self, exam_id: str, start_time: str, hours: int) -> Tuple[str, str]:
        subject = f"Exam Reminder - {hours}h before"
        body = Template(self.EXAM_REMINDER_TEMPLATE).render(
            exam_id=exam_id,
            start_time=start_time,
            hours=hours
        )
        return subject, body

    def get_anomaly_detected_template(
        self,
        anomaly_type: str,
        severity: str,
        exam_id: str
    ) -> Tuple[str, str]:
        subject = f"Anomaly Detected - {severity.upper()}"
        body = Template(self.ANOMALY_DETECTED_TEMPLATE).render(
            exam_id=exam_id,
            anomaly_type=anomaly_type,
            severity=severity
        )
        return subject, body

    def get_grade_ready_template(
        self,
        exam_id: str,
        score: float,
        max_score: float,
        percentage: float
    ) -> Tuple[str, str]:
        subject = "Your Exam Results Are Ready"
        body = Template(self.GRADE_READY_TEMPLATE).render(
            exam_id=exam_id,
            score=score,
            max_score=max_score,
            percentage=f"{percentage:.1f}"
        )
        return subject, body

    def get_high_risk_alert_template(
        self,
        exam_id: str,
        critical_count: int,
        message: str
    ) -> Tuple[str, str]:
        subject = "URGENT: High Risk Alert"
        body = Template(self.HIGH_RISK_ALERT_TEMPLATE).render(
            exam_id=exam_id,
            critical_count=critical_count,
            message=message
        )
        return subject, body
