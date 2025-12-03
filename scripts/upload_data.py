#!/usr/bin/env python3
"""
Script para fazer upload de todos os arquivos CSV para o MinIO via FastAPI
"""
import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

API_URL = "http://localhost:8000"
DATA_DIR = Path("data")

def check_api():
    """Verifica se a API está respondendo"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_file(file_path):
    """Faz upload de um arquivo"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/csv')}
            response = requests.post(f"{API_URL}/upload", files=files, timeout=60)
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    print("=== Upload de Dados Meteorológicos ===\n")
    
    # Verificar API
    if not check_api():
        print(f"❌ Erro: API não está respondendo em {API_URL}")
        print("   Certifique-se de que o FastAPI está rodando (docker-compose up)")
        sys.exit(1)
    
    print("✓ API está respondendo\n")
    
    # Encontrar todos os arquivos CSV
    csv_files = []
    for year_dir in sorted(DATA_DIR.glob("dados_*")):
        for csv_file in sorted(year_dir.glob("*.CSV")) + sorted(year_dir.glob("*.csv")):
            csv_files.append(csv_file)
    
    if not csv_files:
        print("❌ Nenhum arquivo CSV encontrado em data/dados_*/")
        sys.exit(1)
    
    print(f"Encontrados {len(csv_files)} arquivos CSV\n")
    
    # Fazer upload
    success_count = 0
    error_count = 0
    
    for csv_file in tqdm(csv_files, desc="Enviando arquivos"):
        result = upload_file(csv_file)
        
        if result.get("status") == "success":
            success_count += 1
        else:
            error_count += 1
            print(f"\n✗ Erro ao enviar {csv_file.name}: {result.get('message', 'Erro desconhecido')}")
    
    print(f"\n=== Upload concluído ===")
    print(f"Sucesso: {success_count}")
    print(f"Erros: {error_count}")
    print(f"Total: {len(csv_files)}")

if __name__ == "__main__":
    main()

