import pyodbc
from clickhouse_driver import Client
import pandas as pd
import logging
from datetime import datetime
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    # ATUALIZADO: Nome do arquivo de log
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_vendedor.log'), 
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
    BATCH_SIZE = 50000  # tamanho do lote padrão
    def __init__(self):
        self.sql = SQLServerConnector()
        self.ch = ClickHouseConnector()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS dim_vendedor (
            id_funcionario UInt32,
            nome String,
            data_carga DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (id_funcionario)
        PARTITION BY toYYYYMM(data_carga)
        """
        try:
            self.ch.client.execute(query)
            logging.info("Tabela 'dim_vendedor' criada/verificada")
        except Exception as e:
            logging.error(f"Erro ao criar tabela: {e}")
            raise

    def extract_batch(self, batch_size=None):
        if batch_size is None:
            batch_size = self.BATCH_SIZE

        try:
            # ATUALIZADO: Tabela de origem
            count_query = """
                          SELECT COUNT(*) AS total FROM ASERP.dbo.funcionario f 
                          WHERE f.vendedor = 1 
                            AND f.id_funcionario  > 0
                      """
            total_rows = pd.read_sql(count_query, self.sql.conn).iloc[0]["total"]
            logging.info(f"Total de registros: {total_rows}")

            offset = 0
            while offset < total_rows:
                # ATUALIZADO: Colunas e tabela de origem
                query = f"""
                    SELECT
                      f.id_funcionario,
                      f.nome 
                    FROM ASERP.dbo.funcionario f 
                    WHERE f.vendedor = 1
                      AND f.id_funcionario  > 0
                    ORDER BY f.id_funcionario 
                    OFFSET {offset} ROWS
                    FETCH NEXT {batch_size} ROWS ONLY
                """
                df = pd.read_sql(query, self.sql.conn)
                # Renomeando colunas (já feito no SELECT com o 'AS')
                # df.columns = ['id_fornecedor', 'cpf_cnpj', 'razao_social', 'nome_fantasia', 'fone1']
                logging.info(f"Lote extraído: {len(df)} registros (offset {offset})")
                yield df
                offset += batch_size

        except Exception as e:
            logging.error(f"Erro na extração em lote: {e}")
            return

    def transform(self, df):
        try:
            # ATUALIZADO: Drop duplicates na coluna Fornecedor
            df = df.drop_duplicates(subset=["id_funcionario"]) 
            df = df.fillna("")

            # Substituição do applymap removido
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

            logging.info("Transformações aplicadas")
            return df
        except Exception as e:
            logging.error(f"Erro na transformação: {e}")
            return None

    def load(self, df):
        try:
            data = df.to_dict("records")
            # ATUALIZADO: Tabela de destino e colunas
            self.ch.client.execute("INSERT INTO dim_vendedor (id_funcionario, nome) VALUES", data)
            logging.info(f"Registros carregados: {len(data)}")
            return True
        except Exception as e:
            logging.error(f"Erro na carga: {e}")
            return False

    def verify(self):
        try:
            # ATUALIZADO: Tabela de verificação
            total = self.ch.client.execute("SELECT COUNT(*) FROM dim_vendedor")[0][0]
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
    # ATUALIZADO: Instancia a nova classe
    etl = ETLProductor() 
    ok = etl.run()

    print("\n" + "=" * 50)
    print("ETL EXECUTADO COM SUCESSO!" if ok else "ERRO NO PROCESSO ETL!")
    print("=" * 50)
    sys.exit(0 if ok else 1)
