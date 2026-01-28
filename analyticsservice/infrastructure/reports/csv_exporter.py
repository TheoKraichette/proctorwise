import io
import csv
from typing import List, Dict
from datetime import datetime

from domain.entities.exam_analytics import ExamAnalytics
from domain.entities.user_analytics import UserAnalytics


class CSVExporter:
    def export_exam_analytics(self, analytics: ExamAnalytics) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(["Exam Analytics Report"])
        writer.writerow(["Exam ID", analytics.exam_id])
        writer.writerow(["Generated", analytics.generated_at.strftime('%Y-%m-%d %H:%M UTC')])
        writer.writerow([])

        writer.writerow(["Summary Statistics"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Submissions", analytics.total_submissions])
        writer.writerow(["Average Score", f"{analytics.average_score:.1f}%"])
        writer.writerow(["Median Score", f"{analytics.median_score:.1f}%"])
        writer.writerow(["Highest Score", f"{analytics.highest_score:.1f}%"])
        writer.writerow(["Lowest Score", f"{analytics.lowest_score:.1f}%"])
        writer.writerow(["Pass Rate", f"{analytics.pass_rate:.1f}%"])
        writer.writerow([])

        writer.writerow(["Score Distribution"])
        writer.writerow(["Range", "Count"])
        for range_name, count in analytics.score_distribution.items():
            writer.writerow([f"{range_name}%", count])
        writer.writerow([])

        if analytics.question_analytics:
            writer.writerow(["Question Analytics"])
            writer.writerow(["Question ID", "Total Attempts", "Correct Rate", "Average Score"])
            for q in analytics.question_analytics:
                writer.writerow([
                    q.get("question_id"),
                    q.get("total_attempts"),
                    f"{q.get('correct_rate', 0):.1f}%",
                    f"{q.get('average_score', 0):.2f}"
                ])

        return buffer.getvalue().encode('utf-8')

    def export_user_analytics(self, analytics: UserAnalytics) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(["User Performance Report"])
        writer.writerow(["User ID", analytics.user_id])
        writer.writerow(["Generated", analytics.generated_at.strftime('%Y-%m-%d %H:%M UTC')])
        writer.writerow([])

        writer.writerow(["Performance Summary"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Exams Taken", analytics.total_exams_taken])
        writer.writerow(["Average Score", f"{analytics.average_score:.1f}%"])
        writer.writerow(["Exams Passed", analytics.exams_passed])
        writer.writerow(["Exams Failed", analytics.exams_failed])
        writer.writerow(["Pass Rate", f"{analytics.pass_rate:.1f}%"])
        writer.writerow(["Total Anomalies", analytics.total_anomalies])
        writer.writerow([])

        if analytics.score_trend:
            writer.writerow(["Score History"])
            writer.writerow(["Exam ID", "Score", "Date"])
            for entry in analytics.score_trend:
                writer.writerow([
                    entry.get("exam_id"),
                    f"{entry.get('score', 0):.1f}%",
                    entry.get("date")
                ])
            writer.writerow([])

        if analytics.anomaly_breakdown:
            writer.writerow(["Anomaly Breakdown"])
            writer.writerow(["Type", "Count"])
            for anomaly_type, count in analytics.anomaly_breakdown.items():
                writer.writerow([anomaly_type, count])

        return buffer.getvalue().encode('utf-8')

    def export_submissions_list(self, submissions: List[Dict]) -> bytes:
        if not submissions:
            return b"No data available"

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        headers = ["Submission ID", "User ID", "Exam ID", "Score", "Status", "Submitted At"]
        writer.writerow(headers)

        for sub in submissions:
            writer.writerow([
                sub.get("submission_id"),
                sub.get("user_id"),
                sub.get("exam_id"),
                f"{sub.get('percentage', 0):.1f}%" if sub.get('percentage') else "N/A",
                sub.get("status"),
                sub.get("submitted_at")
            ])

        return buffer.getvalue().encode('utf-8')
