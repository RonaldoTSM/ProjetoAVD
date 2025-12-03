#!/usr/bin/env python3
"""
Script simplificado para fazer upload de todos os arquivos CSV para o MinIO via FastAPI
Versão sem dependências extras (sem tqdm)
"""
import os
import sys
import requests
from pathlib import Path

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
        print(f"Erro: API nao esta respondendo em {API_URL}")
        print("   Certifique-se de que o FastAPI esta rodando (docker-compose up)")
        sys.exit(1)
    
    print("API esta respondendo\n")
    
    # Encontrar todos os arquivos CSV
    csv_files = []
    for year_dir in sorted(DATA_DIR.glob("dados_*")):
        for csv_file in sorted(year_dir.glob("*.CSV")) + sorted(year_dir.glob("*.csv")):
            csv_files.append(csv_file)
    
    if not csv_files:
        print("Nenhum arquivo CSV encontrado em data/dados_*/")
        sys.exit(1)
    
    print(f"Encontrados {len(csv_files)} arquivos CSV\n")
    
    # Fazer upload
    success_count = 0
    error_count = 0
    
    for i, csv_file in enumerate(csv_files, 1):
        print(f"[{i}/{len(csv_files)}] Enviando {csv_file.name}...", end=" ")
        result = upload_file(csv_file)
        
        if result.get("status") == "success":
            success_count += 1
            print("Sucesso")
        else:
            error_count += 1
            print(f"Erro: {result.get('message', 'Erro desconhecido')}")
    
    print(f"\n=== Upload concluido ===")
    print(f"Sucesso: {success_count}")
    print(f"Erros: {error_count}")
    print(f"Total: {len(csv_files)}")
    
    if success_count > 0:
        print(f"\n{success_count} arquivo(s) enviado(s) com sucesso!")
        print("   Verifique no MinIO: http://localhost:9091 (bucket raw/)")

if __name__ == "__main__":
    main()

