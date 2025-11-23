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
        logging.FileHandler('etl_produtos.log'), 
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


class ETLProdutos: 
    BATCH_SIZE = 50000 
    def __init__(self):
        self.sql = SQLServerConnector()
        self.ch = ClickHouseConnector()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS dim_produto (
            codigo UInt32,
            descricao String,
            unidade String,
            custo Decimal(10, 4), 
            data_carga DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (codigo)
        PARTITION BY toYYYYMM(data_carga)
        """
        try:
            self.ch.client.execute(query)
            logging.info("Tabela 'dim_produto' criada/verificada")
        except Exception as e:
            logging.error(f"Erro ao criar tabela: {e}")
            raise

    def extract_batch(self, batch_size=None):
        if batch_size is None:
            batch_size = self.BATCH_SIZE

        try:
            count_query = "SELECT COUNT(*) AS total FROM ASPROD.dbo.Skus"
            total_rows = pd.read_sql(count_query, self.sql.conn).iloc[0]["total"]
            logging.info(f"Total de registros (Skus): {total_rows}")

            offset = 0
            while offset < total_rows:
                query = f"""
                SELECT 
                    s.Sku AS codigo,
                    p.descricao_fiscal + ' ' + ISNULL(c.descricao_fiscal, '') + ' ' + ISNULL(s.Tamanho, '') AS descricao,
                    u.Sigla AS unidade,
                    s.Custo AS custo
                FROM ASPROD.dbo.Skus s 
                INNER JOIN ASPROD.dbo.Produtos p ON p.Produto = s.Produto 
                LEFT JOIN ASPROD.dbo.Cores c ON c.Cor = s.Cor
                LEFT JOIN ASPROD.dbo.Unidades u ON u.Unidade = s.Unidade 
                
                ORDER BY s.Sku
                OFFSET {offset} ROWS
                FETCH NEXT {batch_size} ROWS ONLY
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
            # Drop duplicates
            df = df.drop_duplicates(subset=["codigo"]) 
            
            # 1. Tratamento da coluna 'custo' (Resolução do problema 'decimal.ConversionSyntax')
            # Converte para float, o que é seguro para a conversão Decimal do ClickHouse.
            # errors='coerce' transforma valores não-numéricos (se houver) em NaN.
            df['custo'] = pd.to_numeric(df['custo'], errors='coerce')
            
            # 2. Preenchimento de NaN (resultantes de nulos SQL ou coercão)
            # Preenche NaNs de 'custo' com 0.0 e demais colunas com string vazia.
            df['custo'] = df['custo'].fillna(0.0)
            df = df.fillna("")

            # 3. Limpeza e padronização de strings (strip)
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

            logging.info("Transformações aplicadas (incluindo tratamento de custo)")
            return df
        except Exception as e:
            logging.error(f"Erro na transformação: {e}")
            return None

    def load(self, df):
        try:
            data = df.to_dict("records")
            self.ch.client.execute(
                "INSERT INTO dim_produto (codigo, descricao, unidade, custo) VALUES",
                data
            )
            logging.info(f"Registros carregados: {len(data)}")
            return True
        except Exception as e:
            logging.error(f"Erro na carga: {e}")
            return False

    def verify(self):
        try:
            total = self.ch.client.execute("SELECT COUNT(*) FROM dim_produto")[0][0]
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
    etl = ETLProdutos() 
    ok = etl.run()

    print("\n" + "=" * 50)
    print("ETL EXECUTADO COM SUCESSO!" if ok else "ERRO NO PROCESSO ETL!")
    print("=" * 50)
    sys.exit(0 if ok else 1)
