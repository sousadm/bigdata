#!/bin/bash

echo "=========================================="
echo "  DIAGNÓSTICO SQL SERVER"
echo "=========================================="

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "1️⃣  Status do Container SQL Server"
echo "-------------------------------------------"
docker ps --filter "name=sqlserver" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "2️⃣  Logs do SQL Server (últimas 30 linhas)"
echo "-------------------------------------------"
docker logs sqlserver --tail 30

echo ""
echo "3️⃣  Procurando por mensagens importantes..."
echo "-------------------------------------------"

# Verificar se está pronto
if docker logs sqlserver 2>&1 | grep -q "SQL Server is now ready for client connections"; then
    echo -e "${GREEN}✓ SQL Server está PRONTO para conexões${NC}"
    READY=true
else
    echo -e "${RED}✗ SQL Server NÃO está pronto (ainda inicializando?)${NC}"
    READY=false
fi

# Verificar erros comuns
if docker logs sqlserver 2>&1 | grep -qi "error"; then
    echo -e "${YELLOW}⚠ Erros encontrados nos logs:${NC}"
    docker logs sqlserver 2>&1 | grep -i "error" | tail -n 5
fi

# Verificar problemas de senha
if docker logs sqlserver 2>&1 | grep -qi "password"; then
    echo -e "${YELLOW}⚠ Mensagens sobre senha:${NC}"
    docker logs sqlserver 2>&1 | grep -i "password" | tail -n 5
fi

echo ""
echo "4️⃣  Verificando processos SQL Server"
echo "-------------------------------------------"
docker exec sqlserver bash -c "ps aux | grep sqlservr | grep -v grep" 2>/dev/null || echo "Processo não encontrado ou container sem bash"

echo ""
echo "5️⃣  Verificando portas abertas"
echo "-------------------------------------------"
echo "Portas escutando no SQL Server:"
docker exec sqlserver bash -c "netstat -tuln 2>/dev/null | grep LISTEN" 2>/dev/null || \
docker exec sqlserver bash -c "ss -tuln 2>/dev/null | grep LISTEN" 2>/dev/null || \
echo "Não foi possível verificar portas (netstat/ss não disponível)"

echo ""
if docker exec sqlserver bash -c "netstat -tuln 2>/dev/null | grep 1433" > /dev/null 2>&1 || \
   docker exec sqlserver bash -c "ss -tuln 2>/dev/null | grep 1433" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Porta 1433 está ABERTA${NC}"
else
    echo -e "${RED}✗ Porta 1433 NÃO está aberta${NC}"
fi

echo ""
echo "6️⃣  Testando conexão de rede do ClickHouse"
echo "-------------------------------------------"

# Teste de ping
echo -n "Ping: "
if docker exec clickhouse ping -c 1 sqlserver > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALHOU${NC}"
fi

# Teste de DNS
echo -n "DNS: "
if docker exec clickhouse getent hosts sqlserver > /dev/null 2>&1; then
    SQLSERVER_IP=$(docker exec clickhouse getent hosts sqlserver | awk '{print $1}')
    echo -e "${GREEN}OK${NC} (IP: $SQLSERVER_IP)"
else
    echo -e "${RED}FALHOU${NC}"
fi

# Teste de porta TCP
echo -n "Porta 1433 (TCP): "
if docker exec clickhouse bash -c "timeout 3 bash -c 'cat < /dev/null > /dev/tcp/sqlserver/1433'" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FALHOU${NC}"
fi

echo ""
echo "7️⃣  Tentando conectar com sqlcmd"
echo "-------------------------------------------"

if [ "$READY" = true ]; then
    echo "SQL Server está pronto, testando conexão..."
    
    # Teste simples
    echo ""
    echo "Teste 1: SELECT 1"
    docker exec clickhouse sqlcmd -S sqlserver -U sa -P '@Admin123' -C -Q "SELECT 1 AS Teste" 2>&1
    RESULT=$?
    
    if [ $RESULT -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓✓✓ SUCESSO! SQL Server conectado via sqlcmd ✓✓✓${NC}"
        
        echo ""
        echo "Teste 2: Listar databases"
        docker exec clickhouse sqlcmd -S sqlserver -U sa -P '@Admin123' -C -Q "SELECT name FROM sys.databases" 2>&1
        
    else
        echo ""
        echo -e "${RED}✗ Falha na conexão mesmo com SQL Server pronto${NC}"
        echo ""
        echo "Possíveis causas:"
        echo "  1. Senha incorreta (verifique se é '@Admin123')"
        echo "  2. Problema no driver ODBC"
        echo "  3. SQL Server está reiniciando"
    fi
else
    echo -e "${YELLOW}SQL Server ainda não está pronto. Aguardando...${NC}"
    echo ""
    echo "Tentando conectar mesmo assim (pode falhar):"
    docker exec clickhouse sqlcmd -S sqlserver -U sa -P '@Admin123' -C -Q "SELECT 1 AS Teste" 2>&1 || true
    
    echo ""
    echo -e "${BLUE}Recomendação:${NC}"
    echo "  Aguarde 30-60 segundos e execute novamente:"
    echo "  sleep 30 && ./check-sqlserver.sh"
fi

echo ""
echo "8️⃣  Informações do SQL Server"
echo "-------------------------------------------"
echo "Variáveis de ambiente:"
docker exec sqlserver bash -c "env | grep -E 'MSSQL|ACCEPT_EULA'" 2>/dev/null || echo "Não foi possível obter variáveis"

echo ""
echo "=========================================="
echo "           DIAGNÓSTICO COMPLETO"
echo "=========================================="

if [ "$READY" = true ]; then
    echo ""
    echo -e "${GREEN}✓ SQL Server está pronto${NC}"
    echo ""
    echo "Se a conexão ainda falha, tente:"
    echo ""
    echo "1. Reiniciar SQL Server:"
    echo "   docker-compose restart sqlserver"
    echo ""
    echo "2. Ver logs em tempo real:"
    echo "   docker logs -f sqlserver"
    echo ""
    echo "3. Conectar manualmente:"
    echo "   docker exec -it clickhouse bash"
    echo "   sqlcmd -S sqlserver -U sa -P '@Admin123' -C"
else
    echo ""
    echo -e "${YELLOW}⏳ SQL Server ainda está inicializando${NC}"
    echo ""
    echo "Aguarde alguns minutos. O SQL Server pode demorar para iniciar completamente."
    echo ""
    echo "Execute este comando para acompanhar:"
    echo "   docker logs -f sqlserver"
    echo ""
    echo "Quando aparecer 'SQL Server is now ready for client connections', execute novamente:"
    echo "   ./check-sqlserver.sh"
fi

echo "=========================================="
