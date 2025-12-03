"""
Script simples para carregar dados do MinIO para PostgreSQL
Execute no JupyterLab: exec(open('notebooks/carregar_dados_postgresql.py').read())
"""
import sys
import os

# Adicionar path
sys.path.append('/home/jovyan/work')

from utils import (
    read_from_minio,
    write_to_postgres,
    list_minio_files
)
from datetime import datetime
import pandas as pd
import numpy as np

def clean_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e trata dados meteorológicos"""
    df_clean = df.copy()
    
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
        'NOME': 'cidade',
        'Data': 'data_hora',
        'Hora UTC': 'hora_utc'
    }
    
    # Aplicar mapeamento
    df_clean = df_clean.rename(columns=column_mapping)
    
    # Processar data/hora
    if 'data_hora' in df_clean.columns:
        # Se tiver coluna de hora separada, combinar
        if 'hora_utc' in df_clean.columns:
            df_clean['data_hora'] = pd.to_datetime(
                df_clean['data_hora'].astype(str) + ' ' + df_clean['hora_utc'].astype(str).str.replace(' UTC', ''),
                errors='coerce'
            )
        else:
            df_clean['data_hora'] = pd.to_datetime(df_clean['data_hora'], errors='coerce')
        
        # Extrair componentes de data
        df_clean['ano'] = df_clean['data_hora'].dt.year
        df_clean['mes'] = df_clean['data_hora'].dt.month
        df_clean['dia'] = df_clean['data_hora'].dt.day
        df_clean['hora'] = df_clean['data_hora'].dt.hour
    
    # Limpar valores numéricos
    numeric_cols = ['temperatura', 'umidade_relativa', 'pressao_atmosferica',
                    'direcao_vento', 'velocidade_vento', 'radiacao_solar', 'precipitacao']
    
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            # Remover outliers extremos
            if col == 'temperatura':
                df_clean[col] = df_clean[col].clip(-50, 60)
            elif col == 'umidade_relativa':
                df_clean[col] = df_clean[col].clip(0, 100)
            elif col == 'precipitacao':
                df_clean[col] = df_clean[col].clip(0, 500)
    
    # Remover linhas sem data
    df_clean = df_clean.dropna(subset=['data_hora'])
    
    # Selecionar colunas relevantes
    relevant_cols = ['data_hora', 'estacao', 'cidade', 'estado',
                     'temperatura', 'umidade_relativa', 'pressao_atmosferica',
                     'direcao_vento', 'velocidade_vento', 'radiacao_solar',
                     'precipitacao', 'ano', 'mes', 'dia', 'hora']
    
    available_cols = [col for col in relevant_cols if col in df_clean.columns]
    df_clean = df_clean[available_cols]
    
    return df_clean

def main():
    print("=" * 60)
    print("CARREGANDO DADOS DO MINIO PARA POSTGRESQL")
    print("=" * 60)
    print("\nConforme especificacoes do projeto:")
    print("  - FastAPI -> MinIO (raw/)")
    print("  - MinIO -> PostgreSQL (executando agora)")
    print("  - PostgreSQL -> Jupyter Notebook")
    print()
    
    # Listar arquivos no bucket raw
    raw_files = list_minio_files('raw')
    print(f"Encontrados {len(raw_files)} arquivos no bucket raw/\n")
    
    if len(raw_files) == 0:
        print("Nenhum arquivo encontrado no MinIO!")
        print("   Execute primeiro o upload dos dados via FastAPI.")
        return
    
    # Verificar se já há dados no PostgreSQL
    try:
        from utils import read_from_postgres
        query = "SELECT COUNT(*) as total FROM weather_hourly"
        result = read_from_postgres('weather_hourly', query)
        existing_count = result['total'].iloc[0]
        if existing_count > 0:
            print(f"Ja existem {existing_count:,} registros no PostgreSQL.")
            print("   Continuando para adicionar mais dados...")
    except:
        pass
    
    all_processed = []
    success_count = 0
    error_count = 0
    total_records = 0
    
    # Processar arquivos
    print(f"\nProcessando {len(raw_files)} arquivos...\n")
    
    for i, filename in enumerate(raw_files, 1):
        try:
            print(f"[{i:3d}/{len(raw_files)}] {filename[:50]:50s}", end=" ... ")
            
            # Ler arquivo do MinIO
            df = read_from_minio('raw', filename)
            
            # Limpar dados
            df_clean = clean_weather_data(df)
            
            # Extrair cidade se necessário
            if 'cidade' not in df_clean.columns or df_clean['cidade'].isna().all():
                if 'arquivo_origem' in df_clean.columns:
                    def extract_city(f):
                        if pd.isna(f): return 'Desconhecida'
                        f_str = str(f).lower()
                        if 'dados_' in f_str:
                            return f_str.split('dados_')[1].split('_')[0].capitalize()
                        return 'Desconhecida'
                    df_clean['cidade'] = df_clean['arquivo_origem'].apply(extract_city)
            
            # Adicionar metadados
            df_clean['arquivo_origem'] = filename
            # NOTA: Não adicionar 'processing_date' - a tabela usa 'ingestion_date' e 'created_at' (preenchidos automaticamente)
            
            # Filtrar apenas dados válidos
            df_clean = df_clean.dropna(subset=['temperatura', 'umidade_relativa'])
            
            # Remover coluna 'processing_date' se existir (não existe na tabela PostgreSQL)
            if 'processing_date' in df_clean.columns:
                df_clean = df_clean.drop(columns=['processing_date'])
            
            if len(df_clean) > 0:
                # Salvar no PostgreSQL
                write_to_postgres(df_clean, 'weather_hourly', if_exists='append')
                
                all_processed.append(df_clean)
                success_count += 1
                total_records += len(df_clean)
                print(f"OK {len(df_clean):,} registros")
            else:
                print(f"Sem dados validos")
            
        except Exception as e:
            error_count += 1
            print(f"Erro: {str(e)[:60]}")
            continue
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DO PROCESSAMENTO")
    print("=" * 60)
    print(f"   Sucesso: {success_count} arquivos")
    print(f"   Erros: {error_count} arquivos")
    print(f"   Total de registros: {total_records:,}")
    
    if all_processed:
        df_final = pd.concat(all_processed, ignore_index=True)
        
        # Criar agregação diária
        print("\nCriando agregacao diaria...")
        try:
            df_final['data'] = pd.to_datetime(df_final['data_hora']).dt.date
            
            daily_agg = df_final.groupby(['data', 'estacao', 'cidade']).agg({
                'temperatura': ['mean', 'max', 'min'],
                'umidade_relativa': 'mean',
                'pressao_atmosferica': 'mean',
                'velocidade_vento': 'mean',
                'radiacao_solar': 'sum',
                'precipitacao': 'sum'
            }).reset_index()
            
            daily_agg.columns = ['data', 'estacao', 'cidade',
                               'temperatura_media', 'temperatura_max', 'temperatura_min',
                               'umidade_media', 'pressao_media',
                               'velocidade_vento_media', 'radiacao_solar_total',
                               'precipitacao_total']
            
            write_to_postgres(daily_agg, 'weather_daily', if_exists='replace')
            print(f"   Agregacao diaria criada: {len(daily_agg):,} registros")
        except Exception as e:
            print(f"   Erro ao criar agregacao diaria: {str(e)}")
        
        # Verificar resultado final
        try:
            from utils import read_from_postgres
            query = "SELECT COUNT(*) as total FROM weather_hourly"
            result = read_from_postgres('weather_hourly', query)
            final_count = result['total'].iloc[0]
            print(f"\nTotal de registros no PostgreSQL: {final_count:,}")
            print("\nProcessamento concluido com sucesso!")
            print("\nProximos passos:")
            print("   1. Execute o notebook de modelagem: 03_modelagem_conforto_termico.ipynb")
            print("   2. O notebook ja esta configurado para usar PostgreSQL")
        except Exception as e:
            print(f"\nErro ao verificar resultado: {str(e)}")
    else:
        print("\nNenhum arquivo foi processado com sucesso!")
        print("   Verifique os erros acima e tente novamente.")

if __name__ == "__main__":
    main()

