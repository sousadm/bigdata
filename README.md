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
=======
# Documentação da Infraestrutura Big Data

## Visão Geral

Esta documentação descreve uma infraestrutura completa de Big Data containerizada com Docker Compose, incluindo bancos de dados relacionais, OLAP, streaming de dados e ferramentas de monitoramento.

## Arquitetura

A infraestrutura é composta pelos seguintes componentes:

- **SQL Server** - Banco de dados relacional Microsoft
- **PostgreSQL** - Banco de dados relacional open source
- **ClickHouse** - Banco de dados OLAP de alto desempenho
- **Apache Kafka** - Plataforma de streaming distribuída
- **Kafka Connect** - Framework para integração CDC (Change Data Capture)
- **Kafka REST Proxy** - API REST para Kafka
- **Kafka UI** - Interface web para monitoramento
- **Zookeeper** - Coordenação de serviços distribuídos

## Serviços Detalhados

### 1. SQL Server

**Imagem:** `mcr.microsoft.com/mssql/server:2022-latest`

**Portas:**
- `1433:1433` - Porta padrão do SQL Server

**Credenciais:**
- Usuário: `sa`
- Senha: `Admin.Server.2025`

**Volumes:**
- `sqlserver_data:/var/opt/mssql` - Dados persistentes
- `./backup:/var/backup` - Diretório de backups

**Características:**
- Reinício automático habilitado
- EULA aceito automaticamente

---

### 2. PostgreSQL

**Imagem:** `postgres:15`

**Portas:**
- `5432:5432` (configurável via variável de ambiente)

**Credenciais Padrão:**
- Banco: `postgres`
- Usuário: `postgres`
- Senha: `r@@t`

**Volumes:**
- `postgres_data:/var/lib/postgresql/data` - Dados persistentes
- `./postgresql:/docker-entrypoint-initdb.d` - Scripts de inicialização

**Variáveis de Ambiente Configuráveis:**
- `POSTGRES_DB` - Nome do banco de dados
- `POSTGRES_USER` - Usuário administrador
- `POSTGRES_PASSWORD` - Senha do administrador
- `POSTGRES_PORT` - Porta de exposição

---

### 3. ClickHouse

**Build:** Custom (Dockerfile-clickhouse-odbc)

**Portas:**
- `8123:8123` - Interface HTTP
- `9000:9000` - Interface nativa
- `9018:9018` - ODBC Bridge

**Credenciais:**
- Usuário: `admin`
- Senha: `admin123`
- Database: `default`

**Volumes:**
- `clickhouse_data:/var/lib/clickhouse` - Dados persistentes

**Configurações:**
- Timezone: America/Sao_Paulo
- Limite de arquivos abertos: 262144
- Dependência: SQL Server

---

### 4. Apache Kafka

**Imagem:** `confluentinc/cp-kafka:7.4.0`

**Portas:**
- `9092:9092` - Comunicação interna
- `29092:29092` - Comunicação externa (localhost)

**Configurações:**
- Broker ID: 1
- Criação automática de tópicos: Habilitada
- Replication Factor: 1 (adequado para desenvolvimento)

**Health Check:**
- Comando: Lista de tópicos via bootstrap-server
- Intervalo: 10s
- Timeout: 10s
- Retries: 10

**Dependências:**
- Zookeeper (com health check)

---

### 5. Zookeeper

**Imagem:** `confluentinc/cp-zookeeper:7.4.0`

**Portas:**
- `2181:2181` - Porta do cliente

**Configurações:**
- Client Port: 2181
- Tick Time: 2000ms

**Health Check:**
- Comando: `echo ruok | nc localhost 2181`
- Intervalo: 10s
- Timeout: 5s
- Retries: 5

---

### 6. Kafka REST Proxy

**Imagem:** `confluentinc/cp-kafka-rest:7.4.0`

**Portas:**
- `8082:8082` - API REST HTTP

**Funcionalidade:**
- Permite interação com Kafka via requisições HTTP
- Útil para aplicações que não possuem cliente Kafka nativo

**Configurações:**
- Bootstrap Servers: kafka:9092
- Zookeeper: zookeeper:2181

---

### 7. Kafka Connect

**Build:** Custom (Dockerfile-kafka-connect)

**Portas:**
- `8083:8083` - API REST do Connect

**Funcionalidade:**
- Framework para integração CDC (Change Data Capture)
- Captura mudanças do SQL Server em tempo real
- Publica eventos no Kafka

**Configurações:**
- Group ID: compose-connect-group
- Key/Value Converter: JSON
- Schemas: Desabilitados

**Volumes:**
- `./kafka/plugins:/usr/share/confluent-hub-components` - Plugins personalizados
- `./kafka/connect-config:/etc/kafka-connect/config` - Configurações

**Tópicos Internos:**
- `docker-connect-configs` - Configurações de conectores
- `docker-connect-offsets` - Offsets de processamento
- `docker-connect-status` - Status dos conectores

---

### 8. Kafka UI

**Imagem:** `provectuslabs/kafka-ui:latest`

**Portas:**
- `8080:8080` - Interface web

**Funcionalidade:**
- Monitoramento visual do cluster Kafka
- Gerenciamento de tópicos
- Visualização de mensagens
- Métricas e estatísticas

