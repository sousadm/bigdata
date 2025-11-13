FROM confluentinc/cp-kafka-connect:7.4.0

USER root

# Instalar curl e unzip
RUN yum install -y curl unzip

# Instalar conectores com versões corretas
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.7.4

# Instalar Debezium SQL Server connector - versão correta
RUN confluent-hub install --no-prompt debezium/debezium-connector-sqlserver:2.2.1

# Criar diretório para drivers
RUN mkdir -p /usr/share/confluent-hub-components/confluentinc-kafka-connect-jdbc/lib

# Baixar driver JDBC do SQL Server
RUN curl -L -o /usr/share/confluent-hub-components/confluentinc-kafka-connect-jdbc/lib/mssql-jdbc-12.2.0.jre11.jar \
    https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.2.0.jre11/mssql-jdbc-12.2.0.jre11.jar

# Verificar instalação
RUN ls -la /usr/share/confluent-hub-components/
