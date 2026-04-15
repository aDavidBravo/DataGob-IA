# ────────────────────────────────────────────────────────────────────
# DataGob-IA — Makefile de utilidades
# ────────────────────────────────────────────────────────────────────

.PHONY: install setup generate-data api test lint docker-up docker-down clean

# Instalación de dependencias
install:
	pip install -r requirements.txt

# Setup completo (instalar + generar datos)
setup: install generate-data
	@echo "Setup completado!"

# Generar datos sintéticos
generate-data:
	python src/utils/data_generator.py

# Iniciar API
api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar tests
test:
	pytest tests/ -v --cov=src --cov-report=term-missing

# Linting
lint:
	black src/ tests/
	isort src/ tests/
	flake8 src/ tests/

# Docker
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Ejecutar modelos ML
run-dedup:
	python src/ml_models/deduplicator.py

run-fraud:
	python src/ml_models/fraud_detector.py

run-titulos:
	python src/ml_models/titulo_verifier.py

# Limpieza
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache/ htmlcov/ .coverage
