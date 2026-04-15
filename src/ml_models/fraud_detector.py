"""
Detector de Fraude en Bonos Sociales

Modelo de ML para detectar:
1. Personas fallecidas cobrando bonos
2. Doble cobro en Bolivia y países vecinos
3. Beneficiarios fuera del rango etario
4. Patrones anómalos de cobro

Técnicas: Isolation Forest + XGBoost + Reglas de negocio
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import xgboost as xgb
from loguru import logger
from datetime import date
import pickle
from pathlib import Path
from typing import Tuple


def calculate_age(fecha_nacimiento: str) -> int:
    """Calcula la edad actual a partir de fecha de nacimiento."""
    try:
        dob = pd.to_datetime(fecha_nacimiento)
        today = pd.Timestamp.today()
        return int((today - dob).days / 365.25)
    except Exception:
        return -1


def apply_business_rules(df_bonos: pd.DataFrame, df_poblacion: pd.DataFrame,
                         df_defunciones: pd.DataFrame) -> pd.DataFrame:
    """
    Reglas de negocio duras para detección de fraude:
    - Renta Dignidad: solo mayores de 60
    - Bono Juancito Pinto: solo menores de 18
    - Cobro en exterior: flag automático
    - Fallecido cobrando: flag crítico
    """
    logger.info("Aplicando reglas de negocio para detección de fraude...")

    df = df_bonos.copy()

    # Merge con población
    if 'fecha_nacimiento' in df_poblacion.columns:
        df = df.merge(
            df_poblacion[['ci', 'fecha_nacimiento', 'vivo']],
            left_on='ci_beneficiario', right_on='ci', how='left'
        )
        df['edad'] = df['fecha_nacimiento'].apply(calculate_age)

    # CI de fallecidos
    ci_fallecidos = set(df_defunciones['ci_fallecido'].astype(str))

    # Flags de fraude
    df['fraude_fallecido'] = df['ci_beneficiario'].astype(str).isin(ci_fallecidos)
    df['fraude_exterior'] = df.get('cobrado_exterior', False).fillna(False)
    df['fraude_edad_renta'] = (
        (df['tipo_bono'] == 'Renta Dignidad') &
        (df['edad'].fillna(100) < 60)
    )
    df['fraude_edad_juancito'] = (
        (df['tipo_bono'] == 'Bono Juancito Pinto') &
        (df['edad'].fillna(0) >= 18)
    )
    df['fraude_vivo_inactivo'] = df.get('vivo', True).fillna(True) == False

    # Score compuesto
    df['fraude_score_reglas'] = (
        df['fraude_fallecido'].astype(int) * 100 +
        df['fraude_exterior'].astype(int) * 80 +
        df['fraude_edad_renta'].astype(int) * 60 +
        df['fraude_edad_juancito'].astype(int) * 60 +
        df['fraude_vivo_inactivo'].astype(int) * 90
    )

    df['es_fraude_reglas'] = df['fraude_score_reglas'] > 0

    n_fraude = df['es_fraude_reglas'].sum()
    logger.warning(f"Casos de fraude detectados por reglas: {n_fraude:,}")

    return df


def build_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construye features para el modelo ML."""
    features = pd.DataFrame()

    # Numéricas
    features['monto_bs'] = df['monto_bs'].fillna(0)
    features['edad'] = df.get('edad', pd.Series([-1] * len(df))).fillna(-1)
    features['fraude_score_reglas'] = df.get('fraude_score_reglas', 0).fillna(0)

    # Categóricas codificadas
    le = LabelEncoder()
    features['tipo_bono_enc'] = le.fit_transform(
        df['tipo_bono'].fillna('Desconocido')
    )
    features['departamento_enc'] = le.fit_transform(
        df.get('departamento', pd.Series(['Desconocido'] * len(df))).fillna('Desconocido')
    )

    # Flags binarios
    features['cobrado_exterior'] = df.get('cobrado_exterior', False).fillna(False).astype(int)
    features['activo'] = df.get('activo', True).fillna(True).astype(int)

    return features


def train_anomaly_detector(df_features: pd.DataFrame) -> IsolationForest:
    """Isolation Forest para detección de anomalías no supervisada."""
    logger.info("Entrenando Isolation Forest...")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_features)

    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=0.03,  # Esperamos ~3% de fraude
        random_state=42
    )
    iso_forest.fit(X_scaled)

    # Guardar scaler y modelo
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    with open(models_dir / 'fraud_isolation_forest.pkl', 'wb') as f:
        pickle.dump({'model': iso_forest, 'scaler': scaler}, f)

    scores = iso_forest.decision_function(X_scaled)
    n_anomalies = (iso_forest.predict(X_scaled) == -1).sum()
    logger.success(f"Anomalías detectadas: {n_anomalies:,} ({n_anomalies/len(df_features)*100:.1f}%)")

    return iso_forest, scaler


def generate_fraud_report(df_bonos_flagged: pd.DataFrame) -> dict:
    """Genera reporte ejecutivo de fraude detectado."""
    report = {
        'total_registros': len(df_bonos_flagged),
        'total_fraude_detectado': int(df_bonos_flagged.get('es_fraude_reglas', pd.Series([False]*len(df_bonos_flagged))).sum()),
        'monto_total_bs': float(df_bonos_flagged['monto_bs'].sum()),
        'monto_fraude_bs': float(df_bonos_flagged[df_bonos_flagged.get('es_fraude_reglas', False) == True]['monto_bs'].sum()) if 'es_fraude_reglas' in df_bonos_flagged.columns else 0,
        'breakdown': {
            'fallecidos_cobrando': int(df_bonos_flagged.get('fraude_fallecido', pd.Series([False]*len(df_bonos_flagged))).sum()),
            'cobro_exterior': int(df_bonos_flagged.get('fraude_exterior', pd.Series([False]*len(df_bonos_flagged))).sum()),
            'fraude_edad': int(
                df_bonos_flagged.get('fraude_edad_renta', pd.Series([False]*len(df_bonos_flagged))).sum() +
                df_bonos_flagged.get('fraude_edad_juancito', pd.Series([False]*len(df_bonos_flagged))).sum()
            ),
        }
    }

    logger.info("=" * 50)
    logger.info("REPORTE DE FRAUDE EN BONOS SOCIALES")
    logger.info("=" * 50)
    logger.info(f"Total registros:         {report['total_registros']:>10,}")
    logger.info(f"Casos de fraude:         {report['total_fraude_detectado']:>10,}")
    logger.info(f"Monto total (Bs.):       {report['monto_total_bs']:>10,.0f}")
    logger.info(f"Monto en fraude (Bs.):   {report['monto_fraude_bs']:>10,.0f}")
    logger.info("-" * 50)
    for k, v in report['breakdown'].items():
        logger.info(f"  {k:<30} {v:>8,}")

    return report


if __name__ == '__main__':
    logger.info("Cargando datasets sintéticos...")
    df_pop = pd.read_csv('data/synthetic/poblacion_segip.csv')
    df_bonos = pd.read_csv('data/synthetic/bonos_sociales.csv')
    df_def = pd.read_csv('data/synthetic/defunciones_sereci.csv')

    df_flagged = apply_business_rules(df_bonos, df_pop, df_def)
    features = build_ml_features(df_flagged)
    iso_model, scaler = train_anomaly_detector(features)
    report = generate_fraud_report(df_flagged)
