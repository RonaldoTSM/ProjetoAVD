FROM ghcr.io/mlflow/mlflow:v2.8.1

# Instalar dependências necessárias para psycopg2-binary
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    build-essential \
    && pip install psycopg2-binary \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
