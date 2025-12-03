#!/bin/bash
# Script para fazer upload de todos os arquivos CSV para o MinIO via FastAPI

API_URL="http://localhost:8000"

echo "=== Upload de Dados Meteorológicos ==="
echo ""

# Verificar se a API está rodando
if ! curl -s "$API_URL/health" > /dev/null; then
    echo "❌ Erro: API não está respondendo em $API_URL"
    echo "   Certifique-se de que o FastAPI está rodando (docker-compose up)"
    exit 1
fi

echo "✓ API está respondendo"
echo ""

# Contador
count=0
total=0

# Encontrar todos os arquivos CSV
for csv_file in data/dados_*/dados_*.CSV data/dados_*/dados_*.csv; do
    if [ -f "$csv_file" ]; then
        total=$((total + 1))
    fi
done

echo "Encontrados $total arquivos CSV"
echo ""

# Fazer upload de cada arquivo
for csv_file in data/dados_*/dados_*.CSV data/dados_*/dados_*.csv; do
    if [ -f "$csv_file" ]; then
        count=$((count + 1))
        filename=$(basename "$csv_file")
        echo "[$count/$total] Enviando $filename..."
        
        response=$(curl -s -X POST "$API_URL/upload" \
            -F "file=@$csv_file")
        
        if echo "$response" | grep -q "success"; then
            echo "  ✓ Sucesso"
        else
            echo "  ✗ Erro: $response"
        fi
    fi
done

echo ""
echo "=== Upload concluído ==="
echo "Total enviado: $count/$total arquivos"

