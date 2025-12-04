# Projeto AVD - Análise e Visualização de Dados Meteorológicos

## Informações do Projeto

**Disciplina:** Análise e Visualização de Dados (AVD)  
**Instituição:** CESAR SCHOOL  
**Projeto:** Pipeline completo de BI para análise de dados meteorológicos do INMET

## Membros do Grupo

- Brandon Hunt
- Letícia Lopes
- Luís Melo
- Luca Gomes
- Lucas Rosati
- Ronaldo Souto Maior

## Objetivo

Desenvolver um pipeline completo de Business Intelligence (BI) para coleta, tratamento, integração e visualização de dados meteorológicos do INMET, utilizando uma arquitetura containerizada com Docker.

## Arquitetura

O projeto utiliza uma arquitetura em microserviços containerizados:

```
FastAPI (8000) -> MinIO (9000) -> PostgreSQL (5434)
                      |
                      v
              JupyterLab (8880)
                      |
                      v
              MLFlow (5001)
```

### Componentes

1. **FastAPI (porta 8000)**: API para ingestão de dados
   - `/fetch_inmet`: Baixa dados do INMET
   - `/upload`: Recebe arquivos CSV
   - `/store`: Armazena dados no MinIO
   - `/list_files`: Lista arquivos nos buckets
   - `/health`: Health check

2. **MinIO (portas 9000/9091)**: Armazenamento S3-compatible
   - Bucket `raw/`: Dados brutos do INMET
   - Bucket `processed/`: Dados tratados e limpos
   - Bucket `models/`: Modelos ML versionados
   - Console: http://localhost:9091 (usuário: minioadmin, senha: minioadmin)

3. **PostgreSQL (porta 5434)**: Banco de dados estruturado
   - Tabela `weather_hourly`: Dados meteorológicos horários
   - Tabela `weather_daily`: Agregações diárias
   - Tabela `ml_models`: Metadados de modelos ML
   - Tabela `file_metadata`: Metadados de arquivos processados
   - Tabela `predictions`: Previsões dos modelos

4. **JupyterLab (porta 8880)**: Ambiente de análise e modelagem
   - Notebooks de EDA (Exploratory Data Analysis)
   - Processamento e limpeza de dados
   - Feature engineering
   - Treinamento de modelos de machine learning
   - Acesso: http://localhost:8880 (sem senha)

5. **MLFlow (porta 5001)**: Versionamento e tracking de modelos
   - Tracking de experimentos
   - Registro de métricas e parâmetros
   - Armazenamento de artefatos no MinIO
   - Acesso: http://localhost:5001

## Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados
- Git
- Pelo menos 4GB de RAM disponível

### Instalação e Execução

1. **Clone o repositório**:
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

Todos os serviços devem estar com status "Up" e "healthy".

4. **Acesse os serviços**:

   - **FastAPI**: http://localhost:8000
     - Documentação interativa: http://localhost:8000/docs
   
   - **MinIO Console**: http://localhost:9091
     - Usuário: `minioadmin`
     - Senha: `minioadmin`
   
   - **JupyterLab**: http://localhost:8880
     - Sem senha (apenas para desenvolvimento)
   
   - **MLFlow**: http://localhost:5001
   
   - **PostgreSQL**: `localhost:5434`
     - Usuário: `postgres`
     - Senha: `postgres`
     - Database: `weather_db`

### Upload de Dados

#### Opção 1: Via FastAPI (Recomendado)

```bash
# Via curl
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/dados_2020/dados_recife_2020.CSV"

# Ou via interface web em http://localhost:8000/docs
```

#### Opção 2: Via Script Python

```bash
python scripts/upload_data.py
```

### Carregar Dados no PostgreSQL

Após fazer upload dos dados no MinIO, é necessário carregá-los no PostgreSQL:

1. Acesse o JupyterLab: http://localhost:8880
2. Crie um novo notebook ou abra um existente
3. Execute:

```python
exec(open('/home/jovyan/work/notebooks/carregar_dados_postgresql.py').read())
```

Este script irá:
- Ler todos os arquivos do bucket `raw/` no MinIO
- Limpar e processar os dados
- Salvar na tabela `weather_hourly` do PostgreSQL
- Criar agregação diária na tabela `weather_daily`

Tempo estimado: 5-10 minutos dependendo da quantidade de dados.

### Processamento e Análise

1. **Análise Exploratória (EDA)**:
   - Acesse JupyterLab: http://localhost:8880
   - Abra: `notebooks/04_eda_completo.ipynb`
   - Execute todas as células para análise exploratória

2. **Modelagem**:
   - Abra: `notebooks/03_modelagem_conforto_termico.ipynb`
   - Execute todas as células para treinar o modelo
   - O modelo será automaticamente versionado no MLFlow e salvo no MinIO

## Dados

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

