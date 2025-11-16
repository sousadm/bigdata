#!/bin/bash

echo "=========================================="
echo "  CORRIGINDO PROBLEMA DE REDE"
echo "=========================================="

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "🔍 Verificando problema..."

# Verificar se containers estão na mesma rede
CH_NETWORKS=$(docker inspect clickhouse --format='{{range $net,$v := .NetworkSettings.Networks}}{{$net}} {{end}}' 2>/dev/null)
SQL_NETWORKS=$(docker inspect sqlserver --format='{{range $net,$v := .NetworkSettings.Networks}}{{$net}} {{end}}' 2>/dev/null)

echo "Redes do ClickHouse: $CH_NETWORKS"
echo "Redes do SQL Server: $SQL_NETWORKS"

# Verificar rede comum
COMMON_NET=""
for net in $CH_NETWORKS; do
    if echo "$SQL_NETWORKS" | grep -q "$net"; then
        COMMON_NET="$net"
        break
    fi
done

if [ ! -z "$COMMON_NET" ]; then
    echo -e "${GREEN}✓ Containers já estão na mesma rede: $COMMON_NET${NC}"
    echo "O problema pode ser outro. Verifique:"
    echo "  1. Se o SQL Server está realmente iniciado"
    echo "  2. Os logs do SQL Server: docker logs sqlserver"
    exit 0
fi

echo -e "${YELLOW}⚠ Containers NÃO estão na mesma rede${NC}"
echo ""
echo "📋 OPÇÕES DE CORREÇÃO:"
echo ""
echo "1️⃣  Conectar ClickHouse à rede do SQL Server"
echo "2️⃣  Recriar tudo usando docker-compose corrigido"
echo "3️⃣  Cancelar"
echo ""
read -p "Escolha uma opção (1, 2 ou 3): " opcao

case $opcao in
    1)
        echo ""
        echo "🔧 Conectando ClickHouse à rede bigdata_bigdata-net..."
        
        # Verificar se a rede existe
        if docker network inspect bigdata_bigdata-net > /dev/null 2>&1; then
            docker network connect bigdata_bigdata-net clickhouse
            echo -e "${GREEN}✓ ClickHouse conectado à rede bigdata_bigdata-net${NC}"
            
            echo ""
            echo "🧪 Testando conexão..."
            sleep 2
            docker exec clickhouse bash -c "nc -zv sqlserver 1433" 2>&1
            
            echo ""
            echo "Teste sqlcmd:"
            docker exec clickhouse sqlcmd -S sqlserver -U sa -P '@Admin123' -C -Q "SELECT 1 AS Teste"
        else
            echo -e "${RED}✗ Rede bigdata_bigdata-net não existe${NC}"
            echo "Use a opção 2 para recriar tudo corretamente"
        fi
        ;;
        
    2)
        echo ""
        echo "🔄 Recriando ambiente completo..."
        echo ""
        
        # Parar todos os containers
        echo "Parando containers..."
        docker-compose down
        
        # Remover redes antigas
        echo "Limpando redes antigas..."
        docker network prune -f
        
        # Subir novamente
        echo "Iniciando containers..."
        docker-compose up -d clickhouse sqlserver
        
        echo ""
        echo "⏳ Aguardando inicialização (30 segundos)..."
        sleep 30
        
        echo ""
        echo "🧪 Testando conectividade..."
        docker exec clickhouse bash -c "nc -zv sqlserver 1433" 2>&1
        
        echo ""
        echo "Teste sqlcmd:"
        docker exec clickhouse sqlcmd -S sqlserver -U sa -P '@Admin123' -C -Q "SELECT 1 AS Teste"
        
        echo ""
        echo -e "${GREEN}✓ Ambiente recriado${NC}"
        ;;
        
    3)
        echo "Cancelado."
        exit 0
        ;;
        
    *)
        echo -e "${RED}Opção inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "           CORREÇÃO CONCLUÍDA"
echo "=========================================="
echo ""
echo "📝 Próximos passos:"
echo "   1. Execute: ./diagnose-network.sh (para confirmar)"
echo "   2. Execute: ./test-sqlserver-connections.sh (para testar)"
echo ""
