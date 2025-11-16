#!/bin/bash

echo "=== Limpando sistema Docker para resolver 'max depth exceeded' ==="

# 1. Parar todos os containers
echo "1. Parando todos os containers..."
docker-compose down -v
docker stop $(docker ps -aq) 2>/dev/null || true

# 2. Remover containers órfãos
echo "2. Removendo containers..."
docker container prune -f

# 3. Remover imagens não utilizadas (incluindo dangling)
echo "3. Removendo imagens dangling..."
docker image prune -a -f

# 4. Limpar cache de build
echo "4. Limpando cache de build..."
docker builder prune -a -f

# 5. Limpar volumes não utilizados
echo "5. Limpando volumes não utilizados..."
docker volume prune -f

# 6. Remover redes órfãs
echo "6. Removendo redes não utilizadas..."
docker network prune -f

# 7. Limpeza completa do sistema
echo "7. Limpeza completa do sistema Docker..."
docker system prune -a -f --volumes

echo ""
echo "=== Verificando espaço em disco ==="
df -h | grep -E 'Filesystem|/$'

echo ""
echo "=== Status do Docker ==="
docker info | grep -A 5 "Storage Driver"

echo ""
echo "=== Reconstruindo ClickHouse ==="
docker-compose build --no-cache --pull clickhouse

echo ""
echo "=== Iniciando serviços ==="
docker-compose up -d clickhouse sqlserver

echo ""
echo "=== Aguardando inicialização (60s) ==="
sleep 60

echo ""
echo "=== Verificando containers ==="
docker ps -a

echo ""
echo "=== Logs do ClickHouse (últimas 20 linhas) ==="
docker logs clickhouse --tail 20 2>&1 || echo "Container não está rodando"

echo ""
echo "=== Teste concluído ==="
