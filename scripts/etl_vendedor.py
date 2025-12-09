import pyodbc
from clickhouse_driver import Client
import pandas as pd
import logging
from datetime import datetime
import sys
import hashlib

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
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


class Anonymizer:
    """Classe para anonimização de dados sensíveis"""
    
    @staticmethod
    def anonymize_name(name, method='hash'):
        """
        Anonimiza um nome usando diferentes métodos
        
        Args:
            name: Nome a ser anonimizado
            method: Método de anonimização ('hash', 'mask', 'initials')
        
        Returns:
            Nome anonimizado
        """
        if not name or pd.isna(name) or name.strip() == "":
            return name
        
        name = str(name).strip()
        
        if method == 'hash':
            # Hash SHA256 - irreversível
            return hashlib.sha256(name.encode()).hexdigest()[:16]
        
        elif method == 'mask':
            # Anonimiza primeiro nome, mostra nome do meio com +3 caracteres, anonimiza restante
            parts = name.split()
            
            if len(parts) == 1:
                # Nome único: anonimiza completamente
                if len(name) <= 2:
                    return name[0] + '*'
                return name[0] + '*' * (len(name) - 2) + name[-1]
            
            elif len(parts) == 2:
                # Dois nomes: anonimiza o primeiro, mascara o segundo
                first_masked = parts[0][0] + '***'
                second_masked = parts[1][0] + '***'
                return first_masked + ' ' + second_masked
            
            else:
                # Três ou mais nomes: anonimiza primeiro, mostra nomes do meio com +3 chars, anonimiza último
                result = []
                
                # Primeiro nome anonimizado
                result.append(parts[0][0] + '***')
                
                # Nomes do meio: mostra completo apenas se tiver mais de 3 caracteres
                for middle_name in parts[1:-1]:
                    if len(middle_name) > 3:
                        result.append(middle_name)
                    else:
                        result.append(middle_name[0] + '***')
                
                # Último nome anonimizado
                result.append(parts[-1][0] + '***')
                
                return ' '.join(result)
        
        elif method == 'initials':
            # Retorna apenas as iniciais
            parts = name.split()
            if len(parts) == 1:
                return name[0] + '.'
            return ' '.join([p[0] + '.' for p in parts if p])
        
        elif method == 'generic':
            # Substitui por um nome genérico numerado
            hash_num = int(hashlib.md5(name.encode()).hexdigest(), 16) % 10000
            return f"Vendedor_{hash_num:04d}"
        
        elif method == 'vendedor':
            # Inicia com VENDEDOR + primeiro nome do meio com mais de 2 caracteres
            parts = name.split()
            
            if len(parts) == 1:
                # Nome único: apenas VENDEDOR + hash
                hash_num = int(hashlib.md5(name.encode()).hexdigest(), 16) % 10000
                return f"VENDEDOR_{hash_num:04d}"
            
            elif len(parts) == 2:
                # Dois nomes: verifica se o segundo tem mais de 2 caracteres
                if len(parts[1]) > 2:
                    return f"VENDEDOR {parts[1]}"
                else:
                    hash_num = int(hashlib.md5(name.encode()).hexdigest(), 16) % 10000
                    return f"VENDEDOR_{hash_num:04d}"
            
            else:
                # Três ou mais nomes: busca o primeiro nome do meio com mais de 2 caracteres
                for middle_name in parts[1:-1]:
                    if len(middle_name) > 2:
                        return f"VENDEDOR {middle_name}"
                
                # Se nenhum nome do meio tiver mais de 2 caracteres, usa hash
                hash_num = int(hashlib.md5(name.encode()).hexdigest(), 16) % 10000
                return f"VENDEDOR_{hash_num:04d}"
        
        else:
            logging.warning(f"Método de anonimização '{method}' desconhecido. Usando 'hash'")
            return Anonymizer.anonymize_name(name, 'hash')


class ETLProductor: 
    BATCH_SIZE = 50000
    
    # CONFIGURAÇÃO DE ANONIMIZAÇÃO
    ANONYMIZE = True  # True para ativar, False para desativar
    ANONYMIZE_METHOD = 'vendedor'  # Opções: 'hash', 'mask', 'initials', 'generic', 'vendedor'
    
    def __init__(self):
        self.sql = SQLServerConnector()
        self.ch = ClickHouseConnector()
        self.anonymizer = Anonymizer()
        self.name_counter = {}  # Contador para nomes duplicados
        
        if self.ANONYMIZE:
            logging.info(f"Anonimização ATIVADA - Método: {self.ANONYMIZE_METHOD}")
        else:
            logging.info("Anonimização DESATIVADA")

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS dim_vendedor (
            id_vendedor UInt32,
            nome String,
            data_carga DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY (id_vendedor)
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
            count_query = """
                SELECT COUNT(*) AS total FROM ASERP.dbo.funcionario f 
            """
            total_rows = pd.read_sql(count_query, self.sql.conn).iloc[0]["total"]
            logging.info(f"Total de registros: {total_rows}")

            offset = 0
            while offset < total_rows:
                query = f"""
                    SELECT
                      f.id_funcionario as id_vendedor,
                      f.nome 
                    FROM ASERP.dbo.funcionario f 
                    ORDER BY f.id_funcionario 
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

    def anonymize_data(self, df):
        """
        Aplica anonimização nos dados se configurado
        """
        if not self.ANONYMIZE:
            return df
        
        try:
            df_copy = df.copy()
            
            # Anonimiza o campo nome com controle de duplicados
            anonymized_names = []
            for name in df_copy['nome']:
                anon_name = self.anonymizer.anonymize_name(name, self.ANONYMIZE_METHOD)
                
                # Verifica se o nome anonimizado já existe
                if anon_name in self.name_counter:
                    self.name_counter[anon_name] += 1
                    # Adiciona sufixo numérico para diferenciar
                    anon_name = f"{anon_name} #{self.name_counter[anon_name]}"
                else:
                    self.name_counter[anon_name] = 1
                
                anonymized_names.append(anon_name)
            
            df_copy['nome'] = anonymized_names
            
            logging.info(f"Anonimização aplicada com método: {self.ANONYMIZE_METHOD}")
            duplicates = sum(1 for count in self.name_counter.values() if count > 1)
            if duplicates > 0:
                logging.info(f"Nomes duplicados diferenciados: {duplicates}")
            
            return df_copy
            
        except Exception as e:
            logging.error(f"Erro na anonimização: {e}")
            return df

    def transform(self, df):
        try:
            df = df.drop_duplicates(subset=["id_vendedor"]) 
            df = df.fillna("")
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Aplica anonimização
            df = self.anonymize_data(df)
            
            logging.info("Transformações aplicadas")
            return df
        except Exception as e:
            logging.error(f"Erro na transformação: {e}")
            return None

    def load(self, df):
        try:
            data = df.to_dict("records")
            self.ch.client.execute("INSERT INTO dim_vendedor (id_vendedor, nome) VALUES", data)
            logging.info(f"Registros carregados: {len(data)}")
            return True
        except Exception as e:
            logging.error(f"Erro na carga: {e}")
            return False

    def verify(self):
        try:
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
    etl = ETLProductor() 
    ok = etl.run()

    print("\n" + "=" * 50)
    print("ETL EXECUTADO COM SUCESSO!" if ok else "ERRO NO PROCESSO ETL!")
    print("=" * 50)
    sys.exit(0 if ok else 1)
