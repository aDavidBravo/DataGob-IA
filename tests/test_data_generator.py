"""
Tests para el generador de datos sintéticos
"""
import pytest
import pandas as pd
from src.utils.data_generator import (
    generate_ci, generate_population,
    generate_bonos, generate_titulos, generate_defunciones
)


def test_generate_ci_format():
    for _ in range(100):
        ci = generate_ci()
        assert ci.isdigit()
        assert 7 <= len(ci) <= 8


def test_generate_population_small():
    df = generate_population(n=1000)
    assert len(df) >= 1000  # Puede tener duplicados sintéticos
    required_cols = ['id_persona', 'ci', 'nombre', 'apellido_paterno', 'departamento']
    for col in required_cols:
        assert col in df.columns


def test_population_departamentos():
    df = generate_population(n=5000)
    depts = df['departamento'].unique()
    assert len(depts) >= 7  # Al menos 7 de 9 departamentos


def test_generate_bonos():
    pop = generate_population(n=2000)
    bonos = generate_bonos(pop, n_beneficiarios=200)
    assert len(bonos) == 200
    assert 'tipo_bono' in bonos.columns
    assert 'monto_bs' in bonos.columns


def test_generate_titulos():
    titulos = generate_titulos(n=500)
    assert len(titulos) == 500
    assert 'es_valido' in titulos.columns
    # Debe haber algunos títulos falsos (~4%)
    falsos = titulos[~titulos['es_valido']]
    assert len(falsos) > 0


def test_generate_defunciones():
    df = generate_defunciones(n=1000)
    assert len(df) == 1000
    assert 'ci_fallecido' in df.columns
    assert 'fuente' in df.columns
    assert (df['fuente'] == 'SERECI').all()
