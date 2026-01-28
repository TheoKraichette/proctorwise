from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy import text

from infrastructure.database.mariadb_cluster import SessionLocal
from application.interfaces.analytics_repository import AnalyticsRepository


class SQLAlchemyAnalyticsRepository(AnalyticsRepository):

    def get_exam_submissions(self, exam_id: str) -> List[Dict]:
        session = SessionLocal()
        query = text("""
            SELECT submission_id, user_id, exam_id, percentage, submitted_at, status
            FROM proctorwise_corrections.exam_submissions
            WHERE exam_id = :exam_id
        """)
        result = session.execute(query, {"exam_id": exam_id})
        submissions = [dict(row._mapping) for row in result]
        session.close()
        return submissions

    def get_user_submissions(self, user_id: str) -> List[Dict]:
        session = SessionLocal()
        query = text("""
            SELECT submission_id, user_id, exam_id, percentage, submitted_at, status
            FROM proctorwise_corrections.exam_submissions
            WHERE user_id = :user_id
            ORDER BY submitted_at DESC
        """)
        result = session.execute(query, {"user_id": user_id})
        submissions = [dict(row._mapping) for row in result]
        session.close()
        return submissions

    def get_exam_anomalies(self, exam_id: str) -> List[Dict]:
        session = SessionLocal()
        query = text("""
            SELECT a.anomaly_id, a.session_id, a.anomaly_type, a.severity, a.detected_at
            FROM proctorwise_monitoring.anomalies a
            JOIN proctorwise_monitoring.monitoring_sessions s ON a.session_id = s.session_id
            WHERE s.exam_id = :exam_id
        """)
        result = session.execute(query, {"exam_id": exam_id})
        anomalies = [dict(row._mapping) for row in result]
        session.close()
        return anomalies

    def get_user_anomalies(self, user_id: str) -> List[Dict]:
        session = SessionLocal()
        query = text("""
            SELECT a.anomaly_id, a.session_id, a.anomaly_type, a.severity, a.detected_at
            FROM proctorwise_monitoring.anomalies a
            JOIN proctorwise_monitoring.monitoring_sessions s ON a.session_id = s.session_id
            WHERE s.user_id = :user_id
        """)
        result = session.execute(query, {"user_id": user_id})
        anomalies = [dict(row._mapping) for row in result]
        session.close()
        return anomalies

    def get_platform_totals(self) -> Dict:
        session = SessionLocal()
        today = datetime.utcnow().date()

        totals = {}

        try:
            result = session.execute(text("SELECT COUNT(*) FROM proctorwise_users.users"))
            totals["total_users"] = result.scalar() or 0
        except Exception:
            totals["total_users"] = 0

        try:
            result = session.execute(text("SELECT COUNT(DISTINCT exam_id) FROM proctorwise_reservations.reservations"))
            totals["total_exams"] = result.scalar() or 0
        except Exception:
            totals["total_exams"] = 0

        try:
            result = session.execute(text("SELECT COUNT(*) FROM proctorwise_corrections.exam_submissions"))
            totals["total_submissions"] = result.scalar() or 0
        except Exception:
            totals["total_submissions"] = 0

        try:
            result = session.execute(text("SELECT COUNT(*) FROM proctorwise_monitoring.monitoring_sessions"))
            totals["total_monitoring_sessions"] = result.scalar() or 0
        except Exception:
            totals["total_monitoring_sessions"] = 0

        try:
            result = session.execute(text(
                "SELECT COUNT(*) FROM proctorwise_monitoring.monitoring_sessions WHERE status = 'active'"
            ))
            totals["active_sessions"] = result.scalar() or 0
        except Exception:
            totals["active_sessions"] = 0

        try:
            result = session.execute(text("""
                SELECT COUNT(*) FROM proctorwise_corrections.exam_submissions
                WHERE DATE(submitted_at) = :today
            """), {"today": today})
            totals["submissions_today"] = result.scalar() or 0
        except Exception:
            totals["submissions_today"] = 0

        try:
            result = session.execute(text("""
                SELECT COUNT(*) FROM proctorwise_monitoring.anomalies
                WHERE DATE(detected_at) = :today
            """), {"today": today})
            totals["anomalies_today"] = result.scalar() or 0
        except Exception:
            totals["anomalies_today"] = 0

        totals["exams_today"] = totals.get("submissions_today", 0)

        if totals.get("total_exams", 0) > 0:
            totals["avg_anomalies_per_exam"] = totals.get("anomalies_today", 0) / max(totals.get("exams_today", 1), 1)
        else:
            totals["avg_anomalies_per_exam"] = 0

        session.close()
        return totals

    def get_daily_activity(self, days: int = 30) -> List[Dict]:
        session = SessionLocal()
        start_date = datetime.utcnow() - timedelta(days=days)

        try:
            query = text("""
                SELECT DATE(submitted_at) as date, COUNT(*) as submissions
                FROM proctorwise_corrections.exam_submissions
                WHERE submitted_at >= :start_date
                GROUP BY DATE(submitted_at)
                ORDER BY date
            """)
            result = session.execute(query, {"start_date": start_date})
            daily = [{"date": str(row.date), "submissions": row.submissions} for row in result]
        except Exception:
            daily = []

        session.close()
        return daily

    def get_hourly_activity(self, date: datetime) -> List[Dict]:
        session = SessionLocal()
        target_date = date.date()

        try:
            query = text("""
                SELECT HOUR(submitted_at) as hour, COUNT(*) as count
                FROM proctorwise_corrections.exam_submissions
                WHERE DATE(submitted_at) = :target_date
                GROUP BY HOUR(submitted_at)
                ORDER BY hour
            """)
            result = session.execute(query, {"target_date": target_date})
            hourly = [{"hour": row.hour, "submissions": row.count} for row in result]
        except Exception:
            hourly = []

        session.close()
        return hourly

    def get_recent_exams(self, limit: int = 10) -> List[Dict]:
        session = SessionLocal()
        try:
            query = text("""
                SELECT submission_id, user_id, exam_id, percentage, submitted_at, status
                FROM proctorwise_corrections.exam_submissions
                ORDER BY submitted_at DESC
                LIMIT :limit
            """)
            result = session.execute(query, {"limit": limit})
            exams = [dict(row._mapping) for row in result]
        except Exception:
            exams = []

        session.close()
        return exams

    def get_recent_anomalies(self, limit: int = 10) -> List[Dict]:
        session = SessionLocal()
        try:
            query = text("""
                SELECT a.anomaly_id, a.anomaly_type, a.severity, a.detected_at, s.user_id, s.exam_id
                FROM proctorwise_monitoring.anomalies a
                JOIN proctorwise_monitoring.monitoring_sessions s ON a.session_id = s.session_id
                ORDER BY a.detected_at DESC
                LIMIT :limit
            """)
            result = session.execute(query, {"limit": limit})
            anomalies = [dict(row._mapping) for row in result]
        except Exception:
            anomalies = []

        session.close()
        return anomalies

    def get_top_performers(self, limit: int = 10) -> List[Dict]:
        session = SessionLocal()
        try:
            query = text("""
                SELECT user_id, AVG(percentage) as avg_score, COUNT(*) as exam_count
                FROM proctorwise_corrections.exam_submissions
                WHERE percentage IS NOT NULL
                GROUP BY user_id
                HAVING exam_count >= 3
                ORDER BY avg_score DESC
                LIMIT :limit
            """)
            result = session.execute(query, {"limit": limit})
            performers = [dict(row._mapping) for row in result]
        except Exception:
            performers = []

        session.close()
        return performers
