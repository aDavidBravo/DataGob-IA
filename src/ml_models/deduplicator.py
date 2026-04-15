"""
Deduplicator de Identidades - Record Linkage con ML
Detecta personas con múltiples CI o registros duplicados entre instituciones.

Técnicas:
- Blocking para eficiencia O(n)
- Similarity features: Jaro-Winkler, Soundex, fecha, depto
- Clasificador XGBoost para parejas match/no-match
- Clustering para agrupar identidades
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, precision_recall_fscore_support
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import jellyfish
from fuzzywuzzy import fuzz
from loguru import logger
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')


def soundex_similarity(s1: str, s2: str) -> float:
    """Similitud basada en código Soundex (fonético)."""
    try:
        sx1 = jellyfish.soundex(s1)
        sx2 = jellyfish.soundex(s2)
        return 1.0 if sx1 == sx2 else 0.0
    except Exception:
        return 0.0


def compute_pair_features(row1: pd.Series, row2: pd.Series) -> dict:
    """
    Computa features de similitud entre dos registros de persona.
    """
    n1 = str(row1.get('nombre', '')).upper()
    n2 = str(row2.get('nombre', '')).upper()
    ap1 = str(row1.get('apellido_paterno', '')).upper()
    ap2 = str(row2.get('apellido_paterno', '')).upper()
    am1 = str(row1.get('apellido_materno', '')).upper()
    am2 = str(row2.get('apellido_materno', '')).upper()

    return {
        # Nombre
        'jaro_nombre': jellyfish.jaro_winkler_similarity(n1, n2),
        'fuzz_nombre': fuzz.ratio(n1, n2) / 100,
        'soundex_nombre': soundex_similarity(n1, n2),
        # Apellido paterno
        'jaro_ap': jellyfish.jaro_winkler_similarity(ap1, ap2),
        'fuzz_ap': fuzz.ratio(ap1, ap2) / 100,
        'soundex_ap': soundex_similarity(ap1, ap2),
        # Apellido materno
        'jaro_am': jellyfish.jaro_winkler_similarity(am1, am2),
        'fuzz_am': fuzz.ratio(am1, am2) / 100,
        # Fecha de nacimiento
        'fecha_match': 1.0 if row1.get('fecha_nacimiento') == row2.get('fecha_nacimiento') else 0.0,
        # Departamento
        'depto_match': 1.0 if row1.get('departamento') == row2.get('departamento') else 0.0,
        # Sexo
        'sexo_match': 1.0 if row1.get('sexo') == row2.get('sexo') else 0.0,
        # CI igual
        'ci_match': 1.0 if str(row1.get('ci', '')) == str(row2.get('ci', '')) else 0.0,
    }


def blocking_by_soundex(df: pd.DataFrame) -> list:
    """
    Blocking: agrupa candidatos por Soundex del apellido paterno.
    Reduce de O(n^2) a O(n * block_size).
    """
    logger.info("Aplicando blocking por Soundex del apellido...")
    df = df.copy()
    df['soundex_key'] = df['apellido_paterno'].apply(
        lambda x: jellyfish.soundex(str(x).upper()) if pd.notna(x) else 'Z000'
    )

    pairs = []
    for key, group in df.groupby('soundex_key'):
        if len(group) < 2:
            continue
        indices = group.index.tolist()
        # Limitar a 500 por bloque para eficiencia
        if len(indices) > 500:
            indices = indices[:500]
        for i in range(len(indices)):
            for j in range(i+1, len(indices)):
                pairs.append((indices[i], indices[j]))

    logger.info(f"Pares candidatos generados: {len(pairs):,}")
    return pairs


def generate_training_data(df: pd.DataFrame, n_pairs: int = 5000) -> tuple:
    """
    Genera datos de entrenamiento sintéticos:
    - Positivos: pares del mismo individuo (CI igual, ligeras variaciones)
    - Negativos: pares aleatorios de diferentes personas
    """
    logger.info("Generando datos de entrenamiento...")
    features_list = []
    labels = []

    # Positivos (mismo individuo, variaciones)
    sample = df.sample(min(n_pairs // 2, len(df))).reset_index(drop=True)
    for _, row in sample.iterrows():
        row2 = row.copy()
        # Simular error tipográfico en nombre
        nombre = list(str(row['nombre']))
        if len(nombre) > 2:
            idx = np.random.randint(0, len(nombre))
            nombre[idx] = chr(ord(nombre[idx]) + np.random.choice([-1, 1]))
        row2['nombre'] = ''.join(nombre)
        features_list.append(compute_pair_features(row, row2))
        labels.append(1)

    # Negativos (personas diferentes)
    for _ in range(n_pairs // 2):
        r1, r2 = df.sample(2).iloc
        features_list.append(compute_pair_features(r1, r2))
        labels.append(0)

    X = pd.DataFrame(features_list)
    y = np.array(labels)
    return X, y


def train_deduplicator(df: pd.DataFrame) -> xgb.XGBClassifier:
    """
    Entrena un clasificador XGBoost para detectar pares duplicados.
    """
    logger.info("Entrenando modelo de deduplicación...")

    X, y = generate_training_data(df, n_pairs=10_000)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    y_pred = model.predict(X_test)
    p, r, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
    logger.success(f"Modelo entrenado - Precision: {p:.3f} | Recall: {r:.3f} | F1: {f1:.3f}")

    # Guardar modelo
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    with open(models_dir / 'deduplicator_xgb.pkl', 'wb') as f:
        pickle.dump(model, f)
    logger.info("Modelo guardado: models/deduplicator_xgb.pkl")

    return model


def find_duplicates(df: pd.DataFrame, model: xgb.XGBClassifier, threshold: float = 0.7) -> pd.DataFrame:
    """
    Encuentra pares duplicados en el dataframe usando el modelo entrenado.
    """
    pairs = blocking_by_soundex(df)
    logger.info(f"Evaluando {len(pairs):,} pares...")

    results = []
    batch_size = 1000
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i+batch_size]
        features_batch = [
            compute_pair_features(df.loc[p[0]], df.loc[p[1]])
            for p in batch
        ]
        X_batch = pd.DataFrame(features_batch)
        probs = model.predict_proba(X_batch)[:, 1]

        for (idx1, idx2), prob in zip(batch, probs):
            if prob >= threshold:
                r1 = df.loc[idx1]
                r2 = df.loc[idx2]
                results.append({
                    'id_persona_1': r1.get('id_persona', idx1),
                    'id_persona_2': r2.get('id_persona', idx2),
                    'ci_1': r1.get('ci'),
                    'ci_2': r2.get('ci'),
                    'nombre_1': f"{r1.get('nombre')} {r1.get('apellido_paterno')}",
                    'nombre_2': f"{r2.get('nombre')} {r2.get('apellido_paterno')}",
                    'probabilidad_match': round(float(prob), 4),
                    'es_duplicado': True,
                })

    duplicates_df = pd.DataFrame(results)
    logger.success(f"Duplicados encontrados: {len(duplicates_df):,} pares con p >= {threshold}")
    return duplicates_df


if __name__ == '__main__':
    # Ejemplo de uso
    df = pd.read_csv('data/synthetic/poblacion_segip.csv')
    model = train_deduplicator(df)
    duplicados = find_duplicates(df.head(5000), model)
    print(f"\nDuplicados detectados: {len(duplicados)}")
    if not duplicados.empty:
        print(duplicados.head(10).to_string())
