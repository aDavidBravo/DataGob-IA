"""
DataGob-IA FastAPI - REST API con seguridad multinivel
Acceso ultra-restringido con RBAC, JWT y auditoría inmutable
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from loguru import logger
import uuid
import hashlib
import json

# ─── Config ────────────────────────────────────────────────────────────
SECRET_KEY = "change_this_to_a_secure_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# ─── RBAC Roles ──────────────────────────────────────────────────────
ROLES = {
    "operador": 1,       # Solo lectura de estadísticas agregadas
    "analista": 2,       # Consultas con datos anonimizados
    "supervisor": 3,     # Datos desenmascardos por departamento
    "autoridad": 4,      # Acceso a registros individuales (requiere MFA)
    "superadmin": 5,     # Acceso total + administración del sistema
}

# DB simulada de usuarios
FAKE_USERS_DB = {
    "analista01": {
        "username": "analista01",
        "hashed_password": pwd_context.hash("Demo2024!"),
        "role": "analista",
        "institucion": "INE",
        "activo": True,
    },
    "supervisor01": {
        "username": "supervisor01",
        "hashed_password": pwd_context.hash("Supervisor2024!"),
        "role": "supervisor",
        "institucion": "SEGIP",
        "activo": True,
    },
}

# ─── Modelos Pydantic ───────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    expires_at: str


class PopulationStats(BaseModel):
    total_registros: int
    total_ci_activos: int
    total_fallecidos: int
    duplicados_estimados: int
    por_departamento: dict
    fuente: str
    timestamp: str


class FraudAlert(BaseModel):
    id_alerta: str
    tipo: str
    descripcion: str
    severidad: str  # CRITICA | ALTA | MEDIA | BAJA
    departamento: Optional[str]
    timestamp: str
    requiere_investigacion: bool


class AuditLog(BaseModel):
    id_log: str
    usuario: str
    endpoint: str
    timestamp: str
    ip: str
    resultado: str
    hash_verificacion: str


# ─── Auth utils ──────────────────────────────────────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = FAKE_USERS_DB.get(username)
    if user is None or not user["activo"]:
        raise credentials_exception
    return user


def require_role(minimum_role: str):
    """Dependency factory para control de acceso por rol."""
    def checker(current_user: dict = Depends(get_current_user)):
        user_role_level = ROLES.get(current_user["role"], 0)
        required_level = ROLES.get(minimum_role, 99)
        if user_role_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Rol requerido: {minimum_role}"
            )
        return current_user
    return checker


def create_audit_entry(request: Request, user: dict, resultado: str) -> AuditLog:
    """Crea entrada de auditoría inmutable con hash."""
    timestamp = datetime.utcnow().isoformat()
    endpoint = str(request.url.path)
    ip = request.client.host if request.client else "unknown"

    raw = f"{user['username']}|{endpoint}|{timestamp}|{ip}|{resultado}"
    hash_v = hashlib.sha256(raw.encode()).hexdigest()

    return AuditLog(
        id_log=str(uuid.uuid4()),
        usuario=user["username"],
        endpoint=endpoint,
        timestamp=timestamp,
        ip=ip,
        resultado=resultado,
        hash_verificacion=hash_v,
    )


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DataGob-IA API",
    description="Sistema Nacional Integrado de Datos Gubernamentales de Bolivia",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Solo frontend autorizado
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─── Endpoints ─────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "sistema": "DataGob-IA",
        "version": "1.0.0",
        "descripcion": "Sistema Nacional Integrado de Datos Gubernamentales - Bolivia",
        "estado": "operativo",
        "acceso": "restringido",
    }


@app.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        logger.warning(f"Intento de login fallido: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": user["username"], "role": user["role"]}, expire)
    logger.info(f"Login exitoso: {user['username']} [{user['role']}]")

    return Token(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        expires_at=(datetime.utcnow() + expire).isoformat(),
    )


@app.get("/v1/poblacion/stats", response_model=PopulationStats)
async def get_population_stats(
    request: Request,
    current_user: dict = Depends(require_role("analista"))
):
    """Estadísticas agregadas de población (datos anonimizados)."""
    audit = create_audit_entry(request, current_user, "OK")
    logger.info(f"AUDIT: {audit.hash_verificacion}")

    # Datos simulados agregados (nunca datos individuales en este endpoint)
    return PopulationStats(
        total_registros=12_847_234,
        total_ci_activos=11_203_891,
        total_fallecidos=1_643_343,
        duplicados_estimados=287_421,
        por_departamento={
            "La Paz": 2_890_000,
            "Cochabamba": 1_980_000,
            "Santa Cruz": 3_420_000,
            "Oruro": 510_000,
            "Potosí": 830_000,
            "Chuquisaca": 640_000,
            "Tarija": 580_000,
            "Beni": 470_000,
            "Pando": 125_000,
        },
        fuente="SEGIP + SERECI + INE",
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/v1/fraude/alertas", response_model=List[FraudAlert])
async def get_fraud_alerts(
    request: Request,
    severidad: Optional[str] = None,
    current_user: dict = Depends(require_role("supervisor"))
):
    """Lista de alertas de fraude activas. Requiere rol Supervisor+."""
    audit = create_audit_entry(request, current_user, "OK")
    logger.info(f"Alertas consultadas por {current_user['username']} | Audit: {audit.hash_verificacion}")

    alertas = [
        FraudAlert(
            id_alerta=str(uuid.uuid4()),
            tipo="FALLECIDO_COBRANDO_BONO",
            descripcion="4,832 personas con certificado de defunción registran cobros activos de Renta Dignidad",
            severidad="CRITICA",
            departamento="Nacional",
            timestamp=datetime.utcnow().isoformat(),
            requiere_investigacion=True,
        ),
        FraudAlert(
            id_alerta=str(uuid.uuid4()),
            tipo="COBRO_TRANSFRONTERIZO",
            descripcion="2,341 beneficiarios detectados cobrando bonos en Bolivia y Chile/Argentina simultáneamente",
            severidad="CRITICA",
            departamento=None,
            timestamp=datetime.utcnow().isoformat(),
            requiere_investigacion=True,
        ),
        FraudAlert(
            id_alerta=str(uuid.uuid4()),
            tipo="TITULO_FALSO_DETECTADO",
            descripcion="891 títulos universitarios sin respaldo en registro oficial MINEDU detectados por modelo NLP",
            severidad="ALTA",
            departamento=None,
            timestamp=datetime.utcnow().isoformat(),
            requiere_investigacion=True,
        ),
        FraudAlert(
            id_alerta=str(uuid.uuid4()),
            tipo="CI_DUPLICADO",
            descripcion="45,231 pares de CI potencialmente duplicados detectados por modelo de deduplicación",
            severidad="ALTA",
            departamento=None,
            timestamp=datetime.utcnow().isoformat(),
            requiere_investigacion=False,
        ),
    ]

    if severidad:
        alertas = [a for a in alertas if a.severidad == severidad.upper()]

    return alertas


@app.get("/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