## Estrutura do Projeto

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
├── notebooks/                  # Notebooks de análise
│   ├── 01_eda_limpeza.ipynb
│   ├── 02_processamento_limpeza.py
│   ├── 03_modelagem_conforto_termico.ipynb
│   ├── 04_eda_completo.ipynb
│   ├── carregar_dados_postgresql.py
│   └── utils.py
├── sql_scripts/                # Scripts SQL
│   └── 01_create_tables.sql
├── scripts/                    # Scripts auxiliares
│   ├── upload_data.py
│   └── upload_data_simples.py
├── data_utils.py              # Utilitários de dados
├── claude.md                  # Especificações do projeto
└── README.md                  # Este arquivo
```

## Fluxo de Dados

1. **Ingestão**: FastAPI recebe dados do INMET (API ou CSV) e armazena no MinIO (bucket `raw/`)
2. **Processamento**: Script Python processa dados do MinIO, limpa e estrutura
3. **Armazenamento**: Dados processados são salvos no PostgreSQL (tabela `weather_hourly`)
4. **Análise**: JupyterLab lê dados do PostgreSQL para análise exploratória
5. **Modelagem**: Modelos são treinados usando dados do PostgreSQL
6. **Versionamento**: Modelos são versionados no MLFlow e armazenados no MinIO (bucket `models/`)

## Comandos Úteis

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

# Ver status dos serviços
docker-compose ps
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

# Verificar tabelas
docker exec postgres psql -U postgres -d weather_db -c "\dt"
```

## Modelos Implementados

O projeto implementa classificação de conforto térmico baseado em dados meteorológicos:

- **Problema**: Classificação multiclasse de conforto térmico
- **Classes**: Muito Frio, Frio, Confortável, Quente, Muito Quente
- **Algoritmo**: Random Forest Classifier
- **Features**: Umidade relativa, velocidade do vento, precipitação, pressão atmosférica, features temporais cíclicas, heat index
- **Nota**: A temperatura não é usada diretamente como feature para evitar data leakage

### Outros Problemas Suportados (não implementados)

1. Agrupar padrões climáticos (Clustering)
2. Classificar dias chuvosos vs ensolarados (Classificação binária)
3. Prever temperatura horária (Regressão temporal)
4. Agrupar estações por perfil (Clustering)
5. Prever umidade relativa (Regressão)
6. Agrupar padrões de vento (Clustering)
7. Classificar intensidade da chuva (Classificação multiclasse)
8. Agrupar condições extremas (Clustering)
9. Prever sensação térmica (Regressão)

## Testes

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

## Troubleshooting

### Serviços não iniciam

```bash
# Verificar logs
docker-compose logs

# Verificar portas em uso
lsof -i :8000
lsof -i :9000
lsof -i :5434
lsof -i :8880
lsof -i :5001
```

### Erro de conexão com MinIO

- Verifique se o MinIO está saudável: `docker-compose ps minio`
- Aguarde alguns segundos após iniciar o MinIO
- Verifique se os buckets foram criados automaticamente

### Erro de conexão com PostgreSQL

- Verifique se o PostgreSQL está pronto: `docker-compose ps postgres`
- Aguarde a inicialização completa do banco
- Verifique se as tabelas foram criadas: `docker exec postgres psql -U postgres -d weather_db -c "\dt"`

### Erro ao carregar dados no PostgreSQL

- Certifique-se de que os dados foram carregados no MinIO primeiro
- Verifique se o script `carregar_dados_postgresql.py` está no caminho correto
- Use o caminho absoluto: `/home/jovyan/work/notebooks/carregar_dados_postgresql.py`

### Erro "column processing_date does not exist"

Este erro ocorre se o script tentar inserir uma coluna que não existe. O script foi corrigido para remover essa coluna antes de salvar. Certifique-se de usar a versão mais recente do script.

### Modelo com 100% de acurácia

Se o modelo apresentar 100% de acurácia, isso indica data leakage. O problema ocorre quando a variável usada para criar o target também está nas features. A solução é remover `temperatura` da lista de features no notebook de modelagem, já que o target é baseado em temperatura.

## Notas de Desenvolvimento

- Os dados são armazenados em volumes Docker para persistência
- As credenciais padrão são para desenvolvimento apenas
- Em produção, altere todas as senhas e use variáveis de ambiente
- O MinIO é configurado automaticamente com os buckets necessários
- O PostgreSQL cria as tabelas automaticamente via scripts em `sql_scripts/`
- Portas configuradas para evitar conflitos: PostgreSQL (5434), MinIO Console (9091), MLFlow (5001)

## Licença

Ver arquivo LICENSE

## Referências

- [INMET](https://portal.inmet.gov.br/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MLFlow Documentation](https://www.mlflow.org/docs/latest/index.html)
- [MinIO Documentation](https://min.io/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
