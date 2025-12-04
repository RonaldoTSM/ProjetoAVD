"""
Utilitários para trabalhar com MinIO, PostgreSQL e MLFlow
"""
import os
import boto3
from botocore.client import Config
import pandas as pd
from sqlalchemy import create_engine
import mlflow
from io import BytesIO, StringIO

# Configuração MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# Cliente S3 (MinIO)
s3_client = boto3.client(
    's3',
    endpoint_url=f'http://{MINIO_ENDPOINT}',
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# Configuração PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "weather_db")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

# Engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# Configuração MLFlow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


def read_from_minio(bucket: str, filename: str) -> pd.DataFrame:
    """
    Lê arquivos do INMET armazenados no MinIO, detecta automaticamente 
    a linha do cabeçalho e retorna um DataFrame limpo.
    """
    try:
        # Baixar bytes do MinIO
        response = s3_client.get_object(Bucket=bucket, Key=filename)
        raw_bytes = response["Body"].read()

        # Decodificar o arquivo como texto
        raw_text = raw_bytes.decode("latin1").splitlines()

        # Detectar automaticamente o cabeçalho real
        header_index = None
        for i, line in enumerate(raw_text):
            # Cabeçalho padrão dos arquivos INMET
            if line.strip().startswith("Data;") or line.strip().startswith("DATA;"):
                header_index = i
                break

        if header_index is None:
            raise ValueError("Não foi possível identificar o cabeçalho (linha 'Data;Hora') no CSV.")

        # Reconstruir apenas a parte útil do arquivo
        csv_clean = "\n".join(raw_text[header_index:])

        # Ler com pandas com separador correto e engine robusta
        df = pd.read_csv(
            StringIO(csv_clean),
            sep=";",
            engine="python",
            encoding="latin1",
        )

        return df

    except Exception as e:
        print(f"Erro ao ler arquivo do MinIO ({filename}): {str(e)}")
        raise


def write_to_minio(df: pd.DataFrame, bucket: str, filename: str):
    """
    Escreve um DataFrame como CSV no MinIO
    
    Args:
        df: DataFrame a ser salvo
        bucket: Nome do bucket
        filename: Nome do arquivo
    """
    try:
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, sep=';', encoding='latin1')
        csv_buffer.seek(0)
        
        s3_client.upload_fileobj(
            csv_buffer,
            bucket,
            filename,
            ExtraArgs={'ContentType': 'text/csv'}
        )
        print(f"Arquivo salvo no MinIO: {bucket}/{filename}")
    except Exception as e:
        print(f"Erro ao salvar arquivo no MinIO: {str(e)}")
        raise


def list_minio_files(bucket: str) -> list:
    """
    Lista arquivos em um bucket do MinIO
    
    Args:
        bucket: Nome do bucket
        
    Returns:
        Lista de nomes de arquivos
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        return []
    except Exception as e:
        print(f"Erro ao listar arquivos: {str(e)}")
        return []


def read_from_postgres(table_name: str, query: str = None) -> pd.DataFrame:
    """
    Lê dados do PostgreSQL
    
    Args:
        table_name: Nome da tabela
        query: Query SQL customizada (opcional)
        
    Returns:
        DataFrame com os dados
    """
    try:
        if query:
            df = pd.read_sql(query, engine)
        else:
            df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        return df
    except Exception as e:
        print(f"Erro ao ler do PostgreSQL: {str(e)}")
        raise


def write_to_postgres(df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
    """
    Escreve DataFrame no PostgreSQL
    
    Args:
        df: DataFrame a ser salvo
        table_name: Nome da tabela
        if_exists: Comportamento se tabela existe ('fail', 'replace', 'append')
    """
    try:
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        print(f"Dados salvos na tabela {table_name}: {len(df)} registros")
    except Exception as e:
        print(f"Erro ao salvar no PostgreSQL: {str(e)}")
        raise


def setup_mlflow_experiment(experiment_name: str):
    """
    Configura experimento no MLFlow
    
    Args:
        experiment_name: Nome do experimento
    """
    try:
        mlflow.set_experiment(experiment_name)
        print(f"Experimento '{experiment_name}' configurado")
    except Exception as e:
        print(f"Erro ao configurar experimento: {str(e)}")
        raise

