from datetime import datetime
from typing import Optional
import statistics

from domain.entities.user_analytics import UserAnalytics
from application.interfaces.analytics_repository import AnalyticsRepository
from application.interfaces.cache_store import CacheStore


class GetUserAnalytics:
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, repository: AnalyticsRepository, cache: CacheStore):
        self.repository = repository
        self.cache = cache

    def execute(self, user_id: str, use_cache: bool = True) -> UserAnalytics:
        cache_key = f"user_analytics:{user_id}"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        submissions = self.repository.get_user_submissions(user_id)
        anomalies = self.repository.get_user_anomalies(user_id)

        if not submissions:
            return UserAnalytics(
                user_id=user_id,
                total_exams_taken=0,
                average_score=0,
                total_anomalies=0,
                exams_passed=0,
                exams_failed=0,
                pass_rate=0,
                score_trend=[],
                anomaly_breakdown={},
                strongest_areas=[],
                weakest_areas=[]
            )

        scores = [s.get("percentage", 0) for s in submissions if s.get("percentage") is not None]
        if not scores:
            scores = [0]

        passing_threshold = 60
        passed = sum(1 for s in scores if s >= passing_threshold)
        failed = len(scores) - passed

        score_trend = [
            {
                "exam_id": s.get("exam_id"),
                "score": s.get("percentage", 0),
                "date": s.get("submitted_at")
            }
            for s in sorted(submissions, key=lambda x: x.get("submitted_at", ""))
        ]

        anomaly_breakdown = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.get("anomaly_type", "unknown")
            anomaly_breakdown[anomaly_type] = anomaly_breakdown.get(anomaly_type, 0) + 1

        strongest, weakest = self._analyze_areas(submissions)

        analytics = UserAnalytics(
            user_id=user_id,
            total_exams_taken=len(submissions),
            average_score=statistics.mean(scores),
            total_anomalies=len(anomalies),
            exams_passed=passed,
            exams_failed=failed,
            pass_rate=(passed / len(scores) * 100) if scores else 0,
            score_trend=score_trend,
            anomaly_breakdown=anomaly_breakdown,
            strongest_areas=strongest,
            weakest_areas=weakest,
            generated_at=datetime.utcnow()
        )

        self.cache.set(cache_key, analytics, self.CACHE_TTL)
        return analytics

    def _analyze_areas(self, submissions: list) -> tuple:
        area_performance = {}

        for submission in submissions:
            answers = submission.get("answers", [])
            for answer in answers:
                q_type = answer.get("question_type", "unknown")
                if q_type not in area_performance:
                    area_performance[q_type] = {"correct": 0, "total": 0}

                area_performance[q_type]["total"] += 1
                if answer.get("is_correct"):
                    area_performance[q_type]["correct"] += 1

        performance_rates = []
        for area, stats in area_performance.items():
            if stats["total"] > 0:
                rate = stats["correct"] / stats["total"] * 100
                performance_rates.append((area, rate))

        performance_rates.sort(key=lambda x: x[1], reverse=True)

        strongest = [area for area, rate in performance_rates[:3] if rate > 50]
        weakest = [area for area, rate in performance_rates[-3:] if rate < 50]

        return strongest, weakest
