"""
airflow/dags/ca_facility_dag.py

Airflow DAG that runs the entire CA Facility pipeline
automatically every month in this order:
  1. Download CDPH CSV files
  2. Load into PostgreSQL
  3. Run PySpark transformation
  4. Run dbt models
  5. Run dbt tests
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "ca_facility_pipeline",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="ca_facility_pipeline",
    default_args=default_args,
    description="Monthly CA Healthcare Facility data pipeline",
    schedule_interval="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["healthcare", "california", "cdph"],
) as dag:

    # Step 1 — Download
    download_task = BashOperator(
        task_id="download_cdph_files",
        bash_command="cd /opt/airflow && python ingestion/downloader.py",
    )

    # Step 2 — Load to Postgres
    load_task = BashOperator(
        task_id="load_to_postgres",
        bash_command="cd /opt/airflow && python ingestion/loader.py",
    )

    # Step 3 — PySpark transform
    spark_task = BashOperator(
        task_id="spark_transform",
        bash_command="cd /opt/airflow && python spark/spark_transform.py",
    )

    # Step 4 — dbt run
    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/ca_facility_dbt && dbt run",
    )

    # Step 5 — dbt test
    dbt_test_task = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/ca_facility_dbt && dbt test",
    )

    # Define order — each step runs after the previous one
    download_task >> load_task >> spark_task >> dbt_run_task >> dbt_test_task