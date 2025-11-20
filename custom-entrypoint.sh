#!/bin/bash
set -e

# Função para iniciar o ODBC Bridge
start_odbc_bridge() {
    echo "Aguardando ClickHouse Server iniciar..."
    sleep 15
    
    echo "Iniciando ODBC Bridge..."
    /usr/bin/clickhouse odbc-bridge \
        --http-port 9018 \
        --listen-host 0.0.0.0 \
        --log-level trace \
        --daemon \
        --pid-file /var/run/clickhouse-odbc-bridge.pid
    
    echo "ODBC Bridge iniciado com PID: $(cat /var/run/clickhouse-odbc-bridge.pid 2>/dev/null || echo 'N/A')"
}

# Iniciar o ODBC Bridge em background
start_odbc_bridge &

# Executar o entrypoint original do ClickHouse
exec /entrypoint.sh "$@"
