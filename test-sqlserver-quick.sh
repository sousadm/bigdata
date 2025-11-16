#!/bin/bash

echo "=== TESTE RÁPIDO SQL SERVER ==="

# Parar e remover container existente
docker-compose down sqlserver
docker rm -f sqlserver 2>/dev/null

# Reconstruir com a nova configuração
echo "Construindo nova imagem..."
docker-compose build sqlserver

# Iniciar
echo "Iniciando SQL Server..."
docker-compose up -d sqlserver

# Aguardar
echo "Aguardando inicialização..."
sleep 30

# Testar
echo "Testando conexão..."
docker exec sqlserver bash -c "
if [ -f '/opt/mssql-tools18/bin/sqlcmd' ]; then
    echo '✅ sqlcmd encontrado'
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P '@Admin123' -Q 'SELECT @@VERSION' && echo '✅ SQL Server funcionando'
else
    echo '❌ sqlcmd não encontrado'
    # Tentar encontrar onde está
    find / -name 'sqlcmd' -type f 2>/dev/null
fi
"

echo "=== TESTE CONCLUÍDO ==="
