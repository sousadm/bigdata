############# Estrutura de dados OLAP   ##################
1. Dimensão Tempo
CREATE TABLE IF NOT EXISTS dim_tempo (
    tempo_id UInt32,
    data Date,
    ano UInt16,
    semestre UInt8,
    trimestre UInt8,
    mes UInt8,
    mes_nome String,
    mes_abrev String,
    dia UInt8,
    dia_semana UInt8,
    dia_semana_nome String,
    semana_ano UInt8,
    eh_final_semana UInt8
)
ENGINE = MergeTree
ORDER BY (data);


INSERT INTO dim_tempo
SELECT 
    toUInt32(toString(toYear(dt)) || 
             right(toString(toMonth(dt) + 100), 2) || 
             right(toString(toDayOfMonth(dt) + 100), 2)) as tempo_id,
    dt as data,
    toUInt16(toYear(dt)) as ano,
    toUInt8(ceil(toMonth(dt) / 6)) as semestre,
    toUInt8(ceil(toMonth(dt) / 3)) as trimestre,
    toUInt8(toMonth(dt)) as mes,
    multiIf(
        toMonth(dt) = 1, 'Janeiro',
        toMonth(dt) = 2, 'Fevereiro', 
        toMonth(dt) = 3, 'Março',
        toMonth(dt) = 4, 'Abril',
        toMonth(dt) = 5, 'Maio',
        toMonth(dt) = 6, 'Junho',
        toMonth(dt) = 7, 'Julho',
        toMonth(dt) = 8, 'Agosto',
        toMonth(dt) = 9, 'Setembro',
        toMonth(dt) = 10, 'Outubro',
        toMonth(dt) = 11, 'Novembro',
        'Dezembro'
    ) as mes_nome,
    multiIf(
        toMonth(dt) = 1, 'Jan',
        toMonth(dt) = 2, 'Fev',
        toMonth(dt) = 3, 'Mar',
        toMonth(dt) = 4, 'Abr',
        toMonth(dt) = 5, 'Mai',
        toMonth(dt) = 6, 'Jun',
        toMonth(dt) = 7, 'Jul',
        toMonth(dt) = 8, 'Ago',
        toMonth(dt) = 9, 'Set',
        toMonth(dt) = 10, 'Out',
        toMonth(dt) = 11, 'Nov',
        'Dez'
    ) as mes_abrev,
    toUInt8(toDayOfMonth(dt)) as dia,
    toUInt8(toDayOfWeek(dt)) as dia_semana,
    multiIf(
        toDayOfWeek(dt) = 1, 'Domingo',
        toDayOfWeek(dt) = 2, 'Segunda-feira',
        toDayOfWeek(dt) = 3, 'Terça-feira',
        toDayOfWeek(dt) = 4, 'Quarta-feira',
        toDayOfWeek(dt) = 5, 'Quinta-feira',
        toDayOfWeek(dt) = 6, 'Sexta-feira',
        'Sábado'
    ) as dia_semana_nome,
    toUInt8(toWeek(dt)) as semana_ano,
    toUInt8(if(toDayOfWeek(dt) IN (1, 7), 1, 0)) as eh_final_semana
FROM (
    SELECT toDate('2020-01-01') + number as dt
    FROM numbers(365 * 10) -- 10 anos de dados
)
WHERE dt <= today() + interval 2 year; -- Até um ano no futuro



CREATE TABLE default.fato_vendas
(
    `id_venda` UInt64,
    `numero_item` UInt16,
    `fk_id_cliente` UInt32,
    `fk_id_vendedor` UInt32,
    `fk_id_produto` UInt32,
    `fk_tempo_id` UInt32,`quantidade_vendida` Decimal(10,4),
    `valor_unitario` Decimal(10, 4),
    `valor_desconto` Decimal(10, 4),
    `valor_liquido` Decimal(10, 4),
    `data_venda` DateTime,
    `data_carga` DateTime DEFAULT now()
)
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(data_venda)
ORDER BY (fk_tempo_id,
 fk_id_cliente,
 fk_id_produto,
 id_venda,
 numero_item)
SETTINGS index_granularity = 8192;


CREATE TABLE default.dim_cliente
(
    `id_cliente` UInt32,
    `cpf_cnpj` String,
    `nome_fantasia` String,
    `razao_social` String,
    `data_carga` DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(data_carga)
ORDER BY id_cliente
SETTINGS index_granularity = 8192;



CREATE TABLE default.dim_fornecedor
(
    `id_fornecedor` UInt32,
    `cpf_cnpj` String,
    `razao_social` String,
    `nome_fantasia` String,
    `fone1` String,
    `data_carga` DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(data_carga)
ORDER BY id_fornecedor
SETTINGS index_granularity = 8192;



CREATE TABLE default.dim_produto
(
    `id` UInt32,
    `descricao` String,
    `unidade` String,
    `custo` Decimal(10, 4),
    `data_carga` DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree
ORDER BY id
SETTINGS index_granularity = 8192;



CREATE TABLE default.dim_usuario
(
    `username` String,
    `password` String,
    `email` String,
    `data_carga` DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree
ORDER BY username
SETTINGS index_granularity = 8192;



CREATE TABLE default.dim_vendedor
(
    `id_vendedor` UInt32,
    `nome` String,
    `data_carga` DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(data_carga)
ORDER BY id_vendedor
SETTINGS index_granularity = 8192;
