# 🇧🇴 DataGob-IA — Sistema Nacional Integrado de Datos Gubernamentales de Bolivia

> **Plataforma de Data Science & IA para la integración, gobernanza y análisis de datos poblacionales del Estado Plurinacional de Bolivia.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5-orange?logo=apachespark)](https://spark.apache.org)
[![Airflow](https://img.shields.io/badge/Airflow-2.9-red?logo=apacheairflow)](https://airflow.apache.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Problema

Bolivia opera con datos poblacionales **fragmentados y desconectados** entre más de 30 instituciones gubernamentales:

| Institución | Datos que maneja |
|---|---|
| SEGIP | Carnets de Identidad (CI) |
| SERECI | Certificados de Nacimiento / Defunción |
| Ministerio de Educación | Títulos académicos |
| Ministerio de Salud | Historia clínica |
| UDAPE / INE | Estadísticas socioeconómicas |
| SIN | Datos tributarios (NIT) |
| AFP / Gobiernos Municipales | Bonos sociales |
| TSJ / Magistratura | Registros judiciales |
| Gobernaciones / Alcaldías | Registros locales |

**Consecuencias reales:**
- ❌ No se sabe con exactitud cuántos bolivianos somos
- ❌ Personas cobran bonos (Renta Dignidad, Bono Juancito Pinto) en Bolivia **y** en países vecinos
- ❌ Títulos profesionales falsificados sin detección
- ❌ Personas fallecidas en registros activos
- ❌ Duplicidad de identidades y fraude documental
- ❌ Imposibilidad de políticas públicas basadas en datos reales

---

## 🏗️ Solución: DataGob-IA

Una **plataforma centralizada de alta seguridad** que integra, limpia, cruza y analiza los datos de todas las instituciones usando técnicas modernas de Data Engineering e Inteligencia Artificial, con acceso **ultra-restringido** y gobernanza multinivel.

### Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                    DataGob-IA Platform                          │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Ingesta  │→ │  Lake    │→ │ ML / IA  │→ │  Dashboard   │   │
│  │  ETL     │  │ (Delta)  │  │ Modelos  │  │  Gov Access  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│        ↑              ↑            ↑               ↑           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Capa de Seguridad & Auditoría                  │  │
│  │    Zero-Trust | MFA | Cifrado AES-256 | RBAC | Logs      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
DataGob-IA/
├── data/
│   ├── raw/                    # Datos crudos simulados por institución
│   ├── processed/              # Datos limpios y normalizados
│   └── synthetic/              # Datos sintéticos para desarrollo/tests
├── src/
│   ├── ingestion/              # Conectores ETL por institución
│   ├── processing/             # Limpieza, deduplicación, normalización
│   ├── ml_models/              # Modelos de IA (fraude, deduplicación, NLP)
│   ├── api/                    # FastAPI REST API (acceso controlado)
│   ├── governance/             # RBAC, auditoría, control de acceso
│   └── utils/                  # Utilidades compartidas
├── notebooks/
│   ├── 01_eda_population.ipynb
│   ├── 02_deduplication_analysis.ipynb
│   ├── 03_fraud_detection.ipynb
│   ├── 04_social_bonus_crosscheck.ipynb
│   └── 05_population_dashboard.ipynb
├── dags/                       # Apache Airflow DAGs
├── tests/                      # Unit & integration tests
├── docker/                     # Dockerfiles por servicio
├── infra/                      # Terraform / IaC
├── docs/                       # Documentación técnica
├── dashboard/                  # Frontend React (Gov Dashboard)
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Ingesta ETL** | Apache Airflow + Python + dbt |
| **Procesamiento** | Apache Spark (PySpark) |
| **Storage** | Delta Lake (MinIO / S3) |
| **ML / IA** | Scikit-learn, XGBoost, Sentence-Transformers, spaCy |
| **API** | FastAPI + OAuth2 + JWT |
| **Seguridad** | Vault (HashiCorp), AES-256, RBAC, Audit Logs |
| **Monitoreo** | Grafana + Prometheus + Great Expectations |
| **Orquestación** | Docker Compose / Kubernetes |
| **Frontend** | React + TypeScript + Recharts |
| **DB** | PostgreSQL (metadata) + Redis (cache) |

---

## 🔐 Modelo de Seguridad

- **Zero-Trust Architecture**: Todo acceso requiere autenticación, sin importar origen
- **Multi-Factor Authorization (MFA)**: Mínimo 3 autoridades deben aprobar consultas sensibles
- **RBAC granular**: 5 niveles de acceso (Operador → Analista → Supervisor → Autoridad → Super Admin)
- **Cifrado end-to-end**: AES-256 en reposo, TLS 1.3 en tránsito
- **Audit trail inmutable**: Cada consulta queda registrada con hash
- **Data Masking**: PII enmascarada por defecto, desenmascara solo con permiso multinivel

---

## 📊 Modelos de IA incluidos

1. **Deduplicador de Identidades** — Record Linkage con Blocking + ML
2. **Detector de Fraude en Bonos** — Cruce transfronterizo, anomaly detection
3. **Verificador de Títulos** — NLP + similitud semántica
4. **Estimador Poblacional** — Modelado estadístico con datos incompletos
5. **Detector de Personas Fallecidas Activas** — Cross-matching SERECI/SEGIP

---

## 🛠️ Instalación

```bash
# Clonar el repositorio
git clone https://github.com/aDavidBravo/DataGob-IA.git
cd DataGob-IA

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\Activate.ps1  # Windows PowerShell

# Instalar dependencias
pip install -r requirements.txt

# Generar datos sintéticos
python src/utils/data_generator.py

# Levantar servicios
docker-compose up -d

# Ejecutar pipeline ETL
python src/ingestion/run_pipeline.py

# Iniciar API
uvicorn src.api.main:app --reload
```

---

## 👤 Autor

**David Bravo** — Senior Data Scientist  
🇧🇴 La Paz, Bolivia  
📧 data.gov.bolivia@proton.me  
🔗 [github.com/aDavidBravo](https://github.com/aDavidBravo)

---

## 📄 Licencia

MIT License — Ver [LICENSE](LICENSE)

> ⚠️ *Este proyecto utiliza datos 100% sintéticos generados para fines de demostración técnica. No contiene información real de ciudadanos bolivianos.*
