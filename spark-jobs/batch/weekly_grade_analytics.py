"""
Weekly Grade Analytics Spark Job

Analyzes grading data from the past week and generates statistics.
Scheduled to run weekly on Sundays via Airflow.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, max as spark_max,
    min as spark_min, stddev, percentile_approx, lit,
    when, date_format, datediff, current_date
)
from datetime import datetime, timedelta
import argparse


def create_spark_session():
    return SparkSession.builder \
        .appName("WeeklyGradeAnalytics") \
        .config("spark.sql.warehouse.dir", "/proctorwise/warehouse") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()


def load_submissions_data(spark, start_date, end_date):
    """Load submissions data from MariaDB for the specified date range."""
    jdbc_url = "jdbc:mysql://mariadb:3306/proctorwise_corrections"

    submissions_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"""
            (SELECT *
             FROM exam_submissions
             WHERE submitted_at >= '{start_date}'
               AND submitted_at < '{end_date}'
               AND status = 'graded') as submissions_data
        """) \
        .option("user", "proctorwise") \
        .option("password", "proctorwise_secret") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

    return submissions_df


def load_answers_data(spark, submission_ids):
    """Load answers data for the given submissions."""
    jdbc_url = "jdbc:mysql://mariadb:3306/proctorwise_corrections"

    if not submission_ids:
        return None

    ids_str = ",".join([f"'{sid}'" for sid in submission_ids])

    answers_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"""
            (SELECT *
             FROM answers
             WHERE submission_id IN ({ids_str})) as answers_data
        """) \
        .option("user", "proctorwise") \
        .option("password", "proctorwise_secret") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

    return answers_df


def calculate_exam_statistics(submissions_df):
    """Calculate statistics per exam."""
    return submissions_df.groupBy("exam_id") \
        .agg(
            count("submission_id").alias("total_submissions"),
            avg("percentage").alias("avg_score"),
            stddev("percentage").alias("stddev_score"),
            spark_min("percentage").alias("min_score"),
            spark_max("percentage").alias("max_score"),
            percentile_approx("percentage", 0.5).alias("median_score"),
            percentile_approx("percentage", 0.25).alias("q1_score"),
            percentile_approx("percentage", 0.75).alias("q3_score"),
            count(when(col("percentage") >= 60, 1)).alias("passed_count"),
            count(when(col("percentage") < 60, 1)).alias("failed_count")
        ) \
        .withColumn("pass_rate", col("passed_count") / col("total_submissions") * 100)


def calculate_question_difficulty(answers_df):
    """Calculate difficulty statistics per question."""
    if answers_df is None:
        return None

    return answers_df.groupBy("question_id", "question_type") \
        .agg(
            count("answer_id").alias("total_attempts"),
            count(when(col("is_correct") == True, 1)).alias("correct_count"),
            count(when(col("is_correct") == False, 1)).alias("incorrect_count"),
            avg("score").alias("avg_score"),
            avg("max_score").alias("avg_max_score")
        ) \
        .withColumn("correct_rate", col("correct_count") / col("total_attempts") * 100) \
        .withColumn("difficulty",
            when(col("correct_rate") >= 80, "easy")
            .when(col("correct_rate") >= 50, "medium")
            .otherwise("hard")
        )


def calculate_daily_trends(submissions_df):
    """Calculate daily submission trends."""
    return submissions_df \
        .withColumn("submission_date", date_format("submitted_at", "yyyy-MM-dd")) \
        .groupBy("submission_date") \
        .agg(
            count("submission_id").alias("submissions_count"),
            avg("percentage").alias("avg_score"),
            count(when(col("percentage") >= 60, 1)).alias("passed_count")
        ) \
        .orderBy("submission_date")


def calculate_grading_efficiency(submissions_df):
    """Calculate grading efficiency metrics."""
    graded_df = submissions_df.filter(col("graded_at").isNotNull())

    return graded_df \
        .withColumn("grading_time_hours",
            (col("graded_at").cast("long") - col("submitted_at").cast("long")) / 3600
        ) \
        .groupBy("graded_by") \
        .agg(
            count("submission_id").alias("graded_count"),
            avg("grading_time_hours").alias("avg_grading_time_hours"),
            spark_min("grading_time_hours").alias("min_grading_time_hours"),
            spark_max("grading_time_hours").alias("max_grading_time_hours")
        )


def save_to_hdfs(df, output_path):
    """Save DataFrame to HDFS as Parquet."""
    if df is not None:
        df.write \
            .mode("overwrite") \
            .parquet(output_path)


def main(week_start=None):
    spark = create_spark_session()

    if not week_start:
        today = datetime.utcnow()
        days_since_sunday = (today.weekday() + 1) % 7
        last_sunday = today - timedelta(days=days_since_sunday + 7)
        week_start = last_sunday.strftime("%Y-%m-%d")

    start_date = datetime.strptime(week_start, "%Y-%m-%d")
    end_date = start_date + timedelta(days=7)

    print(f"Processing grade data for week: {week_start} to {end_date.strftime('%Y-%m-%d')}")

    year = start_date.strftime("%Y")
    week_num = start_date.strftime("%W")
    base_output_path = f"/proctorwise/processed/grading_results/{year}/week_{week_num}"

    submissions_df = load_submissions_data(
        spark,
        week_start,
        end_date.strftime("%Y-%m-%d")
    )
    submissions_df.cache()

    record_count = submissions_df.count()
    print(f"Loaded {record_count} submission records")

    if record_count > 0:
        exam_stats = calculate_exam_statistics(submissions_df)
        exam_stats = exam_stats.withColumn("week_start", lit(week_start))
        save_to_hdfs(exam_stats, f"{base_output_path}/exam_statistics")
        print(f"Saved exam statistics: {exam_stats.count()} records")

        daily_trends = calculate_daily_trends(submissions_df)
        daily_trends = daily_trends.withColumn("week_start", lit(week_start))
        save_to_hdfs(daily_trends, f"{base_output_path}/daily_trends")
        print(f"Saved daily trends: {daily_trends.count()} records")

        grading_efficiency = calculate_grading_efficiency(submissions_df)
        grading_efficiency = grading_efficiency.withColumn("week_start", lit(week_start))
        save_to_hdfs(grading_efficiency, f"{base_output_path}/grading_efficiency")
        print(f"Saved grading efficiency: {grading_efficiency.count()} records")

        submission_ids = [row.submission_id for row in submissions_df.select("submission_id").collect()]
        if submission_ids:
            answers_df = load_answers_data(spark, submission_ids[:1000])
            if answers_df is not None:
                question_difficulty = calculate_question_difficulty(answers_df)
                if question_difficulty is not None:
                    question_difficulty = question_difficulty.withColumn("week_start", lit(week_start))
                    save_to_hdfs(question_difficulty, f"{base_output_path}/question_difficulty")
                    print(f"Saved question difficulty: {question_difficulty.count()} records")

        summary = {
            "week_start": week_start,
            "total_submissions": record_count,
            "unique_exams": submissions_df.select("exam_id").distinct().count(),
            "unique_users": submissions_df.select("user_id").distinct().count(),
            "avg_score": submissions_df.agg(avg("percentage")).collect()[0][0]
        }
        print(f"Summary: {summary}")

    submissions_df.unpersist()
    spark.stop()
    print("Weekly grade analytics completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week-start", type=str, help="Week start date (YYYY-MM-DD)")
    args = parser.parse_args()

    main(args.week_start)
