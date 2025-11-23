#!/usr/bin/env python3
import pyodbc
import json

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=ASERP;'
    'UID=sa;'
    'PWD=Admin.Server.2025;'
)

cursor = conn.cursor()
cursor.execute("SELECT id_cfop, natureza FROM dbo.cfop")

for row in cursor:
    print(json.dumps({
        'id_cfop': row[0],
        'natureza': row[1]
    }))

cursor.close()
conn.close()
