"""
Data Generator - Genera datos sintéticos realistas para Bolivia
Simula las bases de datos de las instituciones gubernamentales
"""
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker
from loguru import logger

# Configurar Faker para nombres hispanos
fake = Faker(['es_ES', 'es_MX'])
np.random.seed(42)
random.seed(42)

# Departamentos de Bolivia
DEPARTAMENTOS = [
    'La Paz', 'Cochabamba', 'Santa Cruz', 'Oruro', 'Potosí',
    'Chuquisaca', 'Tarija', 'Beni', 'Pando'
]

MUNICIPIOS = {
    'La Paz': ['La Paz', 'El Alto', 'Viacha', 'Achacachi', 'Caranavi'],
    'Cochabamba': ['Cochabamba', 'Quillacollo', 'Sacaba', 'Punata', 'Cliza'],
    'Santa Cruz': ['Santa Cruz de la Sierra', 'Montero', 'Warnes', 'Cotoca'],
    'Oruro': ['Oruro', 'Huanuni', 'Llallagua', 'Challapata'],
    'Potosí': ['Potosí', 'Villazón', 'Uyuni', 'Llica'],
    'Chuquisaca': ['Sucre', 'Camargo', 'Villa Serrano'],
    'Tarija': ['Tarija', 'Yacuiba', 'Villamontes'],
    'Beni': ['Trinidad', 'Guayaramerin', 'Riberalta'],
    'Pando': ['Cobija', 'Porvenir'],
}

ETNIAS = [
    'Mestizo', 'Aymara', 'Quechua', 'Chiquitano', 'Guaraní',
    'Moxeño', 'Chimane', 'Afroboliviano', 'Otro'
]

CARRERAS = [
    'Medicina', 'Derecho', 'Ingeniería Civil', 'Contaduría',
    'Economía', 'Arquitectura', 'Ingeniería de Sistemas',
    'Psicología', 'Odontología', 'Enfermería', 'Pedagogía',
    'Comunicación Social', 'Trabajo Social', 'Turismo',
    'Agronomía', 'Veterinaria'
]

UNIVERSIDADES = [
    'UMSA', 'UMSS', 'UAGRM', 'UTO', 'UAB', 'UAJMS',
    'UPDS', 'UCB', 'UNIFRANZ', 'UTEPSA', 'UFB'
]


def generate_ci() -> str:
    """Genera un Carnet de Identidad boliviano válido (7-8 dígitos)"""
    length = random.choice([7, 8])
    return str(random.randint(10**(length-1), 10**length - 1))


def generate_population(n: int = 12_000_000) -> pd.DataFrame:
    """
    Genera población sintética de Bolivia.
    Bolivia tiene ~12.5M habitantes reales.
    """
    logger.info(f"Generando {n:,} registros de población...")

    depts = np.random.choice(
        DEPARTAMENTOS, n,
        p=[0.28, 0.18, 0.30, 0.05, 0.06, 0.04, 0.05, 0.03, 0.01]
    )

    birth_years = np.random.randint(1924, 2024, n)
    birth_months = np.random.randint(1, 13, n)
    birth_days = np.random.randint(1, 29, n)

    data = {
        'id_persona': [str(uuid.uuid4()) for _ in range(n)],
        'ci': [generate_ci() for _ in range(n)],
        'nombre': [fake.first_name() for _ in range(n)],
        'apellido_paterno': [fake.last_name() for _ in range(n)],
        'apellido_materno': [fake.last_name() for _ in range(n)],
        'fecha_nacimiento': [
            f"{y:04d}-{m:02d}-{d:02d}"
            for y, m, d in zip(birth_years, birth_months, birth_days)
        ],
        'sexo': np.random.choice(['M', 'F'], n, p=[0.49, 0.51]),
        'departamento': depts,
        'municipio': [
            random.choice(MUNICIPIOS.get(d, ['Desconocido']))
            for d in depts
        ],
        'etnia': np.random.choice(ETNIAS, n, p=[0.26, 0.20, 0.30, 0.06, 0.05, 0.03, 0.02, 0.01, 0.07]),
        'vivo': np.random.choice([True, False], n, p=[0.92, 0.08]),
        'activo_segip': np.random.choice([True, False], n, p=[0.88, 0.12]),
        'fuente': 'SEGIP',
    }

    df = pd.DataFrame(data)

    # Introducir duplicados (~2%) - personas con dos CI
    n_dupes = int(n * 0.02)
    dupes = df.sample(n_dupes).copy()
    dupes['ci'] = [generate_ci() for _ in range(n_dupes)]
    dupes['id_persona'] = [str(uuid.uuid4()) for _ in range(n_dupes)]
    dupes['fuente'] = 'DUPLICADO_SEGIP'

    df = pd.concat([df, dupes], ignore_index=True)
    logger.success(f"Población generada: {len(df):,} registros (incl. duplicados)")
    return df


