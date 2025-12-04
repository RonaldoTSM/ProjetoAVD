"""
Script de processamento e limpeza de dados
Lê dados do MinIO (raw), processa e salva em processed e PostgreSQL
"""

import pandas as pd
import numpy as np
from datetime import datetime
from utils import (
    read_from_minio,
    write_to_minio,
    write_to_postgres,
    list_minio_files
)

# ============================================================
# FUNÇÃO PRINCIPAL DE LIMPEZA
# ============================================================

def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e trata dados meteorológicos, preservando DATA + HORA corretamente
    e preservando números (corrige vírgula decimal -> ponto).
    """

    df_clean = df.copy()

    # ============================================================
    # 1. Mapear nomes de colunas para nomes padronizados
    # ============================================================

    column_mapping = {
        # INMET
        'TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)': 'temperatura',
        'UMIDADE RELATIVA DO AR, HORARIA (%)': 'umidade_relativa',
        'VENTO, VELOCIDADE HORARIA (m/s)': 'velocidade_vento',
        'RADIAÇÃO GLOBAL (Kj/m²)': 'radiacao_solar',
        'PRECIPITAÇÃO TOTAL, HORÁRIO (mm)': 'precipitacao',
        'ESTACAO': 'estacao',
        'UF': 'estado',
        'NOME': 'cidade',

        # Cabrobó 2020
        'TempBulboSeco': 'temperatura',
        'UmidadeRelativa': 'umidade_relativa',
        'VelocidadeVento': 'velocidade_vento',
        'RadiacaoGlobal': 'radiacao_solar',
        'Precipitacao': 'precipitacao',
    }

    df_clean = df_clean.rename(columns=column_mapping)

    # ============================================================
    # 2. Construção / detecção da coluna data_hora
    # ============================================================

    # Se já existe data_hora, usa ela
    if "data_hora" in df_clean.columns:
        df_clean["data_hora"] = pd.to_datetime(df_clean["data_hora"], errors="coerce")

    # Caso INMET tradicional: Data + Hora UTC
    elif "Data" in df_clean.columns and "Hora UTC" in df_clean.columns:
        hora_str = (
            df_clean["Hora UTC"]
            .astype(str)
            .str.replace(" UTC", "", regex=False)
            .str.zfill(4)
        )
        df_clean["data_hora"] = pd.to_datetime(
            df_clean["Data"].astype(str) + " " + hora_str,
            format="%Y/%m/%d %H%M",
            errors="coerce"
        )

    # Caso exista só Data
    elif "Data" in df_clean.columns:
        df_clean["data_hora"] = pd.to_datetime(df_clean["Data"], errors="coerce")

    # Caso exista DATA (maiúsculo)
    elif "DATA" in df_clean.columns:
        df_clean["data_hora"] = pd.to_datetime(df_clean["DATA"], errors="coerce")

    else:
        raise ValueError("Nenhuma coluna de data encontrada no arquivo!")

    # Remover registros sem data válida
    df_clean = df_clean.dropna(subset=["data_hora"])

    # ============================================================
    # 3. Normalização dos valores numéricos (com vírgula → ponto)
    # ============================================================

    numeric_columns = [
        "temperatura", "umidade_relativa", "pressao_atmosferica",
        "direcao_vento", "velocidade_vento", "radiacao_solar", "precipitacao"
    ]

    for col in numeric_columns:
        if col in df_clean.columns:
            # transforma tudo em string
            s = df_clean[col].astype(str).str.strip()

            # remove valores inválidos comuns
            s = s.replace({"": None, "nan": None, "NaN": None, "-": None})

            # vírgula decimal → ponto decimal
            s = s.str.replace(",", ".", regex=False)

            # converte finalmente para número
            df_clean[col] = pd.to_numeric(s, errors="coerce")

    # ============================================================
    # 4. Quebrar data em partes
    # ============================================================

    df_clean["ano"] = df_clean["data_hora"].dt.year
    df_clean["mes"] = df_clean["data_hora"].dt.month
    df_clean["dia"] = df_clean["data_hora"].dt.day
    df_clean["hora"] = df_clean["data_hora"].dt.hour

    # ============================================================
    # 5. Manter somente colunas relevantes (as que realmente existem)
    # ============================================================

    relevant_columns = [
        "data_hora", "estacao", "cidade", "estado",
        "temperatura", "umidade_relativa", "pressao_atmosferica",
        "direcao_vento", "velocidade_vento", "radiacao_solar",
        "precipitacao", "ano", "mes", "dia", "hora"
    ]

    existing_cols = [c for c in relevant_columns if c in df_clean.columns]

    return df_clean[existing_cols]


# ============================================================
# PROCESSAMENTO COMPLETO DOS ARQUIVOS RAW
# ============================================================

def process_raw_files():
    print("Iniciando processamento de dados...")

    raw_files = list_minio_files("raw")
    print(f"Encontrados {len(raw_files)} arquivos no bucket raw/")

    all_processed = []

    for filename in raw_files:
        try:
            print(f"\nProcessando: {filename}")

            df = read_from_minio("raw", filename)
            print(f"  - Registros originais: {len(df)}")

            df_clean = clean_weather_data(df)
            print(f"  - Registros após limpeza: {len(df_clean)}")

            df_clean["arquivo_origem"] = filename

            processed_filename = f"processed_{filename}"
            write_to_minio(df_clean, "processed", processed_filename)

            write_to_postgres(df_clean, "weather_hourly", if_exists="append")

            all_processed.append(df_clean)
            print("  ✓ Processado com sucesso")

        except Exception as e:
            print(f"  ✗ Erro ao processar {filename}: {str(e)}")

    print("\nProcessamento concluído!")


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    process_raw_files()
