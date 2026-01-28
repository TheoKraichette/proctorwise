from fastapi import APIRouter
from fastapi.responses import Response

from application.use_cases.get_exam_analytics import GetExamAnalytics
from application.use_cases.get_user_analytics import GetUserAnalytics
from application.use_cases.get_platform_metrics import GetPlatformMetrics, GetAdminDashboard
from infrastructure.repositories.sqlalchemy_analytics_repository import SQLAlchemyAnalyticsRepository
from infrastructure.cache.memory_cache import InMemoryCacheStore
from infrastructure.reports.pdf_generator import PDFReportGenerator
from infrastructure.reports.csv_exporter import CSVExporter
from interface.api.schemas.analytics_response import (
    ExamAnalyticsResponse,
    UserAnalyticsResponse,
    PlatformMetricsResponse,
    DashboardResponse,
    AlertResponse
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

repo = SQLAlchemyAnalyticsRepository()
cache = InMemoryCacheStore()
pdf_generator = PDFReportGenerator()
csv_exporter = CSVExporter()


@router.get("/exams/{exam_id}", response_model=ExamAnalyticsResponse)
def get_exam_analytics(exam_id: str, use_cache: bool = True):
    use_case = GetExamAnalytics(repo, cache)
    analytics = use_case.execute(exam_id, use_cache)

    return ExamAnalyticsResponse(
        exam_id=analytics.exam_id,
        total_submissions=analytics.total_submissions,
        average_score=analytics.average_score,
        median_score=analytics.median_score,
        highest_score=analytics.highest_score,
        lowest_score=analytics.lowest_score,
        pass_rate=analytics.pass_rate,
        score_distribution=analytics.score_distribution,
        question_analytics=analytics.question_analytics,
        average_completion_time=analytics.average_completion_time,
        anomaly_summary=analytics.anomaly_summary,
        generated_at=analytics.generated_at
    )


@router.get("/exams/{exam_id}/report/pdf")
def get_exam_report_pdf(exam_id: str):
    use_case = GetExamAnalytics(repo, cache)
    analytics = use_case.execute(exam_id, use_cache=False)

    pdf_bytes = pdf_generator.generate_exam_report(analytics)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=exam_{exam_id}_report.pdf"
        }
    )


@router.get("/exams/{exam_id}/report/csv")
def get_exam_report_csv(exam_id: str):
    use_case = GetExamAnalytics(repo, cache)
    analytics = use_case.execute(exam_id, use_cache=False)

    csv_bytes = csv_exporter.export_exam_analytics(analytics)

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=exam_{exam_id}_report.csv"
        }
    )


@router.get("/users/{user_id}", response_model=UserAnalyticsResponse)
def get_user_analytics(user_id: str, use_cache: bool = True):
    use_case = GetUserAnalytics(repo, cache)
    analytics = use_case.execute(user_id, use_cache)

    return UserAnalyticsResponse(
        user_id=analytics.user_id,
        total_exams_taken=analytics.total_exams_taken,
        average_score=analytics.average_score,
        total_anomalies=analytics.total_anomalies,
        exams_passed=analytics.exams_passed,
        exams_failed=analytics.exams_failed,
        pass_rate=analytics.pass_rate,
        score_trend=analytics.score_trend,
        anomaly_breakdown=analytics.anomaly_breakdown,
        strongest_areas=analytics.strongest_areas,
        weakest_areas=analytics.weakest_areas,
        generated_at=analytics.generated_at
    )


@router.get("/users/{user_id}/report/pdf")
def get_user_report_pdf(user_id: str):
    use_case = GetUserAnalytics(repo, cache)
    analytics = use_case.execute(user_id, use_cache=False)

    pdf_bytes = pdf_generator.generate_user_report(analytics)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=user_{user_id}_report.pdf"
        }
    )


@router.get("/users/{user_id}/report/csv")
def get_user_report_csv(user_id: str):
    use_case = GetUserAnalytics(repo, cache)
    analytics = use_case.execute(user_id, use_cache=False)

    csv_bytes = csv_exporter.export_user_analytics(analytics)

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=user_{user_id}_report.csv"
        }
    )


@router.get("/platform", response_model=PlatformMetricsResponse)
def get_platform_metrics(use_cache: bool = True):
    use_case = GetPlatformMetrics(repo, cache)
    metrics = use_case.execute(use_cache)

    return PlatformMetricsResponse(
        total_users=metrics.total_users,
        total_exams=metrics.total_exams,
        total_submissions=metrics.total_submissions,
        total_monitoring_sessions=metrics.total_monitoring_sessions,
        active_sessions_now=metrics.active_sessions_now,
        exams_today=metrics.exams_today,
        submissions_today=metrics.submissions_today,
        anomalies_today=metrics.anomalies_today,
        average_anomalies_per_exam=metrics.average_anomalies_per_exam,
        system_health=metrics.system_health,
        hourly_activity=metrics.hourly_activity,
        daily_trends=metrics.daily_trends,
        generated_at=metrics.generated_at
    )


@router.get("/dashboards/admin", response_model=DashboardResponse)
def get_admin_dashboard(use_cache: bool = True):
    use_case = GetAdminDashboard(repo, cache)
    dashboard = use_case.execute(use_cache)

    return DashboardResponse(
        platform_metrics=PlatformMetricsResponse(
            total_users=dashboard.platform_metrics.total_users,
            total_exams=dashboard.platform_metrics.total_exams,
            total_submissions=dashboard.platform_metrics.total_submissions,
            total_monitoring_sessions=dashboard.platform_metrics.total_monitoring_sessions,
            active_sessions_now=dashboard.platform_metrics.active_sessions_now,
            exams_today=dashboard.platform_metrics.exams_today,
            submissions_today=dashboard.platform_metrics.submissions_today,
            anomalies_today=dashboard.platform_metrics.anomalies_today,
            average_anomalies_per_exam=dashboard.platform_metrics.average_anomalies_per_exam,
            system_health=dashboard.platform_metrics.system_health,
            hourly_activity=dashboard.platform_metrics.hourly_activity,
            daily_trends=dashboard.platform_metrics.daily_trends,
            generated_at=dashboard.platform_metrics.generated_at
        ),
        recent_exams=dashboard.recent_exams,
        recent_anomalies=dashboard.recent_anomalies,
        top_performers=dashboard.top_performers,
        alerts=[AlertResponse(**a) for a in dashboard.alerts],
        generated_at=dashboard.generated_at
    )
