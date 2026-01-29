"""
ProctorWise - DAGs de maintenance (backup, cleanup, monitoring)
Remplace les cron jobs par une orchestration Airflow.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'proctorwise',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# ==============================================================================
# DAG 1: Backup quotidien MariaDB
# ==============================================================================
with DAG(
    dag_id='daily_mariadb_backup',
    default_args=default_args,
    description='Backup quotidien de toutes les bases MariaDB',
    schedule_interval='0 1 * * *',  # Tous les jours a 1h00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'maintenance', 'backup', 'daily'],
) as backup_dag:

    start = EmptyOperator(task_id='start')

    backup_all_databases = BashOperator(
        task_id='backup_mariadb',
        bash_command="""
        BACKUP_DIR=/opt/airflow/logs/backups/mariadb
        DATE=$(date +%Y%m%d_%H%M%S)
        mkdir -p $BACKUP_DIR

        docker exec proctorwise-mariadb mysqldump \
          -u${DB_USER:-proctorwise} \
          -p${DB_PASSWORD:-proctorwise_secret} \
          --all-databases \
          --single-transaction \
          --routines \
          --triggers \
          > "$BACKUP_DIR/backup_$DATE.sql"

        FILESIZE=$(stat -f%z "$BACKUP_DIR/backup_$DATE.sql" 2>/dev/null || stat -c%s "$BACKUP_DIR/backup_$DATE.sql" 2>/dev/null || echo 0)
        if [ "$FILESIZE" -lt 1000 ]; then
          echo "ERROR: Backup file too small ($FILESIZE bytes), likely failed"
          exit 1
        fi

        echo "Backup successful: backup_$DATE.sql ($FILESIZE bytes)"
        """,
    )

    cleanup_old_backups = BashOperator(
        task_id='cleanup_old_backups',
        bash_command="""
        BACKUP_DIR=/opt/airflow/logs/backups/mariadb
        if [ -d "$BACKUP_DIR" ]; then
          DELETED=$(find $BACKUP_DIR -name "*.sql" -mtime +7 -delete -print | wc -l)
          echo "Deleted $DELETED backup files older than 7 days"
        fi
        """,
    )

    end = EmptyOperator(task_id='end')

    start >> backup_all_databases >> cleanup_old_backups >> end

# ==============================================================================
# DAG 2: Cleanup HDFS (retention des fichiers Parquet)
# ==============================================================================
with DAG(
    dag_id='weekly_hdfs_cleanup',
    default_args=default_args,
    description='Nettoyage hebdomadaire des anciens fichiers HDFS',
    schedule_interval='0 4 * * 0',  # Dimanche a 4h00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'maintenance', 'hdfs', 'weekly'],
) as hdfs_cleanup_dag:

    start = EmptyOperator(task_id='start')

    check_hdfs_usage = BashOperator(
        task_id='check_hdfs_usage',
        bash_command="""
        echo "=== HDFS Disk Usage ==="
        docker exec proctorwise-namenode hdfs dfs -du -h /proctorwise/
        echo ""
        echo "=== HDFS Report ==="
        docker exec proctorwise-namenode hdfs dfsadmin -report 2>/dev/null | head -20
        """,
    )

    cleanup_old_anomaly_reports = BashOperator(
        task_id='cleanup_old_anomaly_reports',
        bash_command="""
        # Garder les 90 derniers jours de rapports anomalies
        CUTOFF_DATE=$(date -d '90 days ago' +%Y/%m 2>/dev/null || date -v-90d +%Y/%m 2>/dev/null || echo "")
        if [ -z "$CUTOFF_DATE" ]; then
          echo "SKIP: Could not compute cutoff date"
          exit 0
        fi

        echo "Cleaning anomaly reports older than $CUTOFF_DATE"
        YEARS=$(docker exec proctorwise-namenode hdfs dfs -ls /proctorwise/processed/anomaly_reports/ 2>/dev/null | awk '{print $NF}' | grep -oP '\\d{4}$' || true)
        for YEAR in $YEARS; do
          MONTHS=$(docker exec proctorwise-namenode hdfs dfs -ls /proctorwise/processed/anomaly_reports/$YEAR/ 2>/dev/null | awk '{print $NF}' | grep -oP '\\d{2}$' || true)
          for MONTH in $MONTHS; do
            if [ "$YEAR/$MONTH" \< "$CUTOFF_DATE" ]; then
              echo "Deleting /proctorwise/processed/anomaly_reports/$YEAR/$MONTH"
              docker exec proctorwise-namenode hdfs dfs -rm -r -f /proctorwise/processed/anomaly_reports/$YEAR/$MONTH
            fi
          done
        done
        echo "Anomaly report cleanup done"
        """,
    )

    cleanup_old_grading_results = BashOperator(
        task_id='cleanup_old_grading_results',
        bash_command="""
        # Garder les 6 derniers mois de resultats de notation
        CUTOFF_YEAR=$(date -d '180 days ago' +%Y 2>/dev/null || date -v-180d +%Y 2>/dev/null || echo "")
        if [ -z "$CUTOFF_YEAR" ]; then
          echo "SKIP: Could not compute cutoff date"
          exit 0
        fi

        echo "Cleaning grading results older than 6 months"
        docker exec proctorwise-namenode hdfs dfs -ls /proctorwise/processed/grading_results/ 2>/dev/null | awk '{print $NF}' | while read YEARPATH; do
          YEAR=$(basename $YEARPATH)
          if [ "$YEAR" -lt "$CUTOFF_YEAR" ] 2>/dev/null; then
            echo "Deleting $YEARPATH"
            docker exec proctorwise-namenode hdfs dfs -rm -r -f $YEARPATH
          fi
        done
        echo "Grading results cleanup done"
        """,
    )

    end = EmptyOperator(task_id='end')

    start >> check_hdfs_usage >> [cleanup_old_anomaly_reports, cleanup_old_grading_results] >> end

# ==============================================================================
# DAG 3: Monitoring systeme (disque, containers, services)
# ==============================================================================
with DAG(
    dag_id='system_health_check',
    default_args=default_args,
    description='Verification de sante du systeme toutes les 6 heures',
    schedule_interval='0 */6 * * *',  # Toutes les 6 heures
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'maintenance', 'monitoring'],
) as health_dag:

    start = EmptyOperator(task_id='start')

    check_disk_space = BashOperator(
        task_id='check_disk_space',
        bash_command="""
        echo "=== Docker Disk Usage ==="
        docker system df

        echo ""
        echo "=== Host Disk Usage ==="
        df -h / | tail -1

        USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
        echo "Disk usage: ${USAGE}%"

        if [ "$USAGE" -gt 90 ]; then
          echo "CRITICAL: Disk usage above 90%!"
          docker system prune -f --volumes
          echo "Docker prune executed"
        elif [ "$USAGE" -gt 80 ]; then
          echo "WARNING: Disk usage above 80%"
          docker system prune -f
          echo "Docker prune (no volumes) executed"
        else
          echo "OK: Disk usage normal"
        fi
        """,
    )

    check_containers = BashOperator(
        task_id='check_containers',
        bash_command="""
        echo "=== Container Status ==="
        docker compose -f /opt/airflow/dags/../../../docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || \
        docker ps --format "table {{.Names}}\t{{.Status}}" --filter "name=proctorwise"

        echo ""
        echo "=== Unhealthy Containers ==="
        UNHEALTHY=$(docker ps --filter "health=unhealthy" --filter "name=proctorwise" --format "{{.Names}}" 2>/dev/null || true)
        if [ -n "$UNHEALTHY" ]; then
          echo "WARNING: Unhealthy containers found:"
          echo "$UNHEALTHY"
          for C in $UNHEALTHY; do
            echo "Restarting $C..."
            docker restart "$C"
          done
        else
          echo "OK: All containers healthy"
        fi
        """,
    )

    check_services = BashOperator(
        task_id='check_services',
        bash_command="""
        echo "=== Service Health Checks ==="
        SERVICES="localhost:8001 localhost:8000 localhost:8003 localhost:8004 localhost:8005 localhost:8006"
        NAMES="UserService ReservationService MonitoringService CorrectionService NotificationService AnalyticsService"

        i=0
        for SVC in $SERVICES; do
          NAME=$(echo $NAMES | cut -d' ' -f$((i+1)))
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$SVC/health" --max-time 5 2>/dev/null || echo "000")
          if [ "$STATUS" = "200" ]; then
            echo "OK: $NAME ($SVC) - HTTP $STATUS"
          else
            echo "FAIL: $NAME ($SVC) - HTTP $STATUS"
          fi
          i=$((i+1))
        done

        echo ""
        echo "=== Airflow Scheduler ==="
        SCHEDULER=$(docker exec proctorwise-airflow airflow jobs check --job-type SchedulerJob --hostname "" 2>/dev/null && echo "OK" || echo "FAIL")
        echo "Scheduler: $SCHEDULER"
        """,
    )

    check_hdfs = BashOperator(
        task_id='check_hdfs',
        bash_command="""
        echo "=== HDFS Health ==="
        docker exec proctorwise-namenode hdfs dfsadmin -report 2>/dev/null | head -15 || echo "FAIL: HDFS not reachable"

        echo ""
        echo "=== HDFS Safe Mode ==="
        SAFEMODE=$(docker exec proctorwise-namenode hdfs dfsadmin -safemode get 2>/dev/null || echo "unknown")
        echo "$SAFEMODE"
        """,
    )

    end = EmptyOperator(task_id='end')

    start >> [check_disk_space, check_containers, check_services, check_hdfs] >> end

# ==============================================================================
# DAG 4: Initialisation HDFS (trigger manuel, une seule fois)
# ==============================================================================
with DAG(
    dag_id='init_hdfs_structure',
    default_args=default_args,
    description='Initialise la structure de repertoires HDFS (trigger manuel)',
    schedule_interval=None,  # Trigger manuel uniquement
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['proctorwise', 'maintenance', 'hdfs', 'init'],
) as init_hdfs_dag:

    start = EmptyOperator(task_id='start')

    wait_hdfs_ready = BashOperator(
        task_id='wait_hdfs_ready',
        bash_command="""
        echo "Waiting for HDFS to be ready..."
        for i in $(seq 1 30); do
          if docker exec proctorwise-namenode hdfs dfsadmin -safemode get 2>/dev/null | grep -q "OFF"; then
            echo "HDFS is ready (safe mode OFF)"
            exit 0
          fi
          echo "Attempt $i/30 - HDFS not ready yet..."
          sleep 10
        done
        echo "ERROR: HDFS not ready after 5 minutes"
        exit 1
        """,
        execution_timeout=timedelta(minutes=6),
    )

    create_directories = BashOperator(
        task_id='create_hdfs_directories',
        bash_command="""
        echo "Creating HDFS directory structure..."

        DIRS="
          /proctorwise/raw/frames
          /proctorwise/raw/recordings
          /proctorwise/processed/anomaly_reports
          /proctorwise/processed/grading_results
          /proctorwise/processed/user_performance
          /proctorwise/ml/models
          /proctorwise/archive
        "

        for DIR in $DIRS; do
          docker exec proctorwise-namenode hdfs dfs -mkdir -p $DIR
          echo "Created: $DIR"
        done

        docker exec proctorwise-namenode hdfs dfs -chmod -R 755 /proctorwise
        echo "Permissions set to 755"

        echo ""
        echo "=== HDFS Structure ==="
        docker exec proctorwise-namenode hdfs dfs -ls -R /proctorwise/
        """,
    )

    end = EmptyOperator(task_id='end')

    start >> wait_hdfs_ready >> create_directories >> end
