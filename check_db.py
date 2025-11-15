import psycopg2
import csv
import os
import re
from datetime import datetime

# ============================================
# Configuración de conexión
# ============================================
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "corrupcion_db"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD", "td8corrupcion"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5433"),
}

def conectar_db():
    return psycopg2.connect(**DB_CONFIG)

conn = conectar_db()
cur = conn.cursor()

# Ver cuántos registros hay
cur.execute("SELECT COUNT(*) FROM tribunal_juez")
total = cur.fetchone()[0]
print(f"Total de registros en tribunal_juez: {total}")