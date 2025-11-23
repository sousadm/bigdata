🔶 Parte 1 — Conector Kafka → ClickHouse com UPSERT

Este conector faz UPSERT usando o campo codigo como chave.
✔ Compatível com ClickHouse MergeTree usando ReplacingMergeTree (recomendado para dimensões)
#####  Fluxo Final do Pipeline (Profissional)   #################################
#     SQL Server → ETL Python → Kafka → Sink ClickHouse → Tabela Dimensão       #
#################################################################################
1. Dimensão Para suportar UPSERT:

CREATE TABLE default.dim_produto
(
    codigo UInt32,
    descricao String,
    unidade String,
    custo Decimal(10,4),
    data_carga DateTime DEFAULT now(),
    _version UInt64 DEFAULT toUnixTimestamp(now())
)
ENGINE = ReplacingMergeTree(_version)
PARTITION BY toYYYYMM(data_carga)
ORDER BY codigo;

2. Conector Kafka Connect para UPSERT
# A mensagem Kafka deve conter key = código
# Se o produto já existir → atualiza
# Se não existir → insere
{
    "name": "dim-produto-sink",
    "config": {
        "connector.class": "com.clickhouse.kafka.connect.ClickHouseSinkConnector",
        "tasks.max": "1",

        "topics": "dim_produto_topic",

        "hostname": "clickhouse",
        "port": "8123",
        "database": "default",
        "table": "dim_produto",

        "username": "admin",
        "password": "admin123",

        "ssl": "false",

        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable": "false",
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "key.converter.schemas.enable": "false",

        "errors.tolerance": "all",
        "errors.log.enable": "true",

        "insert.mode": "upsert",

        "pk.mode": "record_key",
        "primary.key": "codigo",

        "delete.enabled": "false",

        "clickhouse.settings": "date_time_input_format=best_effort"
    }
}


3. — ETL Python SQL Server → Kafka
# Lê SQL Server
# Executa sua consulta
# Envia cada registro para Kafka
# Define key = código para permitir UPSERT

import pyodbc
from kafka import KafkaProducer
import json

# Conexão SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=SEU_SERVIDOR;"
    "DATABASE=ASPROD;"
    "UID=usuario;"
    "PWD=senha;"
)

cursor = conn.cursor()

query = """
SELECT 
    s.Sku AS codigo,
    p.descricao_fiscal + ' ' + ISNULL(c.descricao_fiscal, '') + ' ' + ISNULL(s.Tamanho, '') AS descricao,
    u.Sigla AS unidade,
    s.Custo AS custo
FROM ASPROD.dbo.Skus s 
INNER JOIN ASPROD.dbo.Produtos p ON p.Produto = s.Produto 
LEFT JOIN ASPROD.dbo.Cores c ON c.Cor = s.Cor
LEFT JOIN ASPROD.dbo.Unidades u ON u.Unidade = s.Unidade;
"""

cursor.execute(query)

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: json.dumps(k).encode("utf-8")
)

topic = "dim_produto_topic"

for row in cursor.fetchall():
    data = {
        "codigo": row.codigo,
        "descricao": row.descricao,
        "unidade": row.unidade,
        "custo": float(row.custo)
    }

    # key definida para permitir UPSERT
    key = {"codigo": row.codigo}

    producer.send(topic, key=key, value=data)

producer.flush()
cursor.close()
conn.close()

print("Carga concluída.")


