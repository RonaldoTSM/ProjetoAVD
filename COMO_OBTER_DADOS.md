# 📥 Como Obter os Dados Meteorológicos

Você tem **3 opções principais** para obter os dados do INMET:

## ✅ Opção 1: Usar os Dados que Já Estão no Projeto (RECOMENDADO)

Você já tem dados na pasta `data/` organizados por ano (2020-2024) e por cidade!

### Passos:

1. **Iniciar os serviços**:
```bash
docker-compose up -d
```

2. **Fazer upload dos dados existentes**:
```bash
# Opção A: Script Python
python3 scripts/upload_data.py

# Opção B: Script Bash
chmod +x scripts/upload_data.sh
./scripts/upload_data.sh

# Opção C: Via API (um arquivo por vez)
curl -X POST "http://localhost:8000/upload" \
  -F "file=@data/dados_2020/dados_recife_2020.CSV"
```

3. **Verificar no MinIO**:
   - Acesse http://localhost:9090
   - Login: `minioadmin` / `minioadmin`
   - Verifique o bucket `raw/`

**Vantagens**: ✅ Rápido, ✅ Dados já disponíveis, ✅ Funciona imediatamente

---

## 🌐 Opção 2: Baixar do Portal do INMET

### Passo a Passo:

1. **Acesse o Portal do INMET**:
   - URL: https://portal.inmet.gov.br/
   - Vá em "Dados Históricos" ou "Dados Meteorológicos"

2. **Selecione as Estações de Pernambuco**:
   - Escolha as 13 cidades do projeto
   - Selecione o período (2020-2024)

3. **Download dos Dados**:
   - Baixe os arquivos CSV
   - Salve na pasta `data/dados_XXXX/` (onde XXXX é o ano)

4. **Estrutura de Pastas**:
```
data/
├── dados_2020/
│   ├── dados_recife_2020.CSV
│   ├── dados_caruaru_2020.CSV
│   └── ...
├── dados_2021/
│   └── ...
└── ...
```

5. **Fazer Upload** (mesmo processo da Opção 1)

**Links Úteis**:
- Portal INMET: https://portal.inmet.gov.br/
- Dados Históricos: https://portal.inmet.gov.br/dadoshistoricos
- Estações Automáticas: https://portal.inmet.gov.br/estacoes

---

## 🔌 Opção 3: Usar a API do INMET (Avançado)

O INMET possui uma API pública, mas requer conhecimento dos códigos das estações.

### Códigos das Estações de Pernambuco:

| Cidade | Código da Estação | Tipo |
|--------|-------------------|------|
| Recife | A827 | Automática |
| Caruaru | A827 | Automática |
| Petrolina | A827 | Automática |
| Garanhuns | A827 | Automática |
| ... | ... | ... |

**Nota**: Os códigos podem variar. Verifique no portal do INMET.

### Usando a API via FastAPI:

1. **Iniciar os serviços**:
```bash
docker-compose up -d
```

2. **Fazer requisição**:
```bash
# Exemplo (ajuste as datas e código da estação)
curl -X POST "http://localhost:8000/fetch_inmet?start_date=2024-01-01&end_date=2024-01-31&station_code=A827"
```

3. **Ou via interface web**:
   - Acesse http://localhost:8000/docs
   - Use o endpoint `/fetch_inmet`
   - Preencha os parâmetros:
     - `start_date`: Data inicial (YYYY-MM-DD)
     - `end_date`: Data final (YYYY-MM-DD)
     - `station_code`: Código da estação (opcional)

### Endpoints da API do INMET:

A API do INMET tem diferentes endpoints. O código atual usa:
- Base URL: `https://apitempo.inmet.gov.br/estacao`

**Documentação da API**:
- https://portal.inmet.gov.br/dadoshistoricos
- https://apitempo.inmet.gov.br/

**⚠️ Importante**: A API do INMET pode ter limitações de taxa ou mudanças. Se não funcionar, use as Opções 1 ou 2.

---

## 📋 Resumo das Opções

| Opção | Dificuldade | Tempo | Recomendado Para |
|-------|-------------|-------|------------------|
| **1. Dados Existentes** | ⭐ Fácil | ⚡ Imediato | Começar rápido |
| **2. Portal INMET** | ⭐⭐ Médio | ⏱️ 10-30 min | Dados atualizados |
| **3. API INMET** | ⭐⭐⭐ Avançado | ⏱️ Variável | Automação |

---

## 🚀 Recomendação

**Para começar rapidamente**: Use a **Opção 1** (dados existentes)

**Para dados atualizados**: Use a **Opção 2** (portal do INMET)

**Para automação**: Use a **Opção 3** (API), mas tenha um plano B

---

## 🔍 Verificar Dados Após Upload

### Via MinIO Console:
1. Acesse http://localhost:9090
2. Login: `minioadmin` / `minioadmin`
3. Navegue até o bucket `raw/`
4. Verifique os arquivos enviados

### Via API:
```bash
curl "http://localhost:8000/list_files?bucket=raw"
```

### Via PostgreSQL:
```bash
docker exec -it postgres psql -U postgres -d weather_db

# Ver quantos registros foram processados
SELECT COUNT(*) FROM weather_hourly;

# Ver por cidade
SELECT cidade, COUNT(*) 
FROM weather_hourly 
GROUP BY cidade;
```

---

## ❓ Problemas Comuns

### "Arquivo não encontrado"
- Verifique se o caminho está correto
- Use caminho absoluto ou relativo ao diretório do projeto

### "Erro ao fazer upload"
- Verifique se o FastAPI está rodando: `docker-compose ps fastapi`
- Verifique os logs: `docker-compose logs fastapi`

### "API do INMET não responde"
- A API pode estar temporariamente indisponível
- Use a Opção 1 ou 2 como alternativa

---

## 📞 Próximos Passos

Após obter os dados:

1. ✅ Fazer upload (Opção 1, 2 ou 3)
2. ✅ Processar os dados (executar `notebooks/02_processamento_limpeza.py`)
3. ✅ Treinar modelos (executar `notebooks/03_modelagem_conforto_termico.ipynb`)
4. ✅ Visualizar resultados (MLFlow, MinIO, PostgreSQL)

