"""
Monthly User Performance Spark Job

Generates comprehensive user performance profiles based on monthly data.
Scheduled to run on the 1st of each month via Airflow.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, max as spark_max,
    min as spark_min, stddev, collect_list, array_distinct,
    lit, when, datediff, current_date, first, last,
    percentile_approx, row_number
)
from pyspark.sql.window import Window
from datetime import datetime, timedelta
import argparse


def create_spark_session():
    return SparkSession.builder \
        .appName("MonthlyUserPerformance") \
        .config("spark.sql.warehouse.dir", "/proctorwise/warehouse") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()


def load_user_submissions(spark, year, month):
    """Load submissions data for the specified month."""
    jdbc_url = "jdbc:mysql://mariadb:3306/proctorwise_corrections"

    submissions_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"""
            (SELECT *
             FROM exam_submissions
             WHERE YEAR(submitted_at) = {year}
               AND MONTH(submitted_at) = {month}) as submissions_data
        """) \
        .option("user", "proctorwise") \
        .option("password", "proctorwise_secret") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

    return submissions_df


def load_user_anomalies(spark, year, month):
    """Load anomalies data for the specified month."""
    jdbc_url = "jdbc:mysql://mariadb:3306/proctorwise_monitoring"

    anomalies_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"""
            (SELECT a.*, s.user_id
             FROM anomalies a
             JOIN monitoring_sessions s ON a.session_id = s.session_id
             WHERE YEAR(a.detected_at) = {year}
               AND MONTH(a.detected_at) = {month}) as anomalies_data
        """) \
        .option("user", "proctorwise") \
        .option("password", "proctorwise_secret") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

    return anomalies_df


def calculate_user_performance(submissions_df):
    """Calculate comprehensive performance metrics per user."""
    window_spec = Window.partitionBy("user_id").orderBy("submitted_at")

    with_rank = submissions_df \
        .withColumn("exam_order", row_number().over(window_spec))

    return with_rank.groupBy("user_id") \
        .agg(
            count("submission_id").alias("total_exams"),
            avg("percentage").alias("avg_score"),
            stddev("percentage").alias("score_consistency"),
            spark_min("percentage").alias("min_score"),
            spark_max("percentage").alias("max_score"),
            percentile_approx("percentage", 0.5).alias("median_score"),
            count(when(col("percentage") >= 60, 1)).alias("exams_passed"),
            count(when(col("percentage") < 60, 1)).alias("exams_failed"),
            first("percentage").alias("first_exam_score"),
            last("percentage").alias("last_exam_score"),
            spark_min("submitted_at").alias("first_exam_date"),
            spark_max("submitted_at").alias("last_exam_date"),
            array_distinct(collect_list("exam_id")).alias("unique_exams")
        ) \
        .withColumn("pass_rate", col("exams_passed") / col("total_exams") * 100) \
        .withColumn("score_improvement", col("last_exam_score") - col("first_exam_score")) \
        .withColumn("performance_tier",
            when(col("avg_score") >= 90, "excellent")
            .when(col("avg_score") >= 75, "good")
            .when(col("avg_score") >= 60, "average")
            .otherwise("needs_improvement")
        )


def calculate_user_anomaly_profile(anomalies_df):
    """Calculate anomaly profile per user."""
    return anomalies_df.groupBy("user_id") \
        .agg(
            count("anomaly_id").alias("total_anomalies"),
            count(when(col("severity") == "critical", 1)).alias("critical_anomalies"),
            count(when(col("severity") == "high", 1)).alias("high_anomalies"),
            count(when(col("severity") == "medium", 1)).alias("medium_anomalies"),
            count(when(col("severity") == "low", 1)).alias("low_anomalies"),
            spark_sum(when(col("anomaly_type") == "face_absent", 1).otherwise(0)).alias("face_absent_count"),
            spark_sum(when(col("anomaly_type") == "multiple_faces", 1).otherwise(0)).alias("multiple_faces_count"),
            spark_sum(when(col("anomaly_type") == "forbidden_object", 1).otherwise(0)).alias("forbidden_object_count"),
            spark_sum(when(col("anomaly_type") == "tab_change", 1).otherwise(0)).alias("tab_change_count"),
            avg("confidence").alias("avg_anomaly_confidence")
        ) \
        .withColumn("risk_level",
            when(col("critical_anomalies") >= 5, "high")
            .when(col("critical_anomalies") >= 2, "medium")
            .when(col("total_anomalies") >= 10, "medium")
            .otherwise("low")
        )


def create_user_profiles(performance_df, anomaly_df):
    """Combine performance and anomaly data into user profiles."""
    if anomaly_df is None:
        return performance_df \
            .withColumn("total_anomalies", lit(0)) \
            .withColumn("critical_anomalies", lit(0)) \
            .withColumn("risk_level", lit("low"))

    return performance_df \
        .join(anomaly_df, "user_id", "left") \
        .na.fill(0, [
            "total_anomalies", "critical_anomalies", "high_anomalies",
            "medium_anomalies", "low_anomalies", "face_absent_count",
            "multiple_faces_count", "forbidden_object_count", "tab_change_count"
        ]) \
        .na.fill("low", ["risk_level"])


def calculate_rankings(user_profiles_df):
    """Calculate rankings among users."""
    window_by_score = Window.orderBy(col("avg_score").desc())
    window_by_improvement = Window.orderBy(col("score_improvement").desc())

    return user_profiles_df \
        .withColumn("score_rank", row_number().over(window_by_score)) \
        .withColumn("improvement_rank", row_number().over(window_by_improvement))


def save_to_hdfs(df, output_path):
    """Save DataFrame to HDFS as Parquet."""
    df.write \
        .mode("overwrite") \
        .parquet(output_path)


def main(year=None, month=None):
    spark = create_spark_session()

    if not year or not month:
        last_month = datetime.utcnow().replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month

    print(f"Processing user performance data for: {year}-{month:02d}")

    base_output_path = f"/proctorwise/processed/user_performance/{year}/{month:02d}"

    submissions_df = load_user_submissions(spark, year, month)
    submissions_df.cache()

    submission_count = submissions_df.count()
    print(f"Loaded {submission_count} submission records")

    if submission_count > 0:
        performance_df = calculate_user_performance(submissions_df)
        print(f"Calculated performance for {performance_df.count()} users")

        anomalies_df = load_user_anomalies(spark, year, month)
        anomaly_count = anomalies_df.count()
        print(f"Loaded {anomaly_count} anomaly records")

        anomaly_profile_df = None
        if anomaly_count > 0:
            anomaly_profile_df = calculate_user_anomaly_profile(anomalies_df)

        user_profiles_df = create_user_profiles(performance_df, anomaly_profile_df)
        user_profiles_df = user_profiles_df.withColumn("report_month", lit(f"{year}-{month:02d}"))

        ranked_profiles = calculate_rankings(user_profiles_df)

        save_to_hdfs(ranked_profiles, f"{base_output_path}/user_profiles")
        print(f"Saved user profiles: {ranked_profiles.count()} records")

        top_performers = ranked_profiles.filter(col("score_rank") <= 100)
        save_to_hdfs(top_performers, f"{base_output_path}/top_performers")
        print(f"Saved top performers: {top_performers.count()} records")

        at_risk = ranked_profiles.filter(
            (col("risk_level") == "high") | (col("performance_tier") == "needs_improvement")
        )
        save_to_hdfs(at_risk, f"{base_output_path}/at_risk_users")
        print(f"Saved at-risk users: {at_risk.count()} records")

        most_improved = ranked_profiles.filter(col("improvement_rank") <= 100)
        save_to_hdfs(most_improved, f"{base_output_path}/most_improved")
        print(f"Saved most improved: {most_improved.count()} records")

        tier_summary = ranked_profiles.groupBy("performance_tier").count()
        save_to_hdfs(tier_summary, f"{base_output_path}/tier_summary")

        risk_summary = ranked_profiles.groupBy("risk_level").count()
        save_to_hdfs(risk_summary, f"{base_output_path}/risk_summary")

        summary = {
            "year": year,
            "month": month,
            "total_users": ranked_profiles.count(),
            "avg_platform_score": ranked_profiles.agg(avg("avg_score")).collect()[0][0],
            "high_risk_users": at_risk.count()
        }
        print(f"Summary: {summary}")

    submissions_df.unpersist()
    spark.stop()
    print("Monthly user performance analysis completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, help="Year to process")
    parser.add_argument("--month", type=int, help="Month to process")
    args = parser.parse_args()

    main(args.year, args.month)
