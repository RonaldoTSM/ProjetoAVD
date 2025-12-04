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

## Como Executar o Projeto Completo

### Pré-requisitos

- Docker e Docker Compose instalados
- Git
- Pelo menos 4GB de RAM disponível
- Navegador web

### Passo a Passo Completo

#### 1. Iniciar os Serviços Docker

```bash
# Clone o repositório (se ainda não tiver)
git clone <url-do-repositorio>
cd classificacao_conforto_termico

# Inicie todos os serviços
docker-compose up -d
```

Aguarde alguns minutos para todos os serviços iniciarem. Verifique o status:

```bash
docker-compose ps
```

Todos os serviços devem estar com status "Up".

#### 2. Upload de Dados via FastAPI

1. **Acesse a documentação interativa da FastAPI**:
   - URL: http://localhost:8000/docs

2. **Faça upload de todos os arquivos CSV**:
   - Na interface do FastAPI, encontre o endpoint `/upload`
   - Clique em "Try it out"
   - Clique em "Choose File" e selecione os arquivos CSV da pasta `data/`
   - Para fazer upload de múltiplos arquivos, repita o processo ou use o script:
   
   ```bash
   python scripts/upload_data.py
   ```

   **Importante**: Faça upload de todos os arquivos CSV antes de prosseguir.

#### 3. Processar Dados no JupyterLab

1. **Acesse o JupyterLab**:
   - URL: http://localhost:8880
   - Não é necessário senha

2. **Abra o terminal no JupyterLab**:
   - Clique em "File" → "New" → "Terminal"

3. **Execute o notebook 02 (processamento)**:
   - No terminal, execute:
   
   ```bash
   cd /home/jovyan/work/notebooks
   python 02_processamento_limpeza.py
   ```
   
   Ou abra o arquivo `02_processamento_limpeza.py` e execute todas as células.

   Este script irá:
   - Ler todos os arquivos do bucket `raw/` no MinIO
   - Limpar e processar os dados
   - Salvar na tabela `weather_hourly` do PostgreSQL
   - Criar dados processados no bucket `processed/` do MinIO

#### 4. Executar Notebook 05 (Envio para ThingsBoard)

**IMPORTANTE**: 
- Este passo pode ser executado ANTES ou DEPOIS de configurar o ThingsBoard
- Se executar antes, você precisará atualizar os tokens depois de criar os dispositivos
- Se executar depois, você já terá os tokens dos dispositivos

1. **No JupyterLab, abra o arquivo `05_push`**:
   - Localização: `notebooks/05_push`
   - Este é um script Python que envia dados para o ThingsBoard

2. **Edite o token do dispositivo** (se já tiver criado dispositivos no ThingsBoard):
   - No código, localize a seção `CITY_DEVICES`
   - Substitua os tokens pelos tokens reais dos seus dispositivos no ThingsBoard
   - Você obterá os tokens após criar os dispositivos no ThingsBoard (passo 5.6)
   - Se ainda não criou os dispositivos, pode usar um token temporário e atualizar depois

3. **Execute o script**:
   - Execute todas as células ou rode via terminal:
   
   ```bash
   python /home/jovyan/work/notebooks/05_push
   ```
   
   Este script:
   - Lê dados processados do MinIO (bucket `processed/`)
   - Classifica conforto térmico
   - Envia dados para o ThingsBoard via API REST
   - Envia dados de todas as 13 cidades de Pernambuco

#### 5. Configurar ThingsBoard

1. **Acesse o ThingsBoard**:
   - URL: http://localhost:8080

2. **Login inicial**:
   - Email: `sysadmin@thingsboard.org`
   - Senha: `sysadmin`

3. **Criar um Tenant**:
   - Após fazer login, você verá a tela de administração
   - Vá em "Tenants" → "Add Tenant"
   - Preencha os dados do tenant (nome, email, etc.)
   - Salve o tenant

4. **Acessar página de administração do perfil**:
   - No menu, vá em "Profile" ou "Administration"
   - Configure as permissões necessárias

5. **Fazer login no Tenant criado**:
   - Faça logout do sysadmin
   - Faça login com as credenciais do tenant que você criou

6. **Criar dispositivos** (se ainda não criou):
   - Vá em "Devices" → "Add Device"
   - Crie dispositivos para cada cidade (ou use um dispositivo genérico)
   - **Copie o token de acesso de cada dispositivo** (você precisará para o notebook 05)

#### 6. Configurar Trendz Analytics

1. **Acesse o Trendz**:
   - URL: http://localhost:8888

2. **Fazer login**:
   - Use as mesmas credenciais do tenant criado no ThingsBoard

