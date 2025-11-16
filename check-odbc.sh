#!/bin/bash

echo "=== Reconstruindo ClickHouse com ODBC ==="

# Parar serviços
docker-compose down

# Reconstruir ClickHouse
docker-compose build --no-cache clickhouse

# Iniciar serviços
docker-compose up -d clickhouse sqlserver

echo "Aguardando inicialização..."
sleep 30

echo "=== Verificando instalação ODBC no container ==="
docker exec clickhouse bash -c "
echo '1. Bibliotecas ODBC:'
find /opt/microsoft -name 'libmsodbcsql*' -type f 2>/dev/null

echo '2. Verificando dependências da biblioteca:'
ldd /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1 || echo 'Biblioteca não encontrada'

echo '3. Drivers ODBC:'
odbcinst -q -d

echo '4. DSNs:'
odbcinst -q -s

echo '5. Conteúdo dos arquivos de configuração:'
echo '=== odbc.ini ==='
cat /etc/odbc.ini
echo '=== odbcinst.ini ==='
cat /etc/odbcinst.ini
"

echo "=== Testando conectividade com SQL Server ==="
docker exec clickhouse bash -c "
echo 'Testando conexão de rede para sqlserver:1433...'
nc -zv sqlserver 1433 && echo 'Conexão OK' || echo 'Conexão FALHOU'
"

echo "=== Testando conexão ODBC com isql ==="
docker exec clickhouse bash -c "
    echo 'Teste com DSN:'
    isql -v sqlserver_asprod sa '@Admin123' -b
" || echo "Teste isql falhou"

echo "=== Testando conexão no ClickHouse ==="
docker exec clickhouse clickhouse-client --user admin --password admin123 -q "
SELECT 'Teste ODBC' as status
FROM odbc('DSN=sqlserver_asprod', 'SELECT 1 as teste')
" 2>/dev/null && echo "SUCESSO: Conexão ODBC funcionando!" || echo "ERRO: Falha na conexão ODBC"

echo "=== Teste concluído ==="
