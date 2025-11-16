#!/bin/bash

echo "=== Limpeza completa do Docker ==="

# Parar todos os containers
echo "1. Parando containers..."
docker-compose down -v

# Remover containers parados
echo "2. Removendo containers parados..."
docker container prune -f

# Remover imagens não utilizadas
echo "3. Removendo imagens não utilizadas..."
docker image prune -a -f

# Remover build cache
echo "4. Limpando build cache..."
docker builder prune -a -f

# Remover volumes órfãos (opcional - cuidado com dados)
echo "5. Removendo volumes órfãos..."
docker volume prune -f

# Verificar espaço em disco
echo "6. Espaço em disco disponível:"
df -h /var/lib/docker

echo ""
echo "=== Limpeza concluída ==="
echo "Execute agora: ./check-odbc.sh"
