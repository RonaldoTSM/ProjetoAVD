# Projeto AVD - Análise e Visualização de Dados Meteorológicos

## 📋 Informações do Projeto

**Disciplina:** Análise e Visualização de Dados (AVD)  
**Instituição:** CESAR SCHOOL  
**Projeto:** Pipeline completo de BI para análise de dados meteorológicos do INMET

## 👥 Membros do Grupo

*Adicione os nomes e GitHub dos membros do grupo aqui*

## 🎯 Objetivo

Desenvolver um pipeline completo de Business Intelligence (BI) para coleta, tratamento, integração e visualização de dados meteorológicos do INMET, utilizando uma arquitetura containerizada com Docker.

## 🏗️ Arquitetura

O projeto utiliza uma arquitetura em microserviços containerizados:

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│ FastAPI │────▶│  MinIO  │────▶│PostgreSQL│
│ (8000)  │     │(9000)   │     │  (5432)  │
└─────────┘     └─────────┘     └──────────┘
     │                │                │
     │                │                │
     └────────────────┼────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌─────────┐  ┌─────────┐  ┌──────────┐
    │ Jupyter │  │ MLFlow  │  │ Trendz  │
    │ (8880)  │  │ (5000)  │  │ (8888)  │
    └─────────┘  └─────────┘  └──────────┘
```

### Componentes

1. **FastAPI (porta 8000)**: API para ingestão de dados
   - `/fetch_inmet`: Baixa dados do INMET
   - `/upload`: Recebe arquivos CSV
   - `/store`: Armazena dados no MinIO

2. **MinIO (portas 9000/9090)**: Armazenamento S3-compatible
   - Bucket `raw/`: Dados brutos
   - Bucket `processed/`: Dados tratados
   - Bucket `models/`: Modelos ML

3. **PostgreSQL (porta 5432)**: Banco de dados estruturado
   - Tabela `weather_hourly`: Dados horários
   - Tabela `weather_daily`: Agregações diárias
   - Tabela `ml_models`: Metadados de modelos

4. **JupyterLab (porta 8880)**: Análise e modelagem
   - Notebooks de EDA
   - Processamento e limpeza
   - Feature engineering
   - Treinamento de modelos

5. **MLFlow (porta 5000)**: Versionamento de modelos
   - Tracking de experimentos
   - Registro de métricas e parâmetros
   - Armazenamento de artefatos

6. **Trendz Analytics (porta 8888)**: Dashboards interativos

## 🚀 Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados
- Git

### Passo a Passo

1. **Clone o repositório** (se ainda não tiver):
```bash
git clone <url-do-repositorio>
cd classificacao_conforto_termico
```

2. **Inicie todos os serviços**:
```bash
docker-compose up -d
```

3. **Aguarde os serviços iniciarem** (pode levar alguns minutos na primeira execução):
```bash
docker-compose ps
```

4. **Acesse os serviços**:

   - **FastAPI**: http://localhost:8000
     - Documentação: http://localhost:8000/docs
   
   - **MinIO Console**: http://localhost:9090
     - Usuário: `minioadmin`
     - Senha: `minioadmin`
   
   - **JupyterLab**: http://localhost:8880
     - Sem senha (desenvolvimento)
   
   - **MLFlow**: http://localhost:5000
   
   - **Trendz**: http://localhost:8888
   
   - **PostgreSQL**: `localhost:5432`
     - Usuário: `postgres`
     - Senha: `postgres`
     - Database: `weather_db`

### Upload de Dados Iniciais

Se você já tem dados CSV locais, pode fazer upload via FastAPI:

```bash
# Via curl
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/dados_2020/dados_recife_2020.CSV"

