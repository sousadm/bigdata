import pyodbc
from clickhouse_driver import Client
import pandas as pd
import logging
from datetime import datetime
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_vendas.log'), 
        logging.StreamHandler(sys.stdout)
    ]
)

class SQLServerConnector:
    def __init__(self, server="localhost", database="ASPROD", user="sa", password="Admin.Server.2025"):
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};"
            f"UID={user};PWD={password};TrustServerCertificate=yes;"
        )
        self.conn = None

    def connect(self):
        try:
            self.conn = pyodbc.connect(self.connection_string)
            logging.info("Conexão com SQL Server estabelecida")
            return True
        except Exception as e:
            logging.error(f"Erro ao conectar ao SQL Server: {e}")
            return False

    def disconnect(self):
        if self.conn:
            self.conn.close()


class ClickHouseConnector:
    def __init__(self, host="localhost", port=9000, user="admin", password="admin123", database="default"):
        self.client = None
        self.config = dict(host=host, port=port, user=user, password=password, database=database)

    def connect(self):
        try:
            self.client = Client(**self.config)
            logging.info("Conexão com ClickHouse estabelecida")
            return True
        except Exception as e:
            logging.error(f"Erro ao conectar ao ClickHouse: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.disconnect()


class ETLProductor: 
    BATCH_SIZE = 50000 
    def __init__(self):
        self.sql = SQLServerConnector()
        self.ch = ClickHouseConnector()

    def create_table(self):
        query = """
          CREATE TABLE default.fato_vendas
          (
              `id_venda` UInt64,
              `numero_item` UInt16, 
              `fk_id_cliente` UInt32,
              `fk_id_produto` UInt32,
              `fk_tempo_id` UInt32,
              `quantidade_vendida` Decimal(10, 4),
              `valor_unitario` Decimal(10, 4),
              `valor_desconto` Decimal(10, 4),
              `valor_liquido` Decimal(10, 4),
              `data_venda`DateTime,
              `data_carga` DateTime DEFAULT now()
          )
          ENGINE = SummingMergeTree
          PARTITION BY toYYYYMM(data_venda)
          ORDER BY (fk_tempo_id, fk_id_cliente, fk_id_produto, id_venda, numero_item);
        """
        try:
            self.ch.client.execute(query)
            logging.info("Tabela 'fato_vendas' criada/verificada")
        except Exception as e:
            logging.error(f"Erro ao criar tabela: {e}")
            raise

    def extract_batch(self, batch_size=None):
        if batch_size is None:
            batch_size = self.BATCH_SIZE

        try:
            count_query = f"""
                SELECT COUNT(*) AS total
                FROM ASERP.dbo.PEDIDOS p 
                INNER JOIN ASERP.dbo.PEDIDO_ITENS i ON p.PEDIDO = i.PEDIDO
                    AND p.DATA_VENDA >= '2024-10-01'
            """

            total_rows = pd.read_sql(count_query, self.sql.conn).iloc[0]["total"]
            logging.info(f"Total de registros: {total_rows}")

            offset = 0
            while offset < total_rows:
                query = f"""
                          WITH CalculoBrutoTotal AS (
                              SELECT
                                  p.PEDIDO,
                                  p.CLIENTE,
                                  p.DATA_VENDA,
                                  p.DESCONTO AS desconto_total_pedido,
                                  i.ITEM,
                                  i.SKU,
                                  i.QTD,
                                  i.PRECO,
                                  i.FRETE,
                                  i.QTD * i.PRECO AS valor_bruto_item,
                                  SUM(i.QTD * i.PRECO) OVER (PARTITION BY p.PEDIDO) AS valor_bruto_total_pedido
                              FROM ASERP.dbo.PEDIDOS p 
                              INNER JOIN ASERP.dbo.PEDIDO_ITENS i ON p.PEDIDO = i.PEDIDO
                                  AND p.DATA_VENDA >= '2024-10-01'
                          )
                          SELECT 
                              id_venda = T.PEDIDO,
                              numero_item = T.ITEM,
                              data_venda = T.DATA_VENDA,
                              fk_id_cliente = T.CLIENTE,
                              fk_id_produto = T.SKU,
                              fk_tempo_id = CAST(FORMAT(T.DATA_VENDA, 'yyyyMMdd') AS INT),
                              quantidade_vendida = T.QTD,
                              valor_unitario = T.PRECO,
                              valor_desconto = CAST(
                                  CASE 
                                      WHEN T.valor_bruto_total_pedido = 0 THEN 0 
                                      ELSE 
                                          (T.valor_bruto_item / T.valor_bruto_total_pedido) * T.desconto_total_pedido
                                  END AS DECIMAL(18, 2)),
                              valor_liquido = CAST(
                                  T.valor_bruto_item - 
                                  CASE 
                                      WHEN T.valor_bruto_total_pedido = 0 THEN 0 
                                      ELSE (T.valor_bruto_item / T.valor_bruto_total_pedido) * T.desconto_total_pedido
                                  END AS DECIMAL(18, 2))
                          FROM 
                              CalculoBrutoTotal T
                          ORDER BY 
	                          id_venda, numero_item;
                """
                df = pd.read_sql(query, self.sql.conn)
                logging.info(f"Lote extraído: {len(df)} registros (offset {offset})")
                yield df
                offset += batch_size

        except Exception as e:
            logging.error(f"Erro na extração em lote: {e}")
            return

    def transform(self, df):
        try:
            df["data_venda"] = pd.to_datetime(df["data_venda"])
            # Drop duplicates
            #df = df.drop_duplicates(subset=["id"]) 
            #df['custo'] = pd.to_numeric(df['custo'], errors='coerce')
            #df['custo'] = df['custo'].fillna(0.0)
            #df = df.fillna("")
            # 3. Limpeza e padronização de strings (strip)
            #df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            logging.info("Transformações aplicadas (incluindo tratamento de custo)")
            return df
        except Exception as e:
            logging.error(f"Erro na transformação: {e}")
            return None

    def load(self, df):
        try:
            data = df.to_dict("records")
            self.ch.client.execute(
                  """
                  INSERT INTO fato_vendas (
                    id_venda, 
                    numero_item, 
                    data_venda,
                    fk_id_cliente, 
                    fk_id_produto, 
                    fk_tempo_id, 
                    quantidade_vendida, 
                    valor_unitario, 
                    valor_desconto, 
                    valor_liquido) VALUES""", 
                  data
            )
            logging.info(f"Registros carregados: {len(data)}")
            return True
        except Exception as e:
            logging.error(f"Erro na carga: {e}")
            return False

    def verify(self):
        try:
            total = self.ch.client.execute("SELECT COUNT(*) FROM fato_vendas")[0][0]
            logging.info(f"Verificação: {total} registros na tabela")
            return total
        except Exception as e:
            logging.error(f"Erro na verificação: {e}")
            return 0

    def run(self):
        logging.info("Iniciando ETL em lote...")
        inicio = datetime.now()

        try:
            if not self.sql.connect():
                return False
            if not self.ch.connect():
                return False

            self.create_table()

            total_processado = 0
            for df in self.extract_batch():
                if df is None or df.empty:
                    continue

                df = self.transform(df)
                if df is None:
                    return False

                if not self.load(df):
                    return False

                total_processado += len(df)
                logging.info(f"Acumulado: {total_processado} registros processados")

            total = self.verify()
            duracao = datetime.now() - inicio

            logging.info(f"ETL em lote concluído em {duracao}")
            logging.info(f"Total processado no ETL: {total_processado}")
            logging.info(f"Total presente no ClickHouse: {total}")

            return True

        except Exception as e:
            logging.error(f"Erro geral no batch: {e}")
            return False

        finally:
            self.sql.disconnect()
            self.ch.disconnect()


if __name__ == "__main__":
    etl = ETLProductor() 
    ok = etl.run()

    print("\n" + "=" * 50)
    print("ETL EXECUTADO COM SUCESSO!" if ok else "ERRO NO PROCESSO ETL!")
    print("=" * 50)
    sys.exit(0 if ok else 1)
