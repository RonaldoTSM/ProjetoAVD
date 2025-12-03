FROM jupyter/scipy-notebook:latest

USER root

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

# Instalar pacotes Python adicionais
RUN pip install --no-cache-dir \
    boto3==1.29.7 \
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.23 \
    mlflow==2.8.1 \
    scikit-learn==1.3.2 \
    matplotlib==3.8.2 \
    seaborn==0.13.0 \
    plotly==5.18.0 \
    python-dotenv==1.0.0

WORKDIR /home/jovyan/work

