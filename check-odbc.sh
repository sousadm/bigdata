#!/bin/bash

echo "=== Reconstruindo ClickHouse com ODBC ==="

# Parar serviços
docker-compose down

# Reconstruir ClickHouse (agora com o odbcinst.ini corrigido)
docker-compose build --no-cache clickhouse

# Iniciar serviços
docker-compose up -d clickhouse sqlserver

echo "Aguardando inicialização..."
sleep 90

echo "=== Verificando instalação ODBC no container ==="
docker exec clickhouse bash -c "
echo '1. Bibliotecas ODBC:'
find /opt/microsoft -name 'libmsodbcsql*' -type f

echo '2. Drivers ODBC:'
odbcinst -q -d

echo '3. DSNs:'
odbcinst -q -s

echo '4. Testando biblioteca (ldd deve funcionar agora):'
ldd /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1 || echo 'Erro ao carregar biblioteca'
"

echo "=== Testando conexão ODBC com isql (Diagnóstico) ==="
# isql -v <DSN> <user> <password>
docker exec clickhouse bash -c "
    isql -v sqlserver_asprod sa @dmin123
" || echo "Erro no teste isql"

echo "=== Testando conexão no ClickHouse (Teste Final) ==="
docker exec clickhouse clickhouse-client --user admin --password admin123 -q "
SELECT 'Teste ODBC' as status
FROM odbc('DSN=sqlserver_asprod', 'SELECT 1 as teste')
" 2>/dev/null || echo "Erro no teste ODBC"

echo "=== Teste concluído ==="

