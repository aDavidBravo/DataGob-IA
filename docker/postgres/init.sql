-- DataGob-IA PostgreSQL Schema
-- Esquema principal del sistema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Schema separado para auditoría (inmutable)
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS datagob;

-- ── Tabla de Usuarios del Sistema ─────────────────────────────────────────────
CREATE TABLE datagob.usuarios (
    id_usuario UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('operador', 'analista', 'supervisor', 'autoridad', 'superadmin')),
    institucion VARCHAR(100) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT NOW(),
    ultimo_acceso TIMESTAMP,
    intentos_fallidos INT DEFAULT 0,
    bloqueado_hasta TIMESTAMP
);

-- ── Tabla de Alertas de Fraude ───────────────────────────────────────────────
CREATE TABLE datagob.alertas_fraude (
    id_alerta UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    severidad VARCHAR(10) NOT NULL CHECK (severidad IN ('CRITICA', 'ALTA', 'MEDIA', 'BAJA')),
    departamento VARCHAR(50),
    ci_involucrado VARCHAR(20),
    monto_bs DECIMAL(12, 2),
    estado VARCHAR(20) DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'EN_INVESTIGACION', 'RESUELTA', 'FALSO_POSITIVO')),
    creado_en TIMESTAMP DEFAULT NOW(),
    resuelto_en TIMESTAMP,
    resuelto_por UUID REFERENCES datagob.usuarios(id_usuario)
);

-- ── Tabla de Duplicados Detectados ────────────────────────────────────────────
CREATE TABLE datagob.duplicados (
    id_duplicado UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ci_1 VARCHAR(20) NOT NULL,
    ci_2 VARCHAR(20) NOT NULL,
    nombre_1 TEXT,
    nombre_2 TEXT,
    probabilidad_match DECIMAL(5, 4) NOT NULL,
    fuente_1 VARCHAR(50),
    fuente_2 VARCHAR(50),
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    detectado_en TIMESTAMP DEFAULT NOW()
);

-- ── Audit Log Inmutable (no se puede DELETE ni UPDATE) ──────────────────────
CREATE TABLE audit.access_log (
    id_log UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    ip_origen INET,
    timestamp TIMESTAMP DEFAULT NOW(),
    resultado VARCHAR(20) NOT NULL,
    hash_verificacion TEXT NOT NULL -- SHA-256 para integridad
);

-- Revocar permisos de UPDATE/DELETE en audit log (inmutabilidad)
REVOKE UPDATE, DELETE ON audit.access_log FROM PUBLIC;
REVOKE UPDATE, DELETE ON audit.access_log FROM datagob;

-- ── Estadísticas Diarias (vista materializada) ─────────────────────────────
CREATE TABLE datagob.estadisticas_diarias (
    fecha DATE PRIMARY KEY DEFAULT CURRENT_DATE,
    total_registros BIGINT,
    total_alertas_criticas INT,
    total_duplicados INT,
    titulos_sospechosos INT,
    bonos_irregulares INT,
    actualizado_en TIMESTAMP DEFAULT NOW()
);

-- Insertar fila inicial de ejemplo
INSERT INTO datagob.estadisticas_diarias VALUES (
    CURRENT_DATE, 12847234, 7, 45231, 891, 7173, NOW()
);

SELECT 'DataGob-IA schema inicializado correctamente' AS status;
