-- Script de criação das tabelas para armazenar dados meteorológicos
-- Banco: weather_db

-- Tabela principal de dados meteorológicos horários
CREATE TABLE IF NOT EXISTS weather_hourly (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP NOT NULL,
    estacao VARCHAR(50),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    temperatura DECIMAL(5,2),
    umidade_relativa DECIMAL(5,2),
    pressao_atmosferica DECIMAL(7,2),
    direcao_vento DECIMAL(5,2),
    velocidade_vento DECIMAL(5,2),
    radiacao_solar DECIMAL(8,2),
    precipitacao DECIMAL(6,2),
    ano INTEGER,
    mes INTEGER,
    dia INTEGER,
    hora INTEGER,
    arquivo_origem VARCHAR(255),
    ingestion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_weather_hourly_data_hora ON weather_hourly(data_hora);
CREATE INDEX IF NOT EXISTS idx_weather_hourly_estacao ON weather_hourly(estacao);
CREATE INDEX IF NOT EXISTS idx_weather_hourly_cidade ON weather_hourly(cidade);
CREATE INDEX IF NOT EXISTS idx_weather_hourly_ano ON weather_hourly(ano);
CREATE INDEX IF NOT EXISTS idx_weather_hourly_ano_mes ON weather_hourly(ano, mes);

-- Tabela para dados processados/agregados
CREATE TABLE IF NOT EXISTS weather_daily (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    estacao VARCHAR(50),
    cidade VARCHAR(100),
    temperatura_media DECIMAL(5,2),
    temperatura_max DECIMAL(5,2),
    temperatura_min DECIMAL(5,2),
    umidade_media DECIMAL(5,2),
    pressao_media DECIMAL(7,2),
    velocidade_vento_media DECIMAL(5,2),
    radiacao_solar_total DECIMAL(8,2),
    precipitacao_total DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(data, estacao)
);

CREATE INDEX IF NOT EXISTS idx_weather_daily_data ON weather_daily(data);
CREATE INDEX IF NOT EXISTS idx_weather_daily_estacao ON weather_daily(estacao);

-- Tabela para metadados de arquivos processados
CREATE TABLE IF NOT EXISTS file_metadata (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) UNIQUE NOT NULL,
    bucket VARCHAR(50),
    file_size BIGINT,
    records_count INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para modelos ML versionados
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(50),
    model_type VARCHAR(100),
    mlflow_run_id VARCHAR(255),
    metrics JSONB,
    parameters JSONB,
    artifact_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'training',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ml_models_name ON ml_models(model_name);
CREATE INDEX IF NOT EXISTS idx_ml_models_mlflow_run_id ON ml_models(mlflow_run_id);

-- Tabela para previsões do modelo
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ml_models(id),
    data_hora TIMESTAMP NOT NULL,
    estacao VARCHAR(50),
    cidade VARCHAR(100),
    prediction_value DECIMAL(10,4),
    confidence DECIMAL(5,4),
    features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_data_hora ON predictions(data_hora);

