# Guía de Instalación y Despliegue

## Requisitos Previos

- Python 3.11+
- Docker + Docker Compose
- Git
- PowerShell 7+ (Windows) o Bash (Linux/Mac)
- 16GB RAM mínimo recomendado
- 50GB disco disponible

---

## Instalación Rápida

### 1. Clonar el repositorio

```powershell
git clone https://github.com/aDavidBravo/DataGob-IA.git
cd DataGob-IA
```

### 2. Configurar variables de entorno

```powershell
Copy-Item .env.example .env
# Editar .env con tus valores seguros
notepad .env
```

### 3. Crear entorno virtual Python

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Generar datos sintéticos

```powershell
python src/utils/data_generator.py
```

### 5. Levantar infraestructura Docker

```powershell
docker-compose up -d
```

Verificar que todos los servicios estén corriendo:

```powershell
docker-compose ps
```

### 6. Iniciar la API

```powershell
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Acceder a los servicios

| Servicio | URL | Credenciales |
|----------|-----|---|
| **API Docs** | http://localhost:8000/docs | - |
| **Airflow** | http://localhost:8080 | admin/admin |
| **MinIO Console** | http://localhost:9001 | minioadmin/MinioGob2024! |
| **Grafana** | http://localhost:3000 | admin/GrafanaGob2024! |

---

## Ejecutar Tests

```powershell
pytest tests/ -v --cov=src --cov-report=html
```

---

## Ejecutar Modelos ML

```powershell
# Deduplicación
python src/ml_models/deduplicator.py

# Detección de fraude
python src/ml_models/fraud_detector.py

# Verificación de títulos (descarga modelo NLP ~400MB)
python src/ml_models/titulo_verifier.py
```

---

## Troubleshooting

### Error: Puerto en uso
```powershell
# Verificar qué usa el puerto
netstat -ano | findstr :8000
```

### Error: Docker no inicia
```powershell
# Verificar Docker Desktop está corriendo
docker info
docker-compose logs
```

### Error: Módulos no encontrados
```powershell
# Asegurar entorno virtual activo
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade
```
