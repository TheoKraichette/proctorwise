"""
ProctorWise - DAGs Airflow pour les jobs Spark
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.docker.operators.docker import DockerOperator

# Configuration par défaut des DAGs
default_args = {
    'owner': 'proctorwise',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Configuration Spark commune
SPARK_MASTER = 'spark://spark-master:7077'
SPARK_JOBS_PATH = '/opt/spark-jobs/batch'

def spark_submit_cmd(job_file, driver_mem='1g', executor_mem='2g', extra_args=''):
    """Generate spark-submit command via docker exec."""
    return f"""
    docker exec proctorwise-spark-master /opt/spark/bin/spark-submit \
      --master {SPARK_MASTER} \
      --driver-memory {driver_mem} \
      --executor-memory {executor_mem} \
      --conf spark.jdbc.user=${{DB_USER:-proctorwise}} \
      --conf spark.jdbc.password=${{DB_PASSWORD:-proctorwise_secret}} \
      --jars /opt/spark/jars/mysql-connector-j-8.0.33.jar \
      {SPARK_JOBS_PATH}/{job_file} {extra_args}
    """

# ==============================================================================
# DAG 1: Agrégation quotidienne des anomalies
# ==============================================================================
with DAG(
    dag_id='daily_anomaly_aggregation',
    default_args=default_args,
    description='Agrégation quotidienne des anomalies de monitoring',
    schedule_interval='0 2 * * *',  # Tous les jours à 2h00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'spark', 'anomaly', 'daily'],
) as daily_anomaly_dag:

    start = EmptyOperator(task_id='start')

    anomaly_aggregation = BashOperator(
        task_id='run_daily_anomaly_aggregation',
        bash_command=spark_submit_cmd('daily_anomaly_aggregation.py'),
    )

    end = EmptyOperator(task_id='end')

    start >> anomaly_aggregation >> end

# ==============================================================================
# DAG 2: Analyse hebdomadaire des notes
# ==============================================================================
with DAG(
    dag_id='weekly_grade_analytics',
    default_args=default_args,
    description='Analyse hebdomadaire des notes et statistiques',
    schedule_interval='0 3 * * 0',  # Tous les dimanches à 3h00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'spark', 'grades', 'weekly'],
) as weekly_grade_dag:

    start = EmptyOperator(task_id='start')

    grade_analytics = BashOperator(
        task_id='run_weekly_grade_analytics',
        bash_command=spark_submit_cmd('weekly_grade_analytics.py'),
    )

    end = EmptyOperator(task_id='end')

    start >> grade_analytics >> end

# ==============================================================================
# DAG 3: Performance utilisateur mensuelle
# ==============================================================================
with DAG(
    dag_id='monthly_user_performance',
    default_args=default_args,
    description='Analyse mensuelle des performances utilisateurs',
    schedule_interval='0 5 1 * *',  # Le 1er de chaque mois à 5h00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'spark', 'users', 'monthly'],
) as monthly_user_dag:

    start = EmptyOperator(task_id='start')

    user_performance = BashOperator(
        task_id='run_monthly_user_performance',
        bash_command=spark_submit_cmd('monthly_user_performance.py', '1g', '1g'),
    )

    end = EmptyOperator(task_id='end')

    start >> user_performance >> end

# ==============================================================================
# DAG 4: Pipeline complet (manual trigger)
# ==============================================================================
with DAG(
    dag_id='full_analytics_pipeline',
    default_args=default_args,
    description='Pipeline complet de tous les jobs analytics (trigger manuel)',
    schedule_interval=None,  # Trigger manuel uniquement
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'spark', 'full-pipeline'],
) as full_pipeline_dag:

    start = EmptyOperator(task_id='start')

    anomaly_job = BashOperator(
        task_id='anomaly_aggregation',
        bash_command=spark_submit_cmd('daily_anomaly_aggregation.py'),
    )

    grade_job = BashOperator(
        task_id='grade_analytics',
        bash_command=spark_submit_cmd('weekly_grade_analytics.py'),
    )

    user_job = BashOperator(
        task_id='user_performance',
        bash_command=spark_submit_cmd('monthly_user_performance.py'),
    )

    end = EmptyOperator(task_id='end')

    start >> anomaly_job >> grade_job >> user_job >> end
