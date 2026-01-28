from datetime import datetime

from domain.entities.platform_metrics import PlatformMetrics, DashboardData
from application.interfaces.analytics_repository import AnalyticsRepository
from application.interfaces.cache_store import CacheStore


class GetPlatformMetrics:
    CACHE_TTL = 60  # 1 minute for real-time metrics

    def __init__(self, repository: AnalyticsRepository, cache: CacheStore):
        self.repository = repository
        self.cache = cache

    def execute(self, use_cache: bool = True) -> PlatformMetrics:
        cache_key = "platform_metrics"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        totals = self.repository.get_platform_totals()
        hourly = self.repository.get_hourly_activity(datetime.utcnow())
        daily = self.repository.get_daily_activity(days=30)

        metrics = PlatformMetrics(
            total_users=totals.get("total_users", 0),
            total_exams=totals.get("total_exams", 0),
            total_submissions=totals.get("total_submissions", 0),
            total_monitoring_sessions=totals.get("total_monitoring_sessions", 0),
            active_sessions_now=totals.get("active_sessions", 0),
            exams_today=totals.get("exams_today", 0),
            submissions_today=totals.get("submissions_today", 0),
            anomalies_today=totals.get("anomalies_today", 0),
            average_anomalies_per_exam=totals.get("avg_anomalies_per_exam", 0),
            system_health={
                "database": "healthy",
                "kafka": "healthy",
                "hdfs": "healthy",
                "redis": "healthy"
            },
            hourly_activity=hourly,
            daily_trends=daily,
            generated_at=datetime.utcnow()
        )

        self.cache.set(cache_key, metrics, self.CACHE_TTL)
        return metrics


class GetAdminDashboard:
    CACHE_TTL = 60

    def __init__(self, repository: AnalyticsRepository, cache: CacheStore):
        self.repository = repository
        self.cache = cache
        self.platform_metrics_use_case = GetPlatformMetrics(repository, cache)

    def execute(self, use_cache: bool = True) -> DashboardData:
        cache_key = "admin_dashboard"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        platform_metrics = self.platform_metrics_use_case.execute(use_cache=False)
        recent_exams = self.repository.get_recent_exams(limit=10)
        recent_anomalies = self.repository.get_recent_anomalies(limit=10)
        top_performers = self.repository.get_top_performers(limit=10)

        alerts = self._generate_alerts(platform_metrics, recent_anomalies)

        dashboard = DashboardData(
            platform_metrics=platform_metrics,
            recent_exams=recent_exams,
            recent_anomalies=recent_anomalies,
            top_performers=top_performers,
            alerts=alerts,
            generated_at=datetime.utcnow()
        )

        self.cache.set(cache_key, dashboard, self.CACHE_TTL)
        return dashboard

    def _generate_alerts(self, metrics: PlatformMetrics, anomalies: list) -> list:
        alerts = []

        if metrics.anomalies_today > 100:
            alerts.append({
                "level": "warning",
                "message": f"High anomaly count today: {metrics.anomalies_today}",
                "type": "anomaly_spike"
            })

        critical_count = sum(1 for a in anomalies if a.get("severity") == "critical")
        if critical_count > 5:
            alerts.append({
                "level": "critical",
                "message": f"{critical_count} critical anomalies in recent activity",
                "type": "critical_anomalies"
            })

        for service, status in metrics.system_health.items():
            if status != "healthy":
                alerts.append({
                    "level": "error",
                    "message": f"Service {service} is {status}",
                    "type": "system_health"
                })

        return alerts
