# DataGob-IA - Arquitectura Técnica

## Visión General

DataGob-IA es una plataforma de **Data Engineering + ML** diseñada para integrar y analizar los datos poblacionales fragmentados de Bolivia. El sistema procesa datos de más de 30 instituciones gubernamentales para generar una fuente única de verdad sobre la población boliviana.

---

## Stack Tecnológico Detallado

### Ingesta y ETL
- **Apache Airflow 2.9**: Orquestación de pipelines. DAG diario a las 2 AM
- **Python + Pandas**: Conectores por institución (SEGIP, SERECI, MINEDU, etc.)
- **dbt**: Transformaciones SQL declarativas sobre el Data Warehouse

### Almacenamiento (Arquitectura Medallion)
```
Bronze Layer → Silver Layer → Gold Layer
(Raw)          (Cleaned)       (Business-ready)
```
- **MinIO**: Object storage compatible con S3
- **Delta Lake**: Formato de tabla con ACID transactions y time travel
- **PostgreSQL**: Metadata, usuarios, audit logs
- **Redis**: Caché de resultados frecuentes

### Machine Learning

| Modelo | Algoritmo | Problema |
|--------|-----------|----------|
| Deduplicador | XGBoost + Record Linkage | Identidades duplicadas |
| Detector de Fraude | Isolation Forest + Reglas | Fraude en bonos |
| Verificador de Títulos | Sentence Transformers | Falsificación de diplomas |
| Estimador Poblacional | Bayesian Estimation | Conteo real de población |
| Detector Fallecidos | Cross-matching | Muertos activos en sistema |

### API y Acceso
- **FastAPI**: REST API con OpenAPI/Swagger
- **OAuth2 + JWT**: Autenticación stateless
- **RBAC**: 5 niveles de acceso
- **Rate limiting**: Por usuario y por endpoint

### Seguridad
- **Zero-Trust**: Toda solicitud se autentica
- **AES-256**: Cifrado de datos en reposo
- **TLS 1.3**: Cifrado en tránsito
- **Audit Log inmutable**: SHA-256, no DELETE/UPDATE
- **MFA multinivel**: Para consultas de datos individuales
- **Data Masking**: PII por defecto enmascarada

### Monitoreo
- **Grafana + Prometheus**: Métricas del sistema
- **Great Expectations**: Calidad de datos
- **Loguru**: Logging estructurado

---

## Flujo de Datos

```
Institución A (SEGIP)  ┐
Institución B (SERECI) ├─► Airflow ETL ► Bronze Lake ► Cleaning ► Silver Lake
Institución C (MINEDU) ┘
                                                                      ↓
                                                               ML Models
                                                          (Dedup, Fraude, NLP)
                                                                      ↓
                                                               Gold Layer
                                                                      ↓
                                                          FastAPI (RBAC)
                                                                      ↓
                                                         Dashboard Gov
```

---

## Modelo de Gobernanza de Datos

### Niveles de Acceso

| Rol | Nivel | Acceso |
|-----|-------|--------|
| Operador | 1 | Estadísticas nacionales agregadas |
| Analista | 2 | Datos anonimizados por departamento |
| Supervisor | 3 | Alertas de fraude + datos por municipio |
| Autoridad | 4 | Registros individuales (requiere MFA) |
| SuperAdmin | 5 | Administración total del sistema |

### Política de Retención
- Datos crudos: 7 años (cumplimiento legal)
- Logs de auditoría: Indefinido (inmutables)
- Caché: 24 horas

### GDPR / Ley de Protección de Datos Bolivia
- Datos PII enmascarados por defecto
- Derecho al acceso solo vía proceso legal
- Cifrado end-to-end obligatorio

---

## Despliegue de Producción

El sistema está diseñado para desplegarse en:
- **Hardware dedicado** en Data Center Gubernamental
- **Kubernetes** para orquestación de contenedores
- **Red aislada** (air-gap opcional para datos críticos)
- **Backup diario cifrado** en ubicación secundaria

---

## KPIs del Sistema

- Tasa de deduplicación: >95% precisión
- Detección de fraude: >92% recall
- Disponibilidad: 99.9% SLA
- Latencia API: <200ms p95
- Frescura de datos: Actualización diaria
