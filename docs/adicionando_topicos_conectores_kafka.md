### TESTANDO O AMBIENTE KAFKA ##########

# Verificar IP do cluster
docker inspect clickhouse | grep IPAddress

✅ 3. Criar tabela no ClickHouse
CREATE TABLE default.dim_produto
(
    id UInt32,
    descricao String,
    unidade String,
    custo Decimal(10,4),
    data_carga DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(data_carga)
ORDER BY id;


✅ 🚀 Criar CONNECTOR (CONSUMER) e submeter
# Se estiver na mesma pasta do arquivo
curl -X POST -H "Content-Type: application/json" --data @produto-clickhouse-sink.json http://localhost:8083/connectors
curl -X POST -H "Content-Type: application/json" --data @produto-mongodb-sink-v2.json http://localhost:8083/connectors

✅ 1. Criar o tópico (SEM ESTAR dentro do container primeiro)	

docker exec -it kafka bash
kafka-topics --bootstrap-server kafka:9092 --create --topic dim-produto --partitions 1 --replication-factor 1
kafka-topics --bootstrap-server kafka:9092 --create --topic mongo-produto --partitions 1 --replication-factor 1

kafka-topics --bootstrap-server kafka:9092 --list

✅ 2. Testar envio de mensagem (producer) Ainda dentro do container:

docker exec -it kafka bash
kafka-console-producer --broker-list kafka:9092 --topic dim_produto --property parse.key=true --property key.separator=":"
100:{"id":100,"descricao":"teste","unidade":"UN","custo":5.32}

# Fora do container
kafka-console-producer --broker-list kafka:29092 --topic <conector_name> --property parse.key=true --property key.separator=":"

kafka-console-producer --broker-list kafka:9092 --topic dim_produto

✅ 4. Testar autenticação do ClickHouse (com o usuário do connector)
curl -u admin:admin123 "http://clickhouse:8123/?query=SELECT%201"


✅ 6. Validar o connector
curl http://localhost:8083/connectors/dim-produto-sink/status

📥 Consumindo Mensagens (Consumer)
kafka-console-consumer --bootstrap-server kafka:29092 --topic dim_produto --from-beginning


🗑️ APAGAR TODOS OS CONECTORES
for c in $(curl -s http://localhost:8083/connectors | jq -r '.[]'); do
  echo "Removendo conector: $c"
  curl -X DELETE http://localhost:8083/connectors/$c
done

curl http://localhost:8083/connectors


🗑️ APAGAR TODOS OS TÓPICOS
docker exec -it kafka bash

for t in $(kafka-topics --bootstrap-server kafka:9092 --list); do
  echo "Apagando tópico: $t"
  kafka-topics --bootstrap-server kafka:9092 --delete --topic "$t"
done

kafka-topics --bootstrap-server kafka:9092 --list


##############################################################
####### 🔑 Preparar a Tabela no ClickHouse     ###############
##############################################################
1. 🔑 Preparar a Tabela no ClickHouse
docker exec -it clickhouse clickhouse-client

CREATE TABLE IF NOT EXISTS default.kafka_test_table (
    id UInt64,
    mensagem String
) ENGINE = MergeTree()
ORDER BY id;

\q

3. Testar se o Kafka Connect consegue acessar o ClickHouse
docker exec -it kafka-connect curl http://clickhouse:8123/

# caminho relativo
curl -X POST -H "Content-Type: application/json" --data @./config/produto-connector.json http://localhost:8083/connectors

# caminho absoluto
curl -X POST -H "Content-Type: application/json" --data @/home/sousa/bigdata/connect/produto-connector.json http://localhost:8083/connectors

# ATUALIZAR o connector
curl -X PUT -H "Content-Type: application/json" --data @produto-connector.json http://localhost:8083/connectors/dim-produto-sink/config

4. Verificar status
curl http://localhost:8083/connectors/clickhouse-sink-connector/status | jq

5. Se houver erro, ver logs
docker logs kafka-connect --tail 100