3. **Adicionar Data Source (PostgreSQL)**:
   - Vá em "Settings" → "Data Sources" → "Add Data Source"
   - Selecione "PostgreSQL"
   - Preencha os dados de conexão:
     - **URL JDBC**: `jdbc:postgresql://postgres:5432/weather_db`
     - **Usuário**: `postgres`
     - **Senha**: `postgres`
   - Teste a conexão e salve

4. **Criar uma View e adicionar componentes**:
   - Vá em "Views" → "Create New View"
   - Adicione componentes (gráficos, tabelas, etc.)
   - Configure os componentes para usar a data source do PostgreSQL
   - Selecione a tabela `weather_hourly` ou `weather_daily`
   - Configure os campos e filtros desejados
   - Salve a view

#### 7. Visualizar Dashboards

Agora você pode:
- **ThingsBoard**: Visualizar dados em tempo real dos dispositivos
- **Trendz**: Visualizar análises e gráficos customizados dos dados do PostgreSQL
- **Streamlit**: Acessar http://localhost:8501 para dashboard alternativo

### Resumo dos Passos (Ordem de Execução)

```
1. docker-compose up -d
   └─ Inicia todos os serviços Docker

2. FastAPI /docs → Upload de arquivos
   └─ http://localhost:8000/docs → POST /upload → Selecionar todos os CSVs

3. JupyterLab → Executar notebook 02
   └─ http://localhost:8880 → Terminal → python 02_processamento_limpeza.py
   └─ Processa dados do MinIO e salva no PostgreSQL

4. ThingsBoard (8080) → Login sysadmin
   └─ Email: sysadmin@thingsboard.org
   └─ Senha: sysadmin

5. ThingsBoard → Criar Tenant
   └─ Tenants → Add Tenant → Preencher dados → Salvar

6. ThingsBoard → Criar Dispositivos (opcional, mas recomendado)
   └─ Devices → Add Device → Copiar token de acesso

7. ThingsBoard → Login no Tenant criado
   └─ Logout do sysadmin → Login com credenciais do tenant

8. JupyterLab → Executar notebook 05
   └─ Editar tokens em CITY_DEVICES (se já criou dispositivos)
   └─ python /home/jovyan/work/notebooks/05_push
   └─ Envia dados para ThingsBoard

9. Trendz (8888) → Login no Tenant
   └─ Usar mesmas credenciais do tenant do ThingsBoard

10. Trendz → Settings → Add Data Source
    └─ Tipo: PostgreSQL
    └─ URL: jdbc:postgresql://postgres:5432/weather_db
    └─ Usuário: postgres
    └─ Senha: postgres
    └─ Testar conexão → Salvar

11. Trendz → Criar View → Adicionar componentes
    └─ Views → Create New View
    └─ Adicionar gráficos, tabelas, etc.
    └─ Configurar para usar data source do PostgreSQL
    └─ Selecionar tabela weather_hourly ou weather_daily
```

### Notas Importantes

- **Ordem de execução**: Os passos 1-3 são obrigatórios nesta ordem. Os passos 4-11 podem ter alguma flexibilidade, mas a ordem sugerida é a mais eficiente.

- **Tokens do ThingsBoard**: Se você executar o notebook 05 antes de criar os dispositivos, pode usar tokens temporários e atualizar depois. Ou crie os dispositivos primeiro e copie os tokens antes de executar o notebook 05.

- **Data Source no Trendz**: A string JDBC completa é: `jdbc:postgresql://postgres:5432/weather_db`
  - Host: `postgres` (nome do container Docker)
  - Porta: `5432` (porta interna do container)
  - Database: `weather_db`
  - Usuário: `postgres`
  - Senha: `postgres`

### Acessos Rápidos

- **FastAPI**: http://localhost:8000/docs
- **JupyterLab**: http://localhost:8880
- **ThingsBoard**: http://localhost:8080
- **Trendz Analytics**: http://localhost:8888
- **Streamlit**: http://localhost:8501
- **MLFlow**: http://localhost:5001
- **MinIO Console**: http://localhost:9091 (usuário: minioadmin, senha: minioadmin)
- **PostgreSQL**: `localhost:5434` (usuário: postgres, senha: postgres, database: weather_db)

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
│   ├── 02_processamento_limpeza.py  # Processa dados do MinIO para PostgreSQL
│   ├── 03_modelagem_conforto_termico.ipynb
│   ├── 04_eda_completo.ipynb
│   ├── 05_push                  # Envia dados para ThingsBoard (executar antes de configurar TB)
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
