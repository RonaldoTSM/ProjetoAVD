# 🚀 Guia Rápido de Início

## Passo 1: Iniciar os Serviços

```bash
docker-compose up -d
```

Aguarde alguns minutos para todos os serviços iniciarem. Verifique o status:

```bash
docker-compose ps
```

## Passo 2: Verificar Serviços

### FastAPI
- URL: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### MinIO Console
- URL: http://localhost:9090
- Usuário: `minioadmin`
- Senha: `minioadmin`

### JupyterLab
- URL: http://localhost:8880
- Sem senha (desenvolvimento)

### MLFlow
- URL: http://localhost:5000

## Passo 3: Upload de Dados

### Opção 1: Via Script Python
```bash
cd scripts
python3 upload_data.py
```

### Opção 2: Via Script Bash
```bash
chmod +x scripts/upload_data.sh
./scripts/upload_data.sh
```

### Opção 3: Via API (curl)
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@data/dados_2020/dados_recife_2020.CSV"
```

### Opção 4: Via Interface Web
1. Acesse http://localhost:8000/docs
2. Use o endpoint `/upload`
3. Selecione um arquivo CSV
4. Clique em "Execute"

## Passo 4: Processar Dados

1. Acesse o JupyterLab: http://localhost:8880
2. Navegue até `notebooks/`
3. Abra `02_processamento_limpeza.py`
4. Execute o script (ou converta para notebook e execute as células)

Isso irá:
- Ler dados do bucket `raw/` no MinIO
- Limpar e processar os dados
- Salvar no bucket `processed/`
- Carregar no PostgreSQL

## Passo 5: Treinar Modelo

1. No JupyterLab, abra `notebooks/03_modelagem_conforto_termico.ipynb`
2. Execute todas as células
3. O modelo será versionado no MLFlow automaticamente

## Passo 6: Visualizar Resultados

### MLFlow
- Acesse http://localhost:5000
- Veja os experimentos, métricas e modelos

### PostgreSQL
```bash
docker exec -it postgres psql -U postgres -d weather_db

# Exemplos de queries:
SELECT COUNT(*) FROM weather_hourly;
SELECT cidade, COUNT(*) FROM weather_hourly GROUP BY cidade;
SELECT * FROM weather_daily LIMIT 10;
```

### MinIO
- Acesse http://localhost:9090
- Navegue pelos buckets:
  - `raw/`: Dados brutos
  - `processed/`: Dados tratados
  - `models/`: Modelos ML

## Comandos Úteis

### Ver logs
```bash
docker-compose logs -f [servico]
# Exemplo: docker-compose logs -f fastapi
```

### Parar serviços
```bash
docker-compose down
```

### Reiniciar um serviço
```bash
docker-compose restart [servico]
```

### Limpar volumes (⚠️ apaga dados)
```bash
docker-compose down -v
```

## Troubleshooting

### Porta já em uso
```bash
# Verificar portas
lsof -i :8000
lsof -i :9000

# Parar processo ou alterar porta no docker-compose.yml
```

### Serviço não inicia
```bash
# Ver logs
docker-compose logs [servico]

# Reconstruir
docker-compose build [servico]
docker-compose up -d [servico]
```

### Erro de conexão
- Aguarde alguns segundos após iniciar os serviços
- Verifique se todos os serviços estão saudáveis: `docker-compose ps`

