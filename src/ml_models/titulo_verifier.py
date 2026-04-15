"""
Verificador de Títulos Universitarios con NLP

Usa Sentence Transformers para detectar:
- Títulos con información inconsistente (universidad/carrera/año)
- Personas con múltiples títulos de diferentes universidades (posible falsificación)
- Coincidencias aproximadas vs registros oficiales MINEDU
"""
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from loguru import logger
from typing import List, Tuple
import re


MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'


def preprocess_titulo_text(row: pd.Series) -> str:
    """Convierte un registro de título en texto unificado para embedding."""
    nombre = str(row.get('nombre_profesional', '')).strip().upper()
    carrera = str(row.get('carrera', '')).strip().upper()
    universidad = str(row.get('universidad', '')).strip().upper()
    year = str(row.get('year_egreso', '')).strip()
    return f"NOMBRE: {nombre} | CARRERA: {carrera} | UNIVERSIDAD: {universidad} | AÑO: {year}"


def embed_titulos(df: pd.DataFrame, model: SentenceTransformer) -> np.ndarray:
    """Genera embeddings para todos los títulos."""
    texts = df.apply(preprocess_titulo_text, axis=1).tolist()
    logger.info(f"Generando embeddings para {len(texts):,} títulos...")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)
    logger.success(f"Embeddings generados: {embeddings.shape}")
    return embeddings


def detect_suspicious_titles(df: pd.DataFrame, embeddings: np.ndarray,
                              threshold: float = 0.92) -> pd.DataFrame:
    """
    Detecta títulos sospechosos por alta similitud entre registros
    que deberían ser únicos (mismo nombre, misma carrera, diferente resolución).
    """
    logger.info("Calculando similitudes entre títulos...")
    suspicious = []

    # Procesar en batches para no saturar memoria
    batch_size = 500
    n = len(df)

    for i in range(0, min(n, 2000), batch_size):  # Limitar para demo
        batch_emb = embeddings[i:i+batch_size]
        sims = cosine_similarity(batch_emb, embeddings)

        for j, sim_row in enumerate(sims):
            idx_i = i + j
            high_sim_indices = np.where((sim_row > threshold) & (np.arange(n) != idx_i))[0]

            for idx_k in high_sim_indices:
                if idx_k > idx_i:  # Evitar duplicados
                    r1 = df.iloc[idx_i]
                    r2 = df.iloc[idx_k]

                    # Solo marca como sospechoso si CI o nombre son similares pero resolución difiere
                    if r1['numero_resolucion'] != r2['numero_resolucion']:
                        suspicious.append({
                            'titulo_1_id': r1.get('id_titulo', idx_i),
                            'titulo_2_id': r2.get('id_titulo', idx_k),
                            'nombre_1': r1.get('nombre_profesional'),
                            'nombre_2': r2.get('nombre_profesional'),
                            'carrera_1': r1.get('carrera'),
                            'carrera_2': r2.get('carrera'),
                            'universidad_1': r1.get('universidad'),
                            'universidad_2': r2.get('universidad'),
                            'similitud': round(float(sim_row[idx_k]), 4),
                            'alerta': 'POSIBLE TITULO DUPLICADO/FALSIFICADO',
                        })

    result_df = pd.DataFrame(suspicious)
    logger.warning(f"Títulos sospechosos detectados: {len(result_df):,}")
    return result_df


def verify_titulo(nombre: str, carrera: str, universidad: str, year: int,
                  df_titulos: pd.DataFrame, model: SentenceTransformer,
                  embeddings: np.ndarray, threshold: float = 0.85) -> dict:
    """
    Verifica si un título específico existe en el registro oficial MINEDU.
    Retorna el resultado de verificación con score de confianza.
    """
    query = f"NOMBRE: {nombre.upper()} | CARRERA: {carrera.upper()} | UNIVERSIDAD: {universidad.upper()} | AÑO: {year}"
    query_emb = model.encode([query])

    sims = cosine_similarity(query_emb, embeddings)[0]
    best_idx = np.argmax(sims)
    best_score = float(sims[best_idx])

    result = {
        'nombre_consultado': nombre,
        'carrera_consultada': carrera,
        'universidad_consultada': universidad,
        'year_consultado': year,
        'score_similitud': round(best_score, 4),
        'verificado': best_score >= threshold,
        'match_nombre': df_titulos.iloc[best_idx]['nombre_profesional'] if best_score > 0.5 else None,
        'match_universidad': df_titulos.iloc[best_idx]['universidad'] if best_score > 0.5 else None,
        'match_resolucion': df_titulos.iloc[best_idx]['numero_resolucion'] if best_score > 0.5 else None,
        'alerta': None if best_score >= threshold else 'TITULO NO ENCONTRADO EN REGISTRO OFICIAL',
    }
    return result


if __name__ == '__main__':
    logger.info("Cargando modelo NLP multilingue...")
    model = SentenceTransformer(MODEL_NAME)

    df_titulos = pd.read_csv('data/synthetic/titulos_universitarios.csv')
    embeddings = embed_titulos(df_titulos, model)

    sospechosos = detect_suspicious_titles(df_titulos, embeddings)
    print(f"\nTítulos sospechosos: {len(sospechosos)}")

    # Demo de verificación puntual
    resultado = verify_titulo(
        nombre="Juan Mamani Condori",
        carrera="Medicina",
        universidad="UMSA",
        year=2010,
        df_titulos=df_titulos,
        model=model,
        embeddings=embeddings
    )
    print("\nVerificación de título:")
    for k, v in resultado.items():
        print(f"  {k}: {v}")
