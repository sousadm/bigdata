✅ Serviços em execução:
SQL Server - Porta 1433
PostgreSQL - Porta 5432
ClickHouse - Portas 8123 (HTTP) e 9000 (Native)
ZooKeeper - Porta 2181
Kafka - Portas 9092 e 29092
Kafka Connect - Porta 8083
Kafka UI - Porta 8080

🔗 Conexões no DBeaver:
ClickHouse: localhost:9000 (sem autenticação)
PostgreSQL: localhost:5432 (usuário: postgres, senha: r@@t)
SQL Server: localhost:1433 (usuário: sa, senha: @dmin123)

📊 Para monitorar:
bash
# Ver status de todos os serviços
docker-compose ps

# Ver logs específicos
docker-compose logs [serviço]

# Acessar Kafka UI
# http://localhost:8080
