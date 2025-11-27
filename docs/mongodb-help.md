

1. Conectar-se com Credenciais (Recomendado)

#docker exec -it meu_mongodb_local mongosh -u user_admin -p senha_secreta --authenticationDatabase admin
docker exec -it mongodb_local mongosh -u admin -p admin123 --authenticationDatabase admin

2. Usando o Comando auth (Se já estiver no mongosh)
#Se você já está dentro do shell do MongoDB, mas ainda não se autenticou, você pode fazê-lo usando o comando db.auth():

use admin 
db.auth("user_admin", "senha_secreta") 
show dbs

3. Enviar connector para o kafka
curl -X POST -H "Content-Type: application/json" --data @produto-mongodb-sink.json http://localhost:8083/connectors