**Configurações:**
- Cluster Name: local
- Bootstrap Servers: kafka:9092

---

## Rede

**Nome:** `bigdata-net`

**Driver:** Bridge

Todos os serviços estão conectados à mesma rede, permitindo comunicação interna através dos nomes dos containers.

---

## Volumes Persistentes

| Volume | Descrição |
|--------|-----------|
| `sqlserver_data` | Dados do SQL Server |
| `postgres_data` | Dados do PostgreSQL |
| `clickhouse_data` | Dados do ClickHouse |

---

## Inicialização

### Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- Mínimo 8GB RAM disponível
- Mínimo 20GB espaço em disco

### Comandos

```bash
# Iniciar toda a infraestrutura
docker-compose up -d

# Verificar status dos serviços
docker-compose ps

# Ver logs de um serviço específico
docker-compose logs -f <nome-do-serviço>

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (ATENÇÃO: Remove todos os dados)
docker-compose down -v
```

---

## Ordem de Inicialização

1. **Zookeeper** - Coordenação distribuída
2. **Kafka** - Aguarda Zookeeper estar saudável
3. **SQL Server** - Banco de dados fonte
4. **ClickHouse** - Aguarda SQL Server
5. **PostgreSQL** - Inicialização independente
6. **Kafka Connect** - Aguarda Kafka e SQL Server
7. **Kafka REST Proxy** - Aguarda Kafka
8. **Kafka UI** - Aguarda Kafka

---

## Casos de Uso

### 1. Pipeline CDC (Change Data Capture)

- SQL Server captura mudanças em tempo real
- Kafka Connect publica eventos no Kafka
- ClickHouse consome eventos para análise OLAP

### 2. Streaming Analytics

- Dados chegam via Kafka REST Proxy
- Processamento em tempo real com Kafka Streams
- Armazenamento em ClickHouse para queries analíticas

### 3. Data Lake

- PostgreSQL como banco operacional
- SQL Server para dados legados
- ClickHouse como data warehouse analítico

---

## Acessos Rápidos

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| SQL Server | `localhost:1433` | sa / Admin.Server.2025 |
| PostgreSQL | `localhost:5432` | postgres / r@@t |
| ClickHouse HTTP | `http://localhost:8123` | admin / admin123 |
| ClickHouse Native | `localhost:9000` | admin / admin123 |
| Kafka UI | `http://localhost:8080` | N/A |
| Kafka Connect API | `http://localhost:8083` | N/A |
| Kafka REST Proxy | `http://localhost:8082` | N/A |

---

## Troubleshooting

### Kafka não inicia

```bash
# Verificar se Zookeeper está saudável
docker-compose ps zookeeper

# Ver logs do Zookeeper
docker-compose logs zookeeper

# Reiniciar Kafka
docker-compose restart kafka
```

### ClickHouse com problemas de conexão

```bash
# Verificar limite de arquivos
docker exec clickhouse bash -c "ulimit -n"

# Ver logs
docker-compose logs clickhouse
```

### Kafka Connect não conecta ao SQL Server

```bash
# Testar conectividade
docker exec kafka-connect ping sqlserver

# Verificar logs de erro
docker-compose logs kafka-connect | grep ERROR
```

---

## Monitoramento

### Verificar Health Checks

```bash
# Status geral
docker-compose ps

# Health check do Kafka
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Health check do Zookeeper
docker exec zookeeper echo ruok | nc localhost 2181
```

### Métricas

- **Kafka UI**: Interface visual completa em `http://localhost:8080`
- **Kafka Connect**: Status via API REST em `http://localhost:8083/connectors`

---

## Segurança

### Considerações Importantes

⚠️ **Esta configuração é para desenvolvimento/teste. Para produção:**

1. Alterar todas as senhas padrão
2. Implementar SSL/TLS nas conexões
3. Configurar autenticação SASL no Kafka
4. Limitar acesso via firewall/security groups
5. Usar secrets management (ex: Docker Secrets, Vault)
6. Implementar backup automatizado
7. Configurar replicação adequada (atualmente RF=1)

---

## Manutenção

### Backup

```bash
# Backup SQL Server
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'Admin.Server.2025' \
  -Q "BACKUP DATABASE [nome_db] TO DISK = N'/var/backup/backup.bak'"

# Backup PostgreSQL
docker exec postgresql pg_dump -U postgres postgres > backup.sql
```

### Limpeza

```bash
# Remover containers parados
docker-compose rm

# Limpar volumes não utilizados
docker volume prune

# Limpar imagens antigas
docker image prune -a
```

---

## Suporte e Documentação Adicional

- [SQL Server Docs](https://docs.microsoft.com/sql/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [ClickHouse Docs](https://clickhouse.com/docs/)
- [Apache Kafka Docs](https://kafka.apache.org/documentation/)
- [Kafka Connect Docs](https://docs.confluent.io/platform/current/connect/)

---

## Changelog

**Versão 1.0** - Configuração inicial
- SQL Server 2022
- PostgreSQL 15
- ClickHouse com ODBC Bridge
- Kafka 7.4.0 com Connect e REST Proxy
- Kafka UI para monitoramento

---

## Licença

Esta infraestrutura utiliza componentes com diferentes licenças. Verifique as licenças individuais de cada componente antes do uso em produção.
