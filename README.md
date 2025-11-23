Data Platform with Docker Compose
Este projeto fornece uma plataforma de dados completa usando Docker Compose, incluindo bancos de dados SQL Server, PostgreSQL, ClickHouse e uma stack Kafka com ferramentas de conectividade.

🏗️ Arquitetura
A plataforma consiste nos seguintes serviços:

SQL Server 2022 - Banco de dados transacional

PostgreSQL 15 - Banco de dados relacional

ClickHouse - Banco de dados colunar para analytics

Kafka - Plataforma de streaming de eventos

Zookeeper - Coordenação do cluster Kafka

Kafka Connect - Conectividade para CDC (Change Data Capture)

Kafka REST Proxy - API REST para Kafka

Kafka UI - Interface web para monitoramento

📋 Pré-requisitos
Docker Engine 20.10+

Docker Compose 2.0+

8GB+ de RAM disponível

10GB+ de espaço em disco

🚀 Como executar
Clone o repositório:

bash
git clone <repository-url>
cd <project-directory>
Execute a stack:

bash
docker-compose up -d
Verifique os serviços:

bash
docker-compose ps
🔧 Serviços e Portas
Serviço	Porta	Descrição
SQL Server	1433	Banco de dados Microsoft SQL Server
PostgreSQL	5432	Banco de dados PostgreSQL
ClickHouse	8123	Interface HTTP do ClickHouse
ClickHouse	9000	Interface nativa
ClickHouse	9018	ODBC Bridge
Kafka	9092, 29092	Brokers Kafka
Zookeeper	2181	Coordenação
Kafka Connect	8083	API Connect
Kafka REST Proxy	8082	API REST
Kafka UI	8080	Interface web
🔐 Credenciais
SQL Server
Usuário: SA

Senha: Admin.Server.2025

Porta: 1433

PostgreSQL
Usuário: postgres (configurável via variáveis de ambiente)

Senha: r@@t (configurável via variáveis de ambiente)

Porta: 5432

ClickHouse
Usuário: admin

Senha: admin123

Porta: 8123 (HTTP), 9000 (nativo), 9018 (ODBC)

Kafka
Broker: kafka:9092 (interno), localhost:29092 (externo)

📁 Estrutura de Volumes
sqlserver_data - Dados do SQL Server

postgres_data - Dados do PostgreSQL

clickhouse_data - Dados do ClickHouse

./backup - Backup do SQL Server (host)

./postgresql - Scripts de inicialização do PostgreSQL

./kafka/plugins - Plugins do Kafka Connect

./kafka/connect-config - Configurações do Kafka Connect

🌐 Variáveis de Ambiente
PostgreSQL
Configure via arquivo .env ou variáveis de sistema:

bash
POSTGRES_DB=postgres
POSTGRES_USER=postgres  
POSTGRES_PASSWORD=r@@t
POSTGRES_PORT=5432
ClickHouse
bash
CLICKHOUSE_USER=admin
CLICKHOUSE_PASSWORD=admin123
CLICKHOUSE_DB=default
TZ=America/Sao_Paulo
🔄 Dependências entre Serviços
Kafka depende do Zookeeper

Kafka Connect depende do Kafka e SQL Server

ClickHouse depende do SQL Server

Kafka REST Proxy depende do Kafka e Zookeeper

Kafka UI depende do Kafka

🛠️ Configurações Especiais
ClickHouse
Configurado com bridge ODBC na porta 9018

Timezone America/Sao_Paulo

Limites de arquivo ajustados para performance (262144)

Imagem customizada via Dockerfile-clickhouse-odbc

Kafka Connect
Preparado para CDC do SQL Server

Suporte a conversores JSON

Caminho de plugins customizável

Imagem customizada via Dockerfile-kafka-connect

Kafka
Health checks configurados

Auto-criação de tópicos habilitada

Múltiplos listeners para acesso interno/externo

📊 Monitoramento
Acesse o Kafka UI em: http://localhost:8080

🛑 Comandos Úteis
bash
# Parar todos os serviços
docker-compose down

# Ver logs
docker-compose logs -f [service-name]

# Reiniciar serviço específico
docker-compose restart [service-name]

# Ver status
docker-compose ps

# Remover volumes (cuidado - perde dados)
docker-compose down -v

# Rebuildar imagens customizadas
docker-compose build --no-cache
⚠️ Notas Importantes
Este setup é para ambiente de desenvolvimento

Ajuste senhas para ambientes de produção

Configure backup regular dos volumes

Monitore uso de recursos (especialmente memória)

Os serviços Kafka possuem health checks para inicialização ordenada

Volumes são persistidos entre reinicializações

🔧 Troubleshooting
Verificar saúde dos serviços:
bash
docker-compose ps
Ver logs específicos:
bash
docker-compose logs kafka
docker-compose logs kafka-connect
Problemas comuns:
Portas em uso: Verifique se as portas necessárias estão livres

Memória insuficiente: Aumente os recursos do Docker

Dependências: Aguarde a inicialização completa do Zookeeper antes do Kafka

📝 Estrutura do Projeto
text
.
├── docker-compose.yml
├── Dockerfile-clickhouse-odbc
├── Dockerfile-kafka-connect
├── backup/
├── postgresql/
├── kafka/
│   ├── plugins/
│   └── connect-config/
└── README.md
📞 Suporte
Para issues e dúvidas, consulte a documentação oficial de cada serviço ou abra uma issue no repositório.
