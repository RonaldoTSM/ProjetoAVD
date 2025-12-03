#!/usr/bin/env python3
"""
Script para testar conexão com PostgreSQL
Execute no JupyterLab ou localmente
"""
import os
from sqlalchemy import create_engine, text
import pandas as pd

# Configuração PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "weather_db")

# URL de conexão
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

print("=== Teste de Conexão PostgreSQL ===\n")
print(f"Host: {POSTGRES_HOST}")
print(f"Database: {POSTGRES_DB}")
print(f"User: {POSTGRES_USER}")
print(f"URL: postgresql://{POSTGRES_USER}:***@{POSTGRES_HOST}:5432/{POSTGRES_DB}\n")

try:
    # Criar engine
    engine = create_engine(DATABASE_URL)
    print("✓ Engine SQLAlchemy criado")
    
    # Testar conexão
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✓ Conexão estabelecida!")
        print(f"  PostgreSQL Version: {version[:50]}...\n")
        
        # Verificar tabelas
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"✓ Tabelas encontradas: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
        
        # Verificar dados
        if 'weather_hourly' in tables:
            result = conn.execute(text("SELECT COUNT(*) FROM weather_hourly;"))
            count = result.fetchone()[0]
            print(f"\n✓ Registros em weather_hourly: {count:,}")
            
            if count > 0:
                result = conn.execute(text("""
                    SELECT cidade, COUNT(*) as registros 
                    FROM weather_hourly 
                    GROUP BY cidade 
                    ORDER BY registros DESC 
                    LIMIT 5;
                """))
                print("\n  Top 5 cidades por registros:")
                for row in result.fetchall():
                    print(f"    - {row[0]}: {row[1]:,} registros")
        
        if 'weather_daily' in tables:
            result = conn.execute(text("SELECT COUNT(*) FROM weather_daily;"))
            count = result.fetchone()[0]
            print(f"\n✓ Registros em weather_daily: {count:,}")
    
    print("\n Conexão PostgreSQL funcionando perfeitamente!")
    
except Exception as e:
    print(f"\n Erro ao conectar: {str(e)}")
    print("\nPossíveis causas:")
    print("  1. PostgreSQL não está rodando")
    print("  2. Credenciais incorretas")
    print("  3. Database não existe")
    print("  4. Problema de rede entre containers")

