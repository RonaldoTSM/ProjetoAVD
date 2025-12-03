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

def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e trata dados meteorológicos
    
    Args:
        df: DataFrame com dados brutos
        
    Returns:
        DataFrame limpo
    """
    df_clean = df.copy()
    
    # Converter colunas de data/hora se necessário
    date_columns = ['DATA', 'Data', 'data', 'DATA (YYYY-MM-DD)', 'HORA (UTC)']
    for col in date_columns:
        if col in df_clean.columns:
            if 'HORA' in col:
                df_clean[col] = pd.to_datetime(df_clean[col], format='%H%M', errors='coerce')
            else:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Normalizar nomes de colunas (exemplos comuns do INMET)
    column_mapping = {
        'TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)': 'temperatura',
        'TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)': 'temperatura_max',
        'TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)': 'temperatura_min',
        'UMIDADE RELATIVA DO AR, HORARIA (%)': 'umidade_relativa',
        'PRESSÃO ATMOSFÉRICA AO NIVEL DA ESTAÇÃO, HORARIA (mB)': 'pressao_atmosferica',
        'VENTO, DIREÇÃO HORARIA (gr)': 'direcao_vento',
        'VENTO, VELOCIDADE HORARIA (m/s)': 'velocidade_vento',
        'RADIAÇÃO GLOBAL (Kj/m²)': 'radiacao_solar',
        'PRECIPITAÇÃO TOTAL, HORÁRIO (mm)': 'precipitacao',
        'ESTACAO': 'estacao',
        'UF': 'estado',
        'NOME': 'cidade'
    }
    
    # Aplicar mapeamento
    df_clean = df_clean.rename(columns=column_mapping)
    
    # Extrair informações de data
    if 'DATA' in df_clean.columns or 'Data' in df_clean.columns:
        date_col = 'DATA' if 'DATA' in df_clean.columns else 'Data'
        df_clean['data_hora'] = pd.to_datetime(df_clean[date_col], errors='coerce')
        df_clean['ano'] = df_clean['data_hora'].dt.year
        df_clean['mes'] = df_clean['data_hora'].dt.month
        df_clean['dia'] = df_clean['data_hora'].dt.day
        df_clean['hora'] = df_clean['data_hora'].dt.hour
    
    # Remover valores inválidos
    numeric_columns = ['temperatura', 'umidade_relativa', 'pressao_atmosferica',
                      'direcao_vento', 'velocidade_vento', 'radiacao_solar', 'precipitacao']
    
    for col in numeric_columns:
        if col in df_clean.columns:
            # Substituir valores inválidos por NaN
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            # Remover outliers extremos (opcional)
            if col in ['temperatura', 'temperatura_max', 'temperatura_min']:
                df_clean[col] = df_clean[col].clip(-50, 60)  # Temperatura razoável
            elif col == 'umidade_relativa':
                df_clean[col] = df_clean[col].clip(0, 100)
            elif col == 'precipitacao':
                df_clean[col] = df_clean[col].clip(0, 500)  # Precipitação máxima razoável
    
    # Remover linhas com muitos valores faltantes
    df_clean = df_clean.dropna(subset=['data_hora'], how='any')
    
    # Selecionar colunas relevantes
    relevant_columns = ['data_hora', 'estacao', 'cidade', 'estado',
                       'temperatura', 'umidade_relativa', 'pressao_atmosferica',
                       'direcao_vento', 'velocidade_vento', 'radiacao_solar',
                       'precipitacao', 'ano', 'mes', 'dia', 'hora']
    
    # Manter apenas colunas que existem
    available_columns = [col for col in relevant_columns if col in df_clean.columns]
    df_clean = df_clean[available_columns]
    
    return df_clean


def process_raw_files():
    """
    Processa todos os arquivos do bucket raw/
    """
    print("Iniciando processamento de dados...")
    
    # Listar arquivos no bucket raw
    raw_files = list_minio_files('raw')
    print(f"Encontrados {len(raw_files)} arquivos no bucket raw/")
    
    all_processed = []
    
    for filename in raw_files:
        try:
            print(f"\nProcessando: {filename}")
            
            # Ler arquivo do MinIO
            df = read_from_minio('raw', filename)
            print(f"  - Registros originais: {len(df)}")
            
            # Limpar dados
            df_clean = clean_weather_data(df)
            print(f"  - Registros após limpeza: {len(df_clean)}")
            
            # Adicionar metadados
            df_clean['arquivo_origem'] = filename
            df_clean['processing_date'] = datetime.now().isoformat()
            
            # Salvar no bucket processed
            processed_filename = f"processed_{filename}"
            write_to_minio(df_clean, 'processed', processed_filename)
            
            # Salvar no PostgreSQL
            write_to_postgres(df_clean, 'weather_hourly', if_exists='append')
            
            all_processed.append(df_clean)
            print(f"  ✓ Processado com sucesso")
            
        except Exception as e:
            print(f"  ✗ Erro ao processar {filename}: {str(e)}")
            continue
    
    if all_processed:
        # Concatenar todos os dados processados
        df_final = pd.concat(all_processed, ignore_index=True)
        print(f"\nTotal de registros processados: {len(df_final)}")
        
        # Criar agregação diária
        create_daily_aggregation(df_final)
    
    print("\nProcessamento concluído!")


def create_daily_aggregation(df: pd.DataFrame):
    """
    Cria agregação diária dos dados
    """
    print("\nCriando agregação diária...")
    
    df['data'] = pd.to_datetime(df['data_hora']).dt.date
    
    daily_agg = df.groupby(['data', 'estacao', 'cidade']).agg({
        'temperatura': ['mean', 'max', 'min'],
        'umidade_relativa': 'mean',
        'pressao_atmosferica': 'mean',
        'velocidade_vento': 'mean',
        'radiacao_solar': 'sum',
        'precipitacao': 'sum'
    }).reset_index()
    
    # Flatten column names
    daily_agg.columns = ['data', 'estacao', 'cidade',
                         'temperatura_media', 'temperatura_max', 'temperatura_min',
                         'umidade_media', 'pressao_media',
                         'velocidade_vento_media', 'radiacao_solar_total',
                         'precipitacao_total']
    
    # Salvar no PostgreSQL
    write_to_postgres(daily_agg, 'weather_daily', if_exists='replace')
    
    # Salvar no MinIO
    write_to_minio(daily_agg, 'processed', 'weather_daily.csv')
    
    print(f"Agregação diária criada: {len(daily_agg)} registros")


if __name__ == "__main__":
    process_raw_files()

