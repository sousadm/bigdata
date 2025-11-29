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



2. Dimensão Cliente

CREATE TABLE dim_cliente
(
    cliente_id UInt32,
    tipo_cliente Enum8('FISICA' = 1, 'JURIDICA' = 2),
    -- Campos específicos PF
    cpf String,
    data_nascimento Date,
    genero Enum8('M' = 1, 'F' = 2, 'O' = 3),
    
    -- Campos específicos PJ
    cnpj String,
    razao_social String,
    nome_fantasia String,
    porte_empresa Enum8('ME' = 1, 'EPP' = 2, 'MEDIA' = 3, 'GRANDE' = 4),
    setor_atuacao String,
    data_abertura Date,
    
    -- Campos comuns
    nome_completo String,
    email String,
    telefone String,
    data_cadastro Date,
    segmento String,
    categoria_id UInt32
)
ENGINE = MergeTree()
ORDER BY (cliente_id, tipo_cliente);