# Ou via interface web em http://localhost:8000/docs
```

### Processamento de Dados

1. Acesse o JupyterLab: http://localhost:8880
2. Abra o notebook `notebooks/02_processamento_limpeza.py`
3. Execute o script para processar os dados do bucket `raw/` e salvar em `processed/` e PostgreSQL

### Treinamento de Modelos

1. No JupyterLab, abra `notebooks/03_modelagem_conforto_termico.ipynb`
2. Execute as células para treinar o modelo
3. O modelo será versionado automaticamente no MLFlow

## 📊 Dados

### Cidades Monitoradas (Pernambuco)

- Arco Verde
- Cabrobó
- Caruaru
- Floresta
- Garanhuns
- Ibimirim
- Ouricuri
- Palmares
- Petrolina
- Recife
- Salgueiro
- Serra Talhada
- Surubim

### Período

Dados de 2020 a 2024 (5 anos)

### Variáveis Meteorológicas

- Temperatura (°C)
- Umidade relativa (%)
- Pressão atmosférica (mB)
- Direção do vento (graus)
- Velocidade do vento (m/s)
- Radiação solar (Kj/m²)
- Precipitação (mm)

## 📁 Estrutura do Projeto

```
classificacao_conforto_termico/
├── docker-compose.yml          # Orquestração dos serviços
├── data/                       # Dados CSV locais
│   ├── dados_2020/
│   ├── dados_2021/
│   ├── dados_2022/
│   ├── dados_2023/
│   ├── dados_2024/
│   └── processed/
├── fastapi/                    # API de ingestão
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── jupyterlab/                 # Ambiente Jupyter
│   ├── Dockerfile
│   └── requirements.txt
├── mlflow/                     # Configuração MLFlow
├── notebooks/                  # Notebooks de análise
│   ├── 01_eda_limpeza.ipynb
│   ├── 02_processamento_limpeza.py
│   ├── 03_modelagem_conforto_termico.ipynb
│   └── utils.py
├── sql_scripts/                # Scripts SQL
│   └── 01_create_tables.sql
├── trendz/                     # Configuração Trendz
├── reports/                    # Relatórios gerados
├── data_utils.py              # Utilitários de dados
├── claude.md                  # Documentação do projeto
└── README.md                  # Este arquivo
```

## 🔧 Comandos Úteis

### Docker Compose

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Ver logs
docker-compose logs -f [servico]

# Reconstruir imagens
docker-compose build

# Reiniciar um serviço específico
docker-compose restart [servico]
```

### MinIO

```bash
# Listar buckets
docker exec minio mc ls myminio/

# Listar arquivos em um bucket
docker exec minio mc ls myminio/raw/

# Baixar arquivo
docker exec minio mc cp myminio/raw/arquivo.csv /tmp/
```

### PostgreSQL

```bash
# Conectar ao banco
docker exec -it postgres psql -U postgres -d weather_db

# Executar query
docker exec postgres psql -U postgres -d weather_db -c "SELECT COUNT(*) FROM weather_hourly;"
```

## 📈 Modelos Implementados

O projeto suporta os seguintes problemas/modelos:

1. Agrupar padrões climáticos (Clustering)
2. Classificar dias chuvosos vs ensolarados (Classificação binária)
3. Prever temperatura horária (Regressão temporal)
4. Agrupar estações por perfil (Clustering)
5. **Classificar conforto térmico** (Classificação multiclasse) - *Implementado*
6. Prever umidade relativa (Regressão)
7. Agrupar padrões de vento (Clustering)
8. Classificar intensidade da chuva (Classificação multiclasse)
9. Agrupar condições extremas (Clustering)
10. Prever sensação térmica (Regressão)

## 🧪 Testes

Para testar a API FastAPI:

```bash
# Health check
curl http://localhost:8000/health

# Listar arquivos no MinIO
curl http://localhost:8000/list_files?bucket=raw

# Upload de arquivo
curl -X POST "http://localhost:8000/upload" \
  -F "file=@caminho/para/arquivo.csv"
```

## 📝 Notas de Desenvolvimento

- Os dados são armazenados em volumes Docker para persistência
- As credenciais padrão são para desenvolvimento apenas
- Em produção, altere todas as senhas e use variáveis de ambiente
- O MinIO é configurado automaticamente com os buckets necessários

## 🐛 Troubleshooting

### Serviços não iniciam

```bash
# Verificar logs
docker-compose logs

# Verificar portas em uso
lsof -i :8000
lsof -i :9000
```

### Erro de conexão com MinIO

- Verifique se o MinIO está saudável: `docker-compose ps minio`
- Aguarde alguns segundos após iniciar o MinIO

### Erro de conexão com PostgreSQL

- Verifique se o PostgreSQL está pronto: `docker-compose ps postgres`
- Aguarde a inicialização completa do banco

## 📄 Licença

Ver arquivo LICENSE

## 📚 Referências

- [INMET](https://portal.inmet.gov.br/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MLFlow Documentation](https://www.mlflow.org/docs/latest/index.html)
- [MinIO Documentation](https://min.io/docs/)
- [Trendz Analytics](https://trendz-iot.github.io/)

