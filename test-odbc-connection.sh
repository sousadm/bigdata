#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    TESTE DE CONEXÃO ODBC COMPLETO     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Função para verificar se container está rodando
check_container() {
    if ! docker ps | grep -q $1; then
        echo -e "${RED}✗ Container $1 não está rodando!${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Container $1 está rodando${NC}"
    return 0
}

# Função para executar teste com feedback
run_test() {
    local test_name=$1
    local test_cmd=$2
    
    echo -e "\n${YELLOW}>>> $test_name${NC}"
    echo "----------------------------------------"
    
    if eval "$test_cmd"; then
        echo -e "${GREEN}✓ SUCESSO${NC}"
        return 0
    else
        echo -e "${RED}✗ FALHOU${NC}"
        return 1
    fi
}

# ==========================
# 1. VERIFICAR CONTAINERS
# ==========================
echo -e "\n${BLUE}[1] VERIFICANDO CONTAINERS${NC}"
echo "========================================="

check_container "clickhouse" || exit 1
check_container "sqlserver" || exit 1

# ==========================
# 2. VERIFICAR INSTALAÇÃO ODBC
# ==========================
echo -e "\n${BLUE}[2] VERIFICANDO INSTALAÇÃO ODBC${NC}"
echo "========================================="

run_test "Verificar biblioteca ODBC instalada" \
"docker exec clickhouse find /opt/microsoft -name 'libmsodbcsql*' -type f 2>/dev/null | grep -q ."

run_test "Verificar drivers ODBC registrados" \
"docker exec clickhouse odbcinst -q -d 2>/dev/null | grep -q 'ODBC Driver 18'"

run_test "Verificar DSN configurado" \
"docker exec clickhouse odbcinst -q -s 2>/dev/null | grep -q 'sqlserver_asprod'"

run_test "Verificar dependências da biblioteca" \
"docker exec clickhouse ldd /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1 2>/dev/null | grep -q 'not found' && exit 1 || exit 0"

# ==========================
# 3. VERIFICAR ARQUIVOS DE CONFIGURAÇÃO
# ==========================
echo -e "\n${BLUE}[3] VERIFICANDO CONFIGURAÇÕES${NC}"
echo "========================================="

run_test "Verificar /etc/odbcinst.ini" \
"docker exec clickhouse cat /etc/odbcinst.ini | grep -q 'ODBC Driver 18'"

run_test "Verificar /etc/odbc.ini" \
"docker exec clickhouse cat /etc/odbc.ini | grep -q 'sqlserver_asprod'"

echo -e "\n${YELLOW}Conteúdo do odbcinst.ini:${NC}"
docker exec clickhouse cat /etc/odbcinst.ini 2>/dev/null

echo -e "\n${YELLOW}Conteúdo do odbc.ini:${NC}"
docker exec clickhouse cat /etc/odbc.ini 2>/dev/null

# ==========================
# 4. VERIFICAR CONECTIVIDADE DE REDE
# ==========================
echo -e "\n${BLUE}[4] VERIFICANDO CONECTIVIDADE DE REDE${NC}"
echo "========================================="

run_test "Ping no SQL Server (rede)" \
"docker exec clickhouse ping -c 2 sqlserver 2>/dev/null | grep -q '0% packet loss'"

run_test "Verificar porta 1433 do SQL Server" \
"docker exec clickhouse nc -zv sqlserver 1433 2>&1 | grep -q 'succeeded'"

# ==========================
# 5. VERIFICAR SQL SERVER
# ==========================
echo -e "\n${BLUE}[5] VERIFICANDO SQL SERVER${NC}"
echo "========================================="

run_test "SQL Server aceita conexões" \
"docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '@Admin123' -Q 'SELECT 1' 2>/dev/null | grep -q '1 rows affected'"

# ==========================
# 6. TESTE ODBC COM ISQL
# ==========================
echo -e "\n${BLUE}[6] TESTE DE CONEXÃO COM ISQL${NC}"
echo "========================================="

echo -e "${YELLOW}Tentando conectar com isql...${NC}"
docker exec clickhouse isql -v sqlserver_asprod sa '@Admin123' <<EOF 2>&1
SELECT 1 as teste;
quit
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Conexão ISQL bem-sucedida${NC}"
else
    echo -e "${RED}✗ Conexão ISQL falhou${NC}"
fi

# ==========================
# 7. TESTE CLICKHOUSE ODBC
# ==========================
echo -e "\n${BLUE}[7] TESTE DE CONEXÃO CLICKHOUSE + ODBC${NC}"
echo "========================================="

echo -e "${YELLOW}Teste 1: Consulta simples via ODBC${NC}"
docker exec clickhouse clickhouse-client --user admin --password admin123 --query \
"SELECT * FROM odbc('DSN=sqlserver_asprod', 'SELECT 1 as numero, ''teste'' as texto')" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Consulta ODBC simples funcionou${NC}"
else
    echo -e "${RED}✗ Consulta ODBC simples falhou${NC}"
fi

echo -e "\n${YELLOW}Teste 2: Listando databases do SQL Server${NC}"
docker exec clickhouse clickhouse-client --user admin --password admin123 --query \
"SELECT * FROM odbc('DSN=sqlserver_asprod', 'SELECT name FROM sys.databases')" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Listagem de databases funcionou${NC}"
else
    echo -e "${RED}✗ Listagem de databases falhou${NC}"
fi

# ==========================
# 8. LOGS E DIAGNÓSTICO
# ==========================
echo -e "\n${BLUE}[8] LOGS DE DIAGNÓSTICO${NC}"
echo "========================================="

echo -e "\n${YELLOW}Últimas 30 linhas do log do ClickHouse:${NC}"
docker logs clickhouse --tail 30 2>&1 | tail -30

echo -e "\n${YELLOW}Últimas 20 linhas do log do SQL Server:${NC}"
docker logs sqlserver --tail 20 2>&1 | tail -20

# ==========================
# 9. RESUMO FINAL
# ==========================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}           RESUMO DO TESTE              ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Contador de sucessos
SUCCESS_COUNT=0
TOTAL_TESTS=10

# Verificar cada componente novamente rapidamente
docker exec clickhouse find /opt/microsoft -name 'libmsodbcsql*' -type f &>/dev/null && ((SUCCESS_COUNT++))
docker exec clickhouse odbcinst -q -d 2>/dev/null | grep -q 'ODBC Driver 18' && ((SUCCESS_COUNT++))
docker exec clickhouse odbcinst -q -s 2>/dev/null | grep -q 'sqlserver_asprod' && ((SUCCESS_COUNT++))
docker exec clickhouse ping -c 1 sqlserver &>/dev/null && ((SUCCESS_COUNT++))
docker exec clickhouse nc -zv sqlserver 1433 2>&1 | grep -q 'succeeded' && ((SUCCESS_COUNT++))

echo -e "Testes básicos: ${GREEN}$SUCCESS_COUNT/$TOTAL_TESTS${NC} passaram"
echo ""

if [ $SUCCESS_COUNT -ge 8 ]; then
    echo -e "${GREEN}✓✓✓ CONFIGURAÇÃO PARECE BOA ✓✓✓${NC}"
    echo "Você pode tentar criar tabelas externas agora!"
else
    echo -e "${RED}✗✗✗ EXISTEM PROBLEMAS NA CONFIGURAÇÃO ✗✗✗${NC}"
    echo "Revise os logs acima para identificar o problema."
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo "Teste concluído em: $(date)"
echo -e "${BLUE}========================================${NC}"
