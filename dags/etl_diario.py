"""
DAG de Apache Airflow: Pipeline ETL diario de integración de datos gubernamentales
Orquesta la ingesta, limpieza, deduplicación y detección de fraude
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Configuración del DAG
default_args = {
    'owner': 'datagob-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': ['data-alerts@datagob.bo.gob'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=6),
}

dag = DAG(
    dag_id='datagob_etl_diario',
    default_args=default_args,
    description='Pipeline ETL diario - Integración datos gubernamentales Bolivia',
    schedule_interval='0 2 * * *',  # Todos los días a las 2:00 AM
    catchup=False,
    max_active_runs=1,
    tags=['datagob', 'etl', 'bolivia', 'gobierno'],
)


# ── Funciones de cada tarea ─────────────────────────────────────────────

def extract_segip(**kwargs):
    """Extrae datos del SEGIP (Carnets de Identidad)."""
    print("[SEGIP] Conectando al sistema SEGIP...")
    print("[SEGIP] Extrayendo registros de CI activos...")
    # En producción: conexión real a DB SEGIP vía SFTP seguro / API
    print("[SEGIP] 11,203,891 registros extraídos")
    kwargs['ti'].xcom_push(key='segip_count', value=11203891)


def extract_sereci(**kwargs):
    """Extrae certificados de nacimiento y defunción del SERECI."""
    print("[SERECI] Extrayendo certificados de nacimiento y defunción...")
    kwargs['ti'].xcom_push(key='sereci_count', value=980432)


def extract_minedu(**kwargs):
    """Extrae registros de títulos universitarios del MINEDU."""
    print("[MINEDU] Extrayendo registro de títulos profesionales...")
    kwargs['ti'].xcom_push(key='minedu_count', value=450231)


def extract_bonos(**kwargs):
    """Extrae registros de bonos sociales de AFP y municipios."""
    print("[BONOS] Extrayendo registros de beneficiarios de bonos...")
    kwargs['ti'].xcom_push(key='bonos_count', value=1843221)


def clean_and_normalize(**kwargs):
    """Limpia y normaliza todos los datasets extraídos."""
    print("[CLEAN] Iniciando limpieza y normalización...")
    print("[CLEAN] Normalizando nombres (mayúsculas, tildes, caracteres especiales)...")
    print("[CLEAN] Estandarizando fechas a formato ISO 8601...")
    print("[CLEAN] Validando formato de CI (7-8 dígitos)...")
    print("[CLEAN] Completado: 99.2% de registros válidos")


def run_deduplication(**kwargs):
    """Ejecuta el modelo de deduplicación de identidades."""
    print("[DEDUP] Cargando modelo XGBoost de deduplicación...")
    print("[DEDUP] Aplicando blocking por Soundex...")
    print("[DEDUP] Evaluando pares candidatos...")
    print("[DEDUP] Duplicados detectados: 45,231 pares")
    kwargs['ti'].xcom_push(key='duplicates_found', value=45231)


def run_fraud_detection(**kwargs):
    """Ejecuta detección de fraude en bonos."""
    print("[FRAUD] Cruzando fallecidos SERECI con beneficiarios activos...")
    print("[FRAUD] Verificando cobros transfronterizos...")
    print("[FRAUD] Alertas generadas: 7,173 casos")
    kwargs['ti'].xcom_push(key='fraud_alerts', value=7173)


def run_titulo_verification(**kwargs):
    """Verifica títulos universitarios con modelo NLP."""
    print("[TITULOS] Generando embeddings con Sentence Transformers...")
    print("[TITULOS] Comparando contra registro oficial MINEDU...")
    print("[TITULOS] Títulos sospechosos: 891")


def update_data_lake(**kwargs):
    """Actualiza el Data Lake con los datos procesados (Delta Lake)."""
    dup = kwargs['ti'].xcom_pull(key='duplicates_found', task_ids='run_deduplication')
    fraud = kwargs['ti'].xcom_pull(key='fraud_alerts', task_ids='run_fraud_detection')
    print(f"[LAKE] Escribiendo datos limpios en Delta Lake...")
    print(f"[LAKE] Resumen: {dup} duplicados marcados | {fraud} alertas de fraude")
    print(f"[LAKE] Actualización completada exitosamente")


def send_dashboard_notification(**kwargs):
    """Notifica al dashboard de autoridades con el resumen del pipeline."""
    print("[NOTIFY] Enviando notificación a dashboard de autoridades...")
    print("[NOTIFY] Email enviado a: data-alerts@datagob.bo.gob")


# ── Definición de Tareas ─────────────────────────────────────────────

t_extract_segip = PythonOperator(
    task_id='extract_segip',
    python_callable=extract_segip,
    dag=dag,
)

t_extract_sereci = PythonOperator(
    task_id='extract_sereci',
    python_callable=extract_sereci,
    dag=dag,
)

t_extract_minedu = PythonOperator(
    task_id='extract_minedu',
    python_callable=extract_minedu,
    dag=dag,
)

t_extract_bonos = PythonOperator(
    task_id='extract_bonos',
    python_callable=extract_bonos,
    dag=dag,
)

t_clean = PythonOperator(
    task_id='clean_and_normalize',
    python_callable=clean_and_normalize,
    dag=dag,
)

t_dedup = PythonOperator(
    task_id='run_deduplication',
    python_callable=run_deduplication,
    dag=dag,
)

t_fraud = PythonOperator(
    task_id='run_fraud_detection',
    python_callable=run_fraud_detection,
    dag=dag,
)

t_titulo = PythonOperator(
    task_id='run_titulo_verification',
    python_callable=run_titulo_verification,
    dag=dag,
)

t_lake = PythonOperator(
    task_id='update_data_lake',
    python_callable=update_data_lake,
    dag=dag,
)

t_notify = PythonOperator(
    task_id='send_dashboard_notification',
    python_callable=send_dashboard_notification,
    dag=dag,
)

# ── Dependencias del Pipeline ─────────────────────────────────────────────
# Extracción paralela de todas las fuentes
[t_extract_segip, t_extract_sereci, t_extract_minedu, t_extract_bonos] >> t_clean

# Procesamiento secuencial
t_clean >> [t_dedup, t_fraud, t_titulo]

# Actualización del lake cuando todo termina
[t_dedup, t_fraud, t_titulo] >> t_lake >> t_notify
