1. Primeiro, verifique os logs para identificar o problema:
bash
# Salvar logs do Kafka Connect para análise
docker-compose logs kafka-connect > kafka-connect-error.log

# Ver o conteúdo do log
cat kafka-connect-error.log | tail -50


2. Parar e remover apenas os serviços problemáticos:
bash
# Parar e remover serviços Kafka (mantendo bancos)
docker-compose stop kafka kafka-connect kafka-rest-proxy kafka-ui zookeeper

docker-compose rm -f kafka kafka-connect kafka-rest-proxy kafka-ui zookeeper
