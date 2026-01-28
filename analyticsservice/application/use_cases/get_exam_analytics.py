from datetime import datetime
from typing import Optional
import statistics

from domain.entities.exam_analytics import ExamAnalytics
from application.interfaces.analytics_repository import AnalyticsRepository
from application.interfaces.cache_store import CacheStore


class GetExamAnalytics:
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, repository: AnalyticsRepository, cache: CacheStore):
        self.repository = repository
        self.cache = cache

    def execute(self, exam_id: str, use_cache: bool = True) -> ExamAnalytics:
        cache_key = f"exam_analytics:{exam_id}"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        submissions = self.repository.get_exam_submissions(exam_id)
        anomalies = self.repository.get_exam_anomalies(exam_id)

        if not submissions:
            return ExamAnalytics(
                exam_id=exam_id,
                total_submissions=0,
                average_score=0,
                median_score=0,
                highest_score=0,
                lowest_score=0,
                pass_rate=0,
                score_distribution={},
                question_analytics=[]
            )

        scores = [s.get("percentage", 0) for s in submissions if s.get("percentage") is not None]

        if not scores:
            scores = [0]

        score_distribution = self._calculate_score_distribution(scores)
        question_analytics = self._calculate_question_analytics(submissions)
        anomaly_summary = self._summarize_anomalies(anomalies)

        passing_threshold = 60
        passed = sum(1 for s in scores if s >= passing_threshold)

        analytics = ExamAnalytics(
            exam_id=exam_id,
            total_submissions=len(submissions),
            average_score=statistics.mean(scores),
            median_score=statistics.median(scores),
            highest_score=max(scores),
            lowest_score=min(scores),
            pass_rate=(passed / len(scores) * 100) if scores else 0,
            score_distribution=score_distribution,
            question_analytics=question_analytics,
            anomaly_summary=anomaly_summary,
            generated_at=datetime.utcnow()
        )

        self.cache.set(cache_key, analytics, self.CACHE_TTL)
        return analytics

    def _calculate_score_distribution(self, scores: list) -> dict:
        distribution = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0
        }

        for score in scores:
            if score <= 20:
                distribution["0-20"] += 1
            elif score <= 40:
                distribution["21-40"] += 1
            elif score <= 60:
                distribution["41-60"] += 1
            elif score <= 80:
                distribution["61-80"] += 1
            else:
                distribution["81-100"] += 1

        return distribution

    def _calculate_question_analytics(self, submissions: list) -> list:
        question_stats = {}

        for submission in submissions:
            answers = submission.get("answers", [])
            for answer in answers:
                q_id = answer.get("question_id")
                if q_id not in question_stats:
                    question_stats[q_id] = {
                        "question_id": q_id,
                        "total_attempts": 0,
                        "correct": 0,
                        "incorrect": 0,
                        "average_score": []
                    }

                question_stats[q_id]["total_attempts"] += 1
                if answer.get("is_correct"):
                    question_stats[q_id]["correct"] += 1
                elif answer.get("is_correct") is False:
                    question_stats[q_id]["incorrect"] += 1

                if answer.get("score") is not None:
                    question_stats[q_id]["average_score"].append(answer["score"])

        result = []
        for q_id, stats in question_stats.items():
            avg_scores = stats["average_score"]
            result.append({
                "question_id": q_id,
                "total_attempts": stats["total_attempts"],
                "correct_rate": (stats["correct"] / stats["total_attempts"] * 100) if stats["total_attempts"] > 0 else 0,
                "average_score": statistics.mean(avg_scores) if avg_scores else 0
            })

        return sorted(result, key=lambda x: x.get("correct_rate", 0))

    def _summarize_anomalies(self, anomalies: list) -> dict:
        summary = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.get("anomaly_type", "unknown")
            summary[anomaly_type] = summary.get(anomaly_type, 0) + 1
        return summary
