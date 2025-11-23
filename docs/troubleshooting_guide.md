# 🔧 Guia de Troubleshooting - ODBC ClickHouse → SQL Server

## 🎯 Problema Identificado

O erro mostra que há **caracteres extras** no arquivo `odbcinst.ini`:

```
Can't open lib '/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1  <- CORRIGIDO'
```

O texto `  <- CORRIGIDO` está sendo incluído no caminho do driver!

## ✅ Solução Passo a Passo

### Opção 1: Usar Script Automático (RECOMENDADO)

```bash
# 1. Dar permissão de execução
chmod +x fix-odbc-files.sh

# 2. Executar
./fix-odbc-files.sh
```

Este script vai:
- Recriar os arquivos `odbc.ini` e `odbcinst.ini` **sem caracteres extras**
- Verificar o conteúdo com `cat -A` (mostra caracteres invisíveis)
- Executar o check-odbc.sh automaticamente

### Opção 2: Manual

```bash
# 1. Remover arquivos antigos
rm -f odbc.ini odbcinst.ini

# 2. Criar odbcinst.ini (copiar exatamente como está abaixo)
cat > odbcinst.ini << 'EOF'
[ODBC Driver 18 for SQL Server]
Description=Microsoft ODBC Driver 18 for SQL Server
Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1
UsageCount=1

[ODBC]
Trace=No
TraceFile=/tmp/odbc.log
EOF

# 3. Criar odbc.ini
cat > odbc.ini << 'EOF'
[sqlserver_asprod]
Driver=ODBC Driver 18 for SQL Server
Server=sqlserver
Database=master
Uid=sa
Pwd=@Admin123
Port=1433
Encrypt=No
TrustServerCertificate=Yes

[sqlserver_aserp]
Driver=ODBC Driver 18 for SQL Server
Server=sqlserver
Database=master
Uid=sa
Pwd=@Admin123
Port=1433
Encrypt=No
TrustServerCertificate=Yes
EOF

# 4. Verificar que não há caracteres estranhos
cat -A odbcinst.ini
cat -A odbc.ini

# 5. Executar teste
chmod +x check-odbc-improved.sh
./check-odbc-improved.sh
```

## 🔍 Verificações Importantes

### 1. Verificar Caracteres Invisíveis

```bash
# O comando cat -A mostra caracteres invisíveis:
# $ = fim de linha (correto)
# ^M = carriage return (Windows - REMOVER)
# ^I = tab
cat -A odbcinst.ini

# Deve mostrar algo como:
# [ODBC Driver 18 for SQL Server]$
# Description=Microsoft ODBC Driver 18 for SQL Server$
# Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1$
```

### 2. Remover Caracteres Windows (se necessário)

```bash
# Instalar dos2unix (se não tiver)
sudo apt-get install dos2unix

# Converter arquivos
dos2unix odbcinst.ini
dos2unix odbc.ini
```

### 3. Verificar Espaços em Branco

```bash
# Não deve ter espaços no final das linhas
sed -i 's/[[:space:]]*$//' odbcinst.ini
sed -i 's/[[:space:]]*$//' odbc.ini
```

## 📋 Checklist de Diagnóstico

Use o script `check-odbc-improved.sh` que executa:

- [ ] **Arquivo odbcinst.ini** está correto no container
- [ ] **Arquivo odbc.ini** está correto no container  
- [ ] **Biblioteca libmsodbcsql** existe e tem permissões
- [ ] **Driver ODBC** é listado pelo odbcinst
- [ ] **DSNs** são listados pelo odbcinst
- [ ] **Dependências** da biblioteca (ldd) estão OK
- [ ] **Rede** entre ClickHouse e SQL Server funciona
- [ ] **isql** consegue conectar
- [ ] **ClickHouse** consegue usar ODBC

## 🐛 Outros Problemas Comuns

### Erro: "Login failed for user 'sa'"

```bash
# Verificar se SQL Server está pronto
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '@Admin123' -Q "SELECT @@VERSION"

# Resetar senha se necessário
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '@Admin123' -Q "ALTER LOGIN sa WITH PASSWORD = '@Admin123'"
```

### Erro: "Cannot open shared object file"

```bash
# Verificar se biblioteca existe
docker exec clickhouse ls -lh /opt/microsoft/msodbcsql18/lib64/

# Verificar permissões
docker exec clickhouse chmod 755 /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1
```

### Erro: "Connection refused"

```bash
# Testar conectividade
docker exec clickhouse nc -zv sqlserver 1433

# Ver logs do SQL Server
docker-compose logs sqlserver | tail -50
```

### Habilitar Debug ODBC

Edite `odbc.ini` e adicione:

```ini
[ODBC]
Trace=Yes
TraceFile=/tmp/odbc.log
```

Depois execute:

```bash
docker-compose down
docker-compose build --no-cache clickhouse
docker-compose up -d

# Executar teste
docker exec clickhouse clickhouse-client --user default --password admin123 --query "
SELECT * FROM odbc('DSN=sqlserver_asprod', 'SELECT 1')
"

# Ver log de debug
docker exec clickhouse cat /tmp/odbc.log
```

## 🎯 Teste Final

Depois de corrigir os arquivos, execute:

```bash
chmod +x check-odbc-improved.sh
./check-odbc-improved.sh
```

Você deve ver:

```
✓ SQL Server está pronto!
✓ Biblioteca ODBC encontrada
✓ Driver listado: [ODBC Driver 18 for SQL Server]
✓ DSN listado: [sqlserver_asprod]
✓ ldd mostra dependências OK
✓ isql conectou com sucesso
✓ ClickHouse ODBC funcionando: Teste ODBC OK
```

## 📝 Comandos Úteis

```bash
# Ver logs em tempo real
docker-compose logs -f clickhouse

# Entrar no container
docker exec -it clickhouse bash

# Testar SQL Server diretamente
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '@Admin123' -Q "SELECT name FROM sys.databases"

# Reconstruir tudo do zero
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## 🚀 Próximo Passo

Após a conexão funcionar, teste uma query real:

```sql
-- No ClickHouse
CREATE TABLE test_odbc.exemplo
ENGINE = ODBC('DSN=sqlserver_asprod', 'master', 'sys.tables');

SELECT TOP 10 * FROM test_odbc.exemplo;
```