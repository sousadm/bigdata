import pandas as pd
import pyodbc
from clickhouse_driver import Client
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ETLVendas:
    def __init__(self, sql_server_config, clickhouse_config):
        """
        Inicializa conexões com SQL Server e ClickHouse
        
        sql_server_config: dict com parâmetros de conexão SQL Server
        clickhouse_config: dict com parâmetros de conexão ClickHouse
        """
        self.sql_server_config = sql_server_config
        self.clickhouse_config = clickhouse_config
        
    def conectar_sql_server(self):
        """Estabelece conexão com SQL Server"""
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.sql_server_config['server']};"
            f"DATABASE={self.sql_server_config['database']};"
            f"UID={self.sql_server_config['username']};"
            f"PWD={self.sql_server_config['password']}"
        )
        return pyodbc.connect(conn_str)
    
    def conectar_clickhouse(self):
        """Estabelece conexão com ClickHouse"""
        return Client(
            host=self.clickhouse_config['host'],
            port=self.clickhouse_config['port'],
            user=self.clickhouse_config['username'],
            password=self.clickhouse_config['password'],
            database=self.clickhouse_config['database']
        )
    
    def criar_tabela_fato(self, recriar=False):
        """
        Cria a tabela fato_vendas no ClickHouse
        
        recriar: Se True, drop a tabela existente antes de criar
        """
        print("Verificando/criando tabela fato_vendas...")
        ch_client = self.conectar_clickhouse()
        
        try:
            if recriar:
                print("  Removendo tabela existente...")
                drop_query = "DROP TABLE IF EXISTS default.fato_vendas"
                ch_client.execute(drop_query)
            
            create_query = """
            CREATE TABLE IF NOT EXISTS default.fato_vendas
            (
                `id_venda` UInt64,
                `numero_item` UInt16,
                `fk_id_cliente` UInt32,
                `fk_id_vendedor` UInt32,
                `fk_id_produto` UInt32,
                `fk_id_produto_grupo` UInt32,
                `fk_tempo_id` UInt32,
                `quantidade_vendida` Decimal(10, 4),
                `valor_unitario` Decimal(10, 4),
                `valor_desconto` Decimal(10, 4),
                `valor_liquido` Decimal(10, 4),
                `data_venda` DateTime,
                `data_carga` DateTime DEFAULT now()
            )
            ENGINE = SummingMergeTree
            PARTITION BY toYYYYMM(data_venda)
            ORDER BY (fk_tempo_id, fk_id_cliente, fk_id_produto, id_venda, numero_item)
            """
            
            ch_client.execute(create_query)
            print("  Tabela fato_vendas verificada/criada com sucesso")
            
        except Exception as e:
            print(f"  Erro ao criar tabela: {str(e)}")
            raise
        finally:
            ch_client.disconnect()
    
    def verificar_dados_existentes(self, ano):
        """
        Verifica se já existem dados para o ano especificado
        
        ano: Ano a verificar
        """
        ch_client = self.conectar_clickhouse()
        
        try:
            query = f"""
            SELECT COUNT(*) as total
            FROM default.fato_vendas
            WHERE toYear(data_venda) = {ano}
            """
            result = ch_client.execute(query)
            total = result[0][0]
            
            if total > 0:
                print(f"⚠️  Atenção: Já existem {total} registros do ano {ano} na tabela")
                return total
            return 0
            
        except Exception as e:
            print(f"  Erro ao verificar dados existentes: {str(e)}")
            return 0
        finally:
            ch_client.disconnect()
    
    def extrair_dados(self, ano=2025):
        """
        Extrai dados do SQL Server usando a query fornecida
        
        ano: Ano para filtro dos dados (default 2025)
        """
        # Nota: A query original tinha uma vírgula faltando após fk_id_produto_grupo
        query = f"""
        WITH CalculoBrutoTotal AS (
            SELECT
                p.PEDIDO,
                p.CLIENTE,
                p.VENDEDOR,
                p.DATA_VENDA,
                p.DESCONTO AS desconto_total_pedido,
                i.ITEM,
                i.SKU,
                s.Grupo,
                i.QTD,
                i.PRECO,
                i.FRETE,
                i.QTD * i.PRECO AS valor_bruto_item,
                SUM(i.QTD * i.PRECO) OVER (PARTITION BY p.PEDIDO) AS valor_bruto_total_pedido
            FROM ASERP.dbo.PEDIDOS p
            INNER JOIN ASERP.dbo.PEDIDO_ITENS i ON p.PEDIDO = i.PEDIDO
            INNER JOIN ASPROD.dbo.Skus s ON s.Sku = i.SKU
            WHERE YEAR(p.DATA_VENDA) = {ano}
        )
        SELECT
            id_venda = T.PEDIDO,
            numero_item = T.ITEM,
            data_venda = T.DATA_VENDA,
            fk_id_cliente = T.CLIENTE,
            fk_id_vendedor = T.VENDEDOR,
            fk_id_produto = T.SKU,
            fk_id_produto_grupo = T.Grupo,
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
            fk_id_vendedor DESC
        """
        
        print("Conectando ao SQL Server...")
        conn = self.conectar_sql_server()
        
        print(f"Extraindo dados do ano {ano}...")
        df = pd.read_sql(query, conn)
        
        conn.close()
        print(f"Extraídos {len(df):,} registros")
        
        return df
    
    def transformar_dados(self, df):
        """
        Realiza transformações necessárias nos dados
        
        df: DataFrame com dados extraídos
        """
        print("Transformando dados...")
        
        # Garantir tipos de dados corretos
        df['id_venda'] = df['id_venda'].astype('uint64')
        df['numero_item'] = df['numero_item'].astype('uint16')
        df['fk_id_cliente'] = df['fk_id_cliente'].astype('uint32')
        df['fk_id_vendedor'] = df['fk_id_vendedor'].astype('uint32')
        df['fk_id_produto'] = df['fk_id_produto'].astype('uint32')
        df['fk_id_produto_grupo'] = df['fk_id_produto_grupo'].astype('uint32')
        df['fk_tempo_id'] = df['fk_tempo_id'].astype('uint32')
        
        # Converter para tipos decimais do ClickHouse
        df['quantidade_vendida'] = pd.to_numeric(df['quantidade_vendida'], errors='coerce')
        df['valor_unitario'] = pd.to_numeric(df['valor_unitario'], errors='coerce')
        df['valor_desconto'] = pd.to_numeric(df['valor_desconto'], errors='coerce')
        df['valor_liquido'] = pd.to_numeric(df['valor_liquido'], errors='coerce')
        
        # Garantir que data_venda seja datetime
        df['data_venda'] = pd.to_datetime(df['data_venda'])
        
        # Verificar e tratar valores nulos
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print("⚠️  Atenção: Valores nulos encontrados:")
            for col, count in null_counts[null_counts > 0].items():
                print(f"    {col}: {count} valores nulos")
            
            # Preencher valores nulos numéricos com 0
            numeric_cols = ['quantidade_vendida', 'valor_unitario', 'valor_desconto', 'valor_liquido']
            for col in numeric_cols:
                if col in df.columns and df[col].isnull().sum() > 0:
                    df[col] = df[col].fillna(0)
                    print(f"    {col} preenchido com 0")
        
        print(f"✓ Dados transformados: {len(df):,} registros")
        return df
    
    def carregar_dados(self, df, batch_size=10000):
        """
        Carrega dados no ClickHouse
        
        df: DataFrame com dados transformados
        batch_size: Tamanho do lote para inserção
        """
        print("Conectando ao ClickHouse...")
        ch_client = self.conectar_clickhouse()
        
        # Query de inserção
        insert_query = """
        INSERT INTO default.fato_vendas (
            id_venda,
            numero_item,
            fk_id_cliente,
            fk_id_vendedor,
            fk_id_produto,            
            fk_id_produto_grupo,
            fk_tempo_id,
            quantidade_vendida,
            valor_unitario,
            valor_desconto,
            valor_liquido,
            data_venda
        ) VALUES
        """
        
        total_rows = len(df)
        rows_inserted = 0
        
        print(f"Iniciando carga de {total_rows:,} registros em lotes de {batch_size:,}...")
        
        # Processar em lotes
        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_data = []
            
            for _, row in batch.iterrows():
                batch_data.append([
                    int(row['id_venda']),
                    int(row['numero_item']),
                    int(row['fk_id_cliente']),
                    int(row['fk_id_vendedor']),
                    int(row['fk_id_produto']),
                    int(row['fk_id_produto_grupo']),
                    int(row['fk_tempo_id']),
                    float(row['quantidade_vendida']),
                    float(row['valor_unitario']),
                    float(row['valor_desconto']),
                    float(row['valor_liquido']),
                    row['data_venda']
                ])
            
            # Inserir lote
            try:
                ch_client.execute(insert_query, batch_data)
                rows_inserted += len(batch)
                progresso = (rows_inserted / total_rows) * 100
                print(f"  Lote {i//batch_size + 1}: {len(batch):,} registros | Progresso: {progresso:.1f}%")
            except Exception as e:
                print(f"❌ Erro ao inserir lote {i//batch_size + 1}: {str(e)}")
                raise
        
        print(f"\n✓ Carga concluída: {rows_inserted:,} registros inseridos")
        
        # Verificar contagem
        count_query = "SELECT COUNT(*) as total FROM default.fato_vendas"
        result = ch_client.execute(count_query)
        print(f"✓ Total de registros na tabela fato_vendas: {result[0][0]:,}")
        
        ch_client.disconnect()
    
    def executar_etl(self, ano=2025, batch_size=10000, recriar_tabela=False, ignorar_existentes=False):
        """
        Executa o processo ETL completo
        
        ano: Ano para extração dos dados
        batch_size: Tamanho do lote para carga
        recriar_tabela: Se True, recria a tabela antes de carregar
        ignorar_existentes: Se True, não verifica dados existentes
        """
        print("=" * 60)
        print("INICIANDO PROCESSO ETL - FATO VENDAS")
        print("=" * 60)
        print(f"Ano: {ano}")
        print(f"Batch size: {batch_size:,}")
        print(f"Recriar tabela: {recriar_tabela}")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Criar/verificar tabela
            self.criar_tabela_fato(recriar=recriar_tabela)
            
            # Verificar dados existentes
            if not ignorar_existentes and not recriar_tabela:
                registros_existentes = self.verificar_dados_existentes(ano)
                if registros_existentes > 0:
                    resposta = input("Deseja continuar? (s/n): ")
                    if resposta.lower() != 's':
                        print("Processo cancelado pelo usuário")
                        return
            
            # Extração
            df = self.extrair_dados(ano)
            
            if len(df) == 0:
                print("⚠️  Nenhum registro encontrado para o ano especificado")
                return
            
            # Transformação
            df_transformado = self.transformar_dados(df)
            
            # Carga
            self.carregar_dados(df_transformado, batch_size)
            
            end_time = datetime.now()
            tempo_total = end_time - start_time
            
            print("\n" + "=" * 60)
            print("✓ PROCESSO ETL CONCLUÍDO COM SUCESSO")
            print(f"Tempo total: {tempo_total}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERRO no processo ETL: {str(e)}")
            raise

# Configurações de conexão
sql_server_config = {
    'server': 'localhost',
    'database': 'ASERP',
    'username': 'sa',
    'password': 'Admin.Server.2025'
}

clickhouse_config = {
    'host': 'localhost',
    'port': 9000,
    'username': 'admin',
    'password': 'admin123',
    'database': 'default'
}

# Script de execução principal
if __name__ == "__main__":
    # Criar instância do ETL
    etl = ETLVendas(sql_server_config, clickhouse_config)
    
    # Executar ETL
    # Opções:
    # - ano: ano a processar
    # - batch_size: tamanho dos lotes
    # - recriar_tabela: True para dropar e recriar a tabela
    # - ignorar_existentes: True para não verificar duplicados
    
    etl.executar_etl(
        ano=2022, 
        batch_size=10000,
        recriar_tabela=False,
        ignorar_existentes=False
    )
