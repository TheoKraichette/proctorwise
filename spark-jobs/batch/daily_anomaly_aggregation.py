"""
Daily Anomaly Aggregation Spark Job

Aggregates anomaly data from the previous day and stores results in HDFS.
Scheduled to run daily at 2 AM via Airflow.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, max as spark_max,
    min as spark_min, date_format, lit, current_timestamp,
    when, window
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    FloatType, TimestampType
)
from datetime import datetime, timedelta
import argparse


def create_spark_session():
    return SparkSession.builder \
        .appName("DailyAnomalyAggregation") \
        .config("spark.sql.warehouse.dir", "/proctorwise/warehouse") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()


def load_anomaly_data(spark, date_str):
    """Load anomaly data from MariaDB for the specified date."""
    jdbc_url = "jdbc:mysql://mariadb:3306/proctorwise_monitoring"

    anomalies_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"""
            (SELECT a.*, s.user_id, s.exam_id, s.reservation_id
             FROM anomalies a
             JOIN monitoring_sessions s ON a.session_id = s.session_id
             WHERE DATE(a.detected_at) = '{date_str}') as anomaly_data
        """) \
        .option("user", "proctorwise") \
        .option("password", "proctorwise_secret") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

    return anomalies_df


def aggregate_by_exam(anomalies_df):
    """Aggregate anomalies by exam."""
    return anomalies_df.groupBy("exam_id") \
        .agg(
            count("anomaly_id").alias("total_anomalies"),
            count(when(col("severity") == "critical", 1)).alias("critical_count"),
            count(when(col("severity") == "high", 1)).alias("high_count"),
            count(when(col("severity") == "medium", 1)).alias("medium_count"),
            count(when(col("severity") == "low", 1)).alias("low_count"),
            spark_sum(when(col("anomaly_type") == "face_absent", 1).otherwise(0)).alias("face_absent_count"),
            spark_sum(when(col("anomaly_type") == "multiple_faces", 1).otherwise(0)).alias("multiple_faces_count"),
            spark_sum(when(col("anomaly_type") == "forbidden_object", 1).otherwise(0)).alias("forbidden_object_count"),
            spark_sum(when(col("anomaly_type") == "tab_change", 1).otherwise(0)).alias("tab_change_count"),
            spark_sum(when(col("anomaly_type") == "webcam_disabled", 1).otherwise(0)).alias("webcam_disabled_count"),
            avg("confidence").alias("avg_confidence")
        )


def aggregate_by_user(anomalies_df):
    """Aggregate anomalies by user."""
    return anomalies_df.groupBy("user_id") \
        .agg(
            count("anomaly_id").alias("total_anomalies"),
            count(when(col("severity") == "critical", 1)).alias("critical_count"),
            count(when(col("severity") == "high", 1)).alias("high_count"),
            spark_sum(when(col("anomaly_type") == "face_absent", 1).otherwise(0)).alias("face_absent_count"),
            spark_sum(when(col("anomaly_type") == "multiple_faces", 1).otherwise(0)).alias("multiple_faces_count"),
            spark_sum(when(col("anomaly_type") == "forbidden_object", 1).otherwise(0)).alias("forbidden_object_count")
        )


def aggregate_hourly(anomalies_df):
    """Aggregate anomalies by hour for trend analysis."""
    return anomalies_df \
        .withColumn("hour", date_format("detected_at", "HH")) \
        .groupBy("hour") \
        .agg(
            count("anomaly_id").alias("anomaly_count"),
            count(when(col("severity") == "critical", 1)).alias("critical_count")
        ) \
        .orderBy("hour")


def save_to_hdfs(df, output_path):
    """Save DataFrame to HDFS as Parquet."""
    df.write \
        .mode("overwrite") \
        .parquet(output_path)


def main(date_str=None):
    spark = create_spark_session()

    if not date_str:
        yesterday = datetime.utcnow() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

    print(f"Processing anomaly data for date: {date_str}")

    year, month, day = date_str.split("-")
    base_output_path = f"/proctorwise/processed/anomaly_reports/{year}/{month}"

    anomalies_df = load_anomaly_data(spark, date_str)
    anomalies_df.cache()

    record_count = anomalies_df.count()
    print(f"Loaded {record_count} anomaly records")

    if record_count > 0:
        exam_agg = aggregate_by_exam(anomalies_df)
        exam_agg = exam_agg.withColumn("report_date", lit(date_str))
        save_to_hdfs(exam_agg, f"{base_output_path}/by_exam/{day}")
        print(f"Saved exam aggregation: {exam_agg.count()} records")

        user_agg = aggregate_by_user(anomalies_df)
        user_agg = user_agg.withColumn("report_date", lit(date_str))
        save_to_hdfs(user_agg, f"{base_output_path}/by_user/{day}")
        print(f"Saved user aggregation: {user_agg.count()} records")

        hourly_agg = aggregate_hourly(anomalies_df)
        hourly_agg = hourly_agg.withColumn("report_date", lit(date_str))
        save_to_hdfs(hourly_agg, f"{base_output_path}/hourly/{day}")
        print(f"Saved hourly aggregation: {hourly_agg.count()} records")

        summary = {
            "date": date_str,
            "total_anomalies": record_count,
            "unique_exams": anomalies_df.select("exam_id").distinct().count(),
            "unique_users": anomalies_df.select("user_id").distinct().count()
        }
        print(f"Summary: {summary}")

    anomalies_df.unpersist()
    spark.stop()
    print("Daily anomaly aggregation completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="Date to process (YYYY-MM-DD)")
    args = parser.parse_args()

    main(args.date)
