Essa é a maneira **mais rápida e recomendada** de começar\! Usar o Docker simplifica a instalação e configuração do Prometheus e do Grafana.

Você pode configurar ambos usando o **Docker Compose**, que permite definir e executar aplicações multi-container.

-----

## 🛠️ Configuração Inicial com Docker Compose

Para configurar o Prometheus e o Grafana, você precisará de três arquivos principais em um único diretório:

1.  **`prometheus.yml`**: O arquivo de configuração do Prometheus.
2.  **`docker-compose.yml`**: O arquivo que define e conecta os serviços (Prometheus e Grafana).
3.  **`grafana/`**: Um diretório para persistir os dados do Grafana (opcional, mas recomendado).

### 1\. Crie a Estrutura de Arquivos

Crie um diretório chamado `monitoring` (ou o que preferir) e, dentro dele, crie a seguinte estrutura:

```
monitoring/
├── prometheus.yml
├── docker-compose.yml
└── grafana/
```

### 2\. Defina o `prometheus.yml`

Este arquivo configura o **Prometheus** para monitorar a si mesmo (o que é padrão) e, crucialmente, para **monitorar o Node Exporter** (que será adicionado no `docker-compose.yml` para coletar métricas do host).

```yaml
# prometheus.yml
global:
  scrape_interval: 15s # Puxa métricas a cada 15 segundos

scrape_configs:
  # Monitoramento do próprio Prometheus
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Monitoramento do Node Exporter (para métricas do host)
  - job_name: 'node_exporter'
    static_configs:
      # O nome do serviço no Docker Compose é "node_exporter"
      - targets: ['node_exporter:9100']
```

### 3\. Defina o `docker-compose.yml`

Este arquivo define os três serviços que iremos executar: **Prometheus**, **Grafana** e **Node Exporter**.

```yaml
# docker-compose.yml
version: '3.8'

networks:
  monitor-net:
    driver: bridge

volumes:
  grafana_data: {}

services:
  # 1. Prometheus Server
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      # Monta o arquivo de configuração criado na Etapa 2
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - monitor-net
    restart: unless-stopped

  # 2. Node Exporter (Para coletar métricas do host)
  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/host/rootfs'
    networks:
      - monitor-net
    restart: unless-stopped

  # 3. Grafana Server
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      # Persiste os dados de dashboards e configurações
      - grafana_data:/var/lib/grafana
    networks:
      - monitor-net
    restart: unless-stopped
    # Define uma dependência: Grafana só inicia após Prometheus e Node Exporter
    depends_on:
      - prometheus
      - node_exporter
```

-----

## 4\. 🚀 Execute e Acesse

1.  **Inicie os Contêineres:** Na pasta `monitoring`, execute o comando:

    ```bash
    docker-compose up -d
    ```

    (O `-d` executa os serviços em segundo plano).

2.  **Acesse o Prometheus:** Abra seu navegador em `http://localhost:9090`.

      * Vá para **Status \> Targets** para verificar se o `prometheus` e o `node_exporter` estão com status `UP`.

3.  **Acesse o Grafana:** Abra seu navegador em `http://localhost:3000`.

      * **Login Padrão:** O usuário e senha padrão são **admin** / **admin**. Você será solicitado a criar uma nova senha.

### Próximo Passo no Grafana:

1.  **Adicione a Fonte de Dados (Data Source):**
      * No Grafana, vá em **Configuration** (o ícone de engrenagem) \> **Data Sources**.
      * Clique em **Add data source** e escolha **Prometheus**.
      * No campo **URL**, insira `http://prometheus:9090` (este é o nome do serviço definido no `docker-compose.yml` e a porta interna da rede Docker).
      * Clique em **Save & Test**. Se aparecer "Data source is working", a conexão está pronta\!

Agora você pode criar seus dashboards no Grafana usando as métricas coletadas pelo Prometheus.

