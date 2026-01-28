import io
from datetime import datetime
from typing import Optional

from domain.entities.exam_analytics import ExamAnalytics
from domain.entities.user_analytics import UserAnalytics


class PDFReportGenerator:
    def __init__(self):
        self.pdf = None

    def generate_exam_report(self, analytics: ExamAnalytics) -> bytes:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
        except ImportError:
            return self._generate_text_fallback_exam(analytics)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 20)
        c.drawString(1 * inch, height - 1 * inch, "Exam Analytics Report")

        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 1.5 * inch, f"Exam ID: {analytics.exam_id}")
        c.drawString(1 * inch, height - 1.75 * inch, f"Generated: {analytics.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")

        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, height - 2.5 * inch, "Summary Statistics")

        c.setFont("Helvetica", 12)
        y = height - 3 * inch
        stats = [
            f"Total Submissions: {analytics.total_submissions}",
            f"Average Score: {analytics.average_score:.1f}%",
            f"Median Score: {analytics.median_score:.1f}%",
            f"Highest Score: {analytics.highest_score:.1f}%",
            f"Lowest Score: {analytics.lowest_score:.1f}%",
            f"Pass Rate: {analytics.pass_rate:.1f}%"
        ]

        for stat in stats:
            c.drawString(1.2 * inch, y, stat)
            y -= 0.3 * inch

        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, y - 0.5 * inch, "Score Distribution")

        y -= 1 * inch
        c.setFont("Helvetica", 12)
        for range_name, count in analytics.score_distribution.items():
            c.drawString(1.2 * inch, y, f"{range_name}%: {count} students")
            y -= 0.3 * inch

        if analytics.anomaly_summary:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1 * inch, y - 0.5 * inch, "Anomaly Summary")

            y -= 1 * inch
            c.setFont("Helvetica", 12)
            for anomaly_type, count in analytics.anomaly_summary.items():
                c.drawString(1.2 * inch, y, f"{anomaly_type}: {count}")
                y -= 0.3 * inch

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    def generate_user_report(self, analytics: UserAnalytics) -> bytes:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
        except ImportError:
            return self._generate_text_fallback_user(analytics)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 20)
        c.drawString(1 * inch, height - 1 * inch, "User Performance Report")

        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 1.5 * inch, f"User ID: {analytics.user_id}")
        c.drawString(1 * inch, height - 1.75 * inch, f"Generated: {analytics.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")

        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, height - 2.5 * inch, "Performance Summary")

        c.setFont("Helvetica", 12)
        y = height - 3 * inch
        stats = [
            f"Total Exams Taken: {analytics.total_exams_taken}",
            f"Average Score: {analytics.average_score:.1f}%",
            f"Exams Passed: {analytics.exams_passed}",
            f"Exams Failed: {analytics.exams_failed}",
            f"Pass Rate: {analytics.pass_rate:.1f}%",
            f"Total Anomalies: {analytics.total_anomalies}"
        ]

        for stat in stats:
            c.drawString(1.2 * inch, y, stat)
            y -= 0.3 * inch

        if analytics.strongest_areas:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1 * inch, y - 0.5 * inch, "Strongest Areas")
            y -= 1 * inch
            c.setFont("Helvetica", 12)
            for area in analytics.strongest_areas:
                c.drawString(1.2 * inch, y, f"- {area}")
                y -= 0.25 * inch

        if analytics.weakest_areas:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1 * inch, y - 0.5 * inch, "Areas for Improvement")
            y -= 1 * inch
            c.setFont("Helvetica", 12)
            for area in analytics.weakest_areas:
                c.drawString(1.2 * inch, y, f"- {area}")
                y -= 0.25 * inch

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_text_fallback_exam(self, analytics: ExamAnalytics) -> bytes:
        content = f"""
EXAM ANALYTICS REPORT
=====================
Exam ID: {analytics.exam_id}
Generated: {analytics.generated_at.strftime('%Y-%m-%d %H:%M UTC')}

SUMMARY STATISTICS
------------------
Total Submissions: {analytics.total_submissions}
Average Score: {analytics.average_score:.1f}%
Median Score: {analytics.median_score:.1f}%
Highest Score: {analytics.highest_score:.1f}%
Lowest Score: {analytics.lowest_score:.1f}%
Pass Rate: {analytics.pass_rate:.1f}%

SCORE DISTRIBUTION
------------------
"""
        for range_name, count in analytics.score_distribution.items():
            content += f"{range_name}%: {count} students\n"

        return content.encode('utf-8')

    def _generate_text_fallback_user(self, analytics: UserAnalytics) -> bytes:
        content = f"""
USER PERFORMANCE REPORT
=======================
User ID: {analytics.user_id}
Generated: {analytics.generated_at.strftime('%Y-%m-%d %H:%M UTC')}

PERFORMANCE SUMMARY
-------------------
Total Exams Taken: {analytics.total_exams_taken}
Average Score: {analytics.average_score:.1f}%
Exams Passed: {analytics.exams_passed}
Exams Failed: {analytics.exams_failed}
Pass Rate: {analytics.pass_rate:.1f}%
Total Anomalies: {analytics.total_anomalies}
"""
        return content.encode('utf-8')