def generate_bonos(population_df: pd.DataFrame, n_beneficiarios: int = 1_800_000) -> pd.DataFrame:
    """Genera registros de bonos sociales."""
    logger.info(f"Generando {n_beneficiarios:,} beneficiarios de bonos...")

    beneficiarios = population_df.sample(n_beneficiarios)

    bonos = [
        ('Renta Dignidad', 3000, 'Adultos mayores +60 años'),
        ('Bono Juancito Pinto', 200, 'Niños en escuela fiscal'),
        ('Bono Juana Azurduy', 1820, 'Mujeres embarazadas'),
        ('Canasta Familiar Covid', 500, 'Familias vulnerables'),
    ]

    registros = []
    for _, persona in beneficiarios.iterrows():
        bono_name, monto, desc = random.choice(bonos)
        registros.append({
            'id_bono': str(uuid.uuid4()),
            'ci_beneficiario': persona['ci'],
            'id_persona': persona['id_persona'],
            'tipo_bono': bono_name,
            'monto_bs': monto,
            'descripcion': desc,
            'departamento': persona['departamento'],
            'fecha_registro': fake.date_between(start_date='-5y', end_date='today'),
            'activo': np.random.choice([True, False], p=[0.85, 0.15]),
            'cobrado_exterior': np.random.choice([True, False], p=[0.97, 0.03]),  # 3% fraude
            'pais_cobro_exterior': np.random.choice(
                ['Chile', 'Argentina', 'Brasil', 'Perú', None],
                p=[0.01, 0.01, 0.005, 0.005, 0.97]
            ),
        })

    df = pd.DataFrame(registros)
    logger.success(f"Bonos generados: {len(df):,} registros")
    return df


def generate_titulos(n: int = 450_000) -> pd.DataFrame:
    """Genera títulos universitarios registrados en MINEDU."""
    logger.info(f"Generando {n:,} títulos universitarios...")

    registros = []
    for _ in range(n):
        es_falso = random.random() < 0.04  # 4% de títulos falsos
        registros.append({
            'id_titulo': str(uuid.uuid4()),
            'ci_profesional': generate_ci(),
            'nombre_profesional': f"{fake.first_name()} {fake.last_name()} {fake.last_name()}",
            'carrera': random.choice(CARRERAS),
            'universidad': random.choice(UNIVERSIDADES),
            'year_egreso': random.randint(1985, 2023),
            'numero_resolucion': f"RES-{random.randint(100, 9999)}/{random.randint(2000, 2023)}",
            'es_valido': not es_falso,
            'observaciones': 'Título falsificado detectado' if es_falso else None,
            'fuente': 'MINEDU',
        })

    df = pd.DataFrame(registros)
    logger.success(f"Títulos generados: {len(df):,} registros")
    return df


def generate_defunciones(n: int = 980_000) -> pd.DataFrame:
    """Genera certificados de defunción del SERECI."""
    logger.info(f"Generando {n:,} registros de defunción...")

    data = {
        'id_defuncion': [str(uuid.uuid4()) for _ in range(n)],
        'ci_fallecido': [generate_ci() for _ in range(n)],
        'nombre_fallecido': [f"{fake.first_name()} {fake.last_name()}" for _ in range(n)],
        'fecha_defuncion': [fake.date_between(start_date='-80y', end_date='today') for _ in range(n)],
        'departamento': np.random.choice(DEPARTAMENTOS, n),
        'causa_muerte': np.random.choice(
            ['Enfermedad crónica', 'Accidente', 'Vejez', 'COVID-19', 'Otra'],
            n, p=[0.35, 0.20, 0.30, 0.10, 0.05]
        ),
        'registrado_segip': np.random.choice([True, False], n, p=[0.78, 0.22]),
        'fuente': 'SERECI',
    }

    df = pd.DataFrame(data)

    # Personas muertas que aún cobran bonos (~5000 casos)
    df_muertos_activos = df.sample(5000).copy()
    df_muertos_activos['cobra_bono_activo'] = True
    logger.warning(f"Casos detectados: {5000} fallecidos con bonos activos")

    logger.success(f"Defunciones generadas: {len(df):,} registros")
    return df


def save_synthetic_data():
    """Guarda todos los datasets sintéticos."""
    output_dir = Path('data/synthetic')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generar datasets (reducidos para demo)
    pop = generate_population(n=100_000)
    pop.to_csv(output_dir / 'poblacion_segip.csv', index=False)
    logger.info("Guardado: poblacion_segip.csv")

    bonos = generate_bonos(pop, n_beneficiarios=15_000)
    bonos.to_csv(output_dir / 'bonos_sociales.csv', index=False)
    logger.info("Guardado: bonos_sociales.csv")

    titulos = generate_titulos(n=10_000)
    titulos.to_csv(output_dir / 'titulos_universitarios.csv', index=False)
    logger.info("Guardado: titulos_universitarios.csv")

    defunciones = generate_defunciones(n=8_000)
    defunciones.to_csv(output_dir / 'defunciones_sereci.csv', index=False)
    logger.info("Guardado: defunciones_sereci.csv")

    # Resumen
    print("\n" + "="*60)
    print("DATOS SINTÉTICOS GENERADOS EXITOSAMENTE")
    print("="*60)
    print(f"  Población (SEGIP):     {len(pop):>10,} registros")
    print(f"  Bonos Sociales:        {len(bonos):>10,} registros")
    print(f"  Títulos (MINEDU):      {len(titulos):>10,} registros")
    print(f"  Defunciones (SERECI):  {len(defunciones):>10,} registros")
    print("="*60)
    print(f"  Directorio: {output_dir.absolute()}")


if __name__ == '__main__':
    save_synthetic_data()
