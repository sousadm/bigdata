1. Primeiro, verifique os logs para identificar o problema:
bash
# Salvar logs do Kafka Connect para análise
docker-compose logs kafka-connect > kafka-connect-error.log

# Ver o conteúdo do log
cat kafka-connect-error.log | tail -50


2. Parar e remover apenas os serviços problemáticos:
bash
# Parar e remover serviços Kafka e logs (mantendo bancos)
docker-compose stop kafka kafka-connect kafka-rest-proxy kafka-ui zookeeper
docker-compose rm -f kafka kafka-connect kafka-rest-proxy kafka-ui zookeeper
docker-compose logs -f kafka kafka-connect kafka-rest-proxy kafka-ui zookeeper



### Recriar os tópicos internos ######################
#   Quando houver instabilidade do kafka-connect     #
######################################################
1. Parar o kafka-connect
docker-compose stop kafka-connect

2. Entrar no container do Kafka
docker exec -it kafka bash

3. Deletar os tópicos internos antigos
kafka-topics --bootstrap-server localhost:9092 --delete --topic docker-connect-offsets
kafka-topics --bootstrap-server localhost:9092 --delete --topic docker-connect-configs
kafka-topics --bootstrap-server localhost:9092 --delete --topic docker-connect-status

# Sair do container
4. exit
