"""
FastAPI - Ingestão de Dados Meteorológicos do INMET
Endpoints: /fetch_inmet, /upload, /store
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import pandas as pd
from datetime import datetime
from typing import Optional
import boto3
from botocore.client import Config
import requests
from io import BytesIO
import logging
import os
import io
from fastapi import APIRouter

router = APIRouter()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Weather Data Ingestion API",
    description="API para ingestão de dados meteorológicos do INMET",
    version="1.0.0"
)

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


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "Weather Data Ingestion API",
        "endpoints": {
            "/fetch_inmet": "Baixar dados do INMET",
            "/upload": "Upload de arquivo CSV",
            "/store": "Armazenar dados no MinIO",
            "/health": "Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    try:
        # Verificar conexão com MinIO
        s3_client.list_buckets()
        return {"status": "healthy", "minio": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/fetch_inmet")
async def fetch_inmet(
    station_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Baixa dados do INMET via API
    
    Args:
        station_code: Código da estação (opcional)
        start_date: Data inicial (formato: YYYY-MM-DD)
        end_date: Data final (formato: YYYY-MM-DD)
    """
    try:
        # URL da API do INMET (exemplo - ajustar conforme necessário)
        # Nota: A API real do INMET pode ter endpoints diferentes
        base_url = "https://apitempo.inmet.gov.br/estacao"
        
        if station_code:
            url = f"{base_url}/{start_date}/{end_date}/{station_code}"
        else:
            # Se não especificar estação, buscar todas de Pernambuco
            url = f"{base_url}/{start_date}/{end_date}"
        
        logger.info(f"Buscando dados do INMET: {url}")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Converter resposta para DataFrame
        data = response.json()
        df = pd.DataFrame(data)
        
        # Adicionar metadados
        df['ingestion_date'] = datetime.now().isoformat()
        df['source'] = 'inmet_api'
        
        # Salvar no MinIO
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inmet_data_{timestamp}.csv"
        
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, sep=';', encoding='latin1')
        csv_buffer.seek(0)
        
        s3_client.upload_fileobj(
            csv_buffer,
            'raw',
            filename,
            ExtraArgs={'ContentType': 'text/csv'}
        )
        
        logger.info(f"Dados salvos no MinIO: raw/{filename}")
        
        return {
            "status": "success",
            "message": f"Dados baixados e salvos no MinIO",
            "filename": filename,
            "records": len(df),
            "bucket": "raw"
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao buscar dados do INMET: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Recebe arquivo CSV via upload
    
    Args:
        file: Arquivo CSV a ser enviado
    """
    try:
        # Validar tipo de arquivo
        if not file.filename.endswith(('.csv', '.CSV')):
            raise HTTPException(status_code=400, detail="Apenas arquivos CSV são aceitos")
        
        # Ler arquivo
        contents = await file.read()
        # Arquivos do INMET têm metadados nas primeiras linhas, precisamos encontrar onde começam os dados
        content_str = contents.decode('latin1')
        lines = content_str.split('\n')
        
        # Procurar linha que começa com "Data" (cabeçalho)
        header_line = None
        for i, line in enumerate(lines):
            if line.strip().startswith('Data') and 'Hora' in line:
                header_line = i
                break
        
        if header_line is None:
            # Se não encontrar, tentar ler normalmente
            header_line = 0
        
        # Ler CSV pulando as linhas de metadados
        try:
            df = pd.read_csv(
                BytesIO(contents), 
                sep=';', 
                encoding='latin1', 
                skiprows=header_line,
                on_bad_lines='skip', 
                engine='python'
            )
        except Exception as e:
            logger.error(f"Erro ao ler CSV: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo CSV: {str(e)}")
        
        # Adicionar metadados
        df['ingestion_date'] = datetime.now().isoformat()
        df['source'] = 'upload'
        df['original_filename'] = file.filename
        
        # Salvar no MinIO
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upload_{timestamp}_{file.filename}"
        
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, sep=';', encoding='latin1')
        csv_buffer.seek(0)
        
        s3_client.upload_fileobj(
            csv_buffer,
            'raw',
            filename,
            ExtraArgs={'ContentType': 'text/csv'}
        )
        
        logger.info(f"Arquivo salvo no MinIO: raw/{filename}")
        
        return {
            "status": "success",
            "message": f"Arquivo enviado e salvo no MinIO",
            "filename": filename,
            "records": len(df),
            "bucket": "raw"
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Arquivo CSV vazio ou inválido")
    except Exception as e:
        logger.error(f"Erro ao processar upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.post("/store")
async def store_data(
    bucket: str,
    filename: str,
    data: dict
):
    """
    Armazena dados estruturados no MinIO
    
    Args:
        bucket: Nome do bucket (raw, processed, models)
        filename: Nome do arquivo
        data: Dados em formato JSON
    """
    try:
        # Validar bucket
        valid_buckets = ['raw', 'processed', 'models']
        if bucket not in valid_buckets:
            raise HTTPException(
                status_code=400,
                detail=f"Bucket inválido. Use um dos: {valid_buckets}"
            )
        
        # Converter dados para DataFrame e depois CSV
        df = pd.DataFrame(data)
        df['storage_date'] = datetime.now().isoformat()
        
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, sep=';', encoding='latin1')
        csv_buffer.seek(0)
        
        s3_client.upload_fileobj(
            csv_buffer,
            bucket,
            filename,
            ExtraArgs={'ContentType': 'text/csv'}
        )
        
        logger.info(f"Dados armazenados no MinIO: {bucket}/{filename}")
        
        return {
            "status": "success",
            "message": f"Dados armazenados no MinIO",
            "filename": filename,
            "bucket": bucket,
            "records": len(df)
        }
        
    except Exception as e:
        logger.error(f"Erro ao armazenar dados: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


@app.get("/list_files")
async def list_files(bucket: str = "raw"):
    """
    Lista arquivos em um bucket do MinIO
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    "filename": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat()
                })
        
        return {
            "bucket": bucket,
            "count": len(files),
            "files": files
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
    


@router.post("/upload_all_data")
async def upload_all_data():
    base_folder = "/app/data"
    uploaded_files = []

    for root, dirs, files in os.walk(base_folder):
        for filename in files:
            # Aceita .csv e .CSV etc.
            if filename.lower().endswith(".csv"):
                full_path = os.path.join(root, filename)

                try:
                    # Abrir arquivo como bytes
                    with open(full_path, "rb") as f:
                        s3_client.upload_fileobj(
                            f,
                            "raw",      # bucket
                            filename    # nome do arquivo no bucket
                        )

                    uploaded_files.append(filename)

                except Exception as e:
                    return {
                        "status": "error",
                        "file": filename,
                        "error": str(e)
                    }

    return {
        "status": "success",
        "total_uploaded": len(uploaded_files),
        "files": uploaded_files
    }


app.include_router(router)
