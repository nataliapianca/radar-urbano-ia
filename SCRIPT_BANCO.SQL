-- =====================================================================
-- Radar Urbano IA — esquema do banco de dados (PostgreSQL)
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Tabelas de domínio
-- ---------------------------------------------------------------------

CREATE TABLE categoria (
    id    smallint     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome  varchar(50)  NOT NULL,
    CONSTRAINT uq_categoria_nome UNIQUE (nome)
);

CREATE TABLE prioridade (
    id     smallint     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome   varchar(20)  NOT NULL,
    ordem  smallint     NOT NULL,
    CONSTRAINT uq_prioridade_nome  UNIQUE (nome),
    CONSTRAINT uq_prioridade_ordem UNIQUE (ordem)
);

CREATE TABLE status_relato (
    id     smallint     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome   varchar(30)  NOT NULL,
    ordem  smallint     NOT NULL,
    CONSTRAINT uq_status_relato_nome  UNIQUE (nome),
    CONSTRAINT uq_status_relato_ordem UNIQUE (ordem)
);

-- ---------------------------------------------------------------------
-- Relato
-- ---------------------------------------------------------------------

CREATE TABLE relato (
    id                uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
    texto             varchar(5000)     NOT NULL,
    latitude          double precision  NOT NULL,
    longitude         double precision  NOT NULL,
    referencia_local  text              NULL,        -- pendente de definição
    status_id         smallint          NOT NULL,
    criado_em         timestamptz       NOT NULL DEFAULT now(),
    CONSTRAINT ck_relato_texto_tamanho CHECK (char_length(texto) BETWEEN 10 AND 5000),
    CONSTRAINT ck_relato_latitude      CHECK (latitude  BETWEEN -90  AND 90),
    CONSTRAINT ck_relato_longitude     CHECK (longitude BETWEEN -180 AND 180),
    CONSTRAINT fk_relato_status
        FOREIGN KEY (status_id) REFERENCES status_relato (id)
);

CREATE INDEX ix_relato_status_id ON relato (status_id);
CREATE INDEX ix_relato_criado_em ON relato (criado_em DESC);

-- ---------------------------------------------------------------------
-- Classificação
-- ---------------------------------------------------------------------

CREATE TABLE classificacao (
    id               bigint         GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    relato_id        uuid           NOT NULL,
    categoria_id     smallint       NOT NULL,
    prioridade_id    smallint       NOT NULL,
    setor            varchar(150)   NOT NULL,
    risco_associado  varchar(1000)  NOT NULL,
    modelo_ia        varchar(100)   NULL,
    vigente          boolean        NOT NULL DEFAULT true,
    classificado_em  timestamptz    NOT NULL DEFAULT now(),
    CONSTRAINT ck_classificacao_setor CHECK (char_length(setor) >= 1),
    CONSTRAINT ck_classificacao_risco CHECK (char_length(risco_associado) >= 1),
    CONSTRAINT fk_classificacao_relato
        FOREIGN KEY (relato_id) REFERENCES relato (id) ON DELETE CASCADE,
    CONSTRAINT fk_classificacao_categoria
        FOREIGN KEY (categoria_id) REFERENCES categoria (id),
    CONSTRAINT fk_classificacao_prioridade
        FOREIGN KEY (prioridade_id) REFERENCES prioridade (id)
);

-- Garante no máximo 1 classificação vigente por relato
CREATE UNIQUE INDEX uq_classificacao_vigente_por_relato
    ON classificacao (relato_id)
    WHERE vigente;

CREATE INDEX ix_classificacao_relato_id     ON classificacao (relato_id);
CREATE INDEX ix_classificacao_categoria_id  ON classificacao (categoria_id);
CREATE INDEX ix_classificacao_prioridade_id ON classificacao (prioridade_id);

-- ---------------------------------------------------------------------
-- Informações relevantes (até 20 por classificação)
-- ---------------------------------------------------------------------

CREATE TABLE informacao_relevante (
    classificacao_id  bigint    NOT NULL,
    ordem             smallint  NOT NULL,
    texto             text      NOT NULL,
    CONSTRAINT pk_informacao_relevante PRIMARY KEY (classificacao_id, ordem),
    -- ordem 1..20 + PK composta limitam a 20 itens por classificação
    CONSTRAINT ck_informacao_relevante_ordem CHECK (ordem BETWEEN 1 AND 20),
    CONSTRAINT fk_informacao_relevante_classificacao
        FOREIGN KEY (classificacao_id) REFERENCES classificacao (id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Histórico de status
-- ---------------------------------------------------------------------

CREATE TABLE historico_status (
    id                   bigint       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    relato_id            uuid         NOT NULL,
    status_anterior_id   smallint     NULL,          -- NULL na criação do relato
    status_novo_id       smallint     NOT NULL,
    alterado_em          timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT ck_historico_status_mudou
        CHECK (status_anterior_id IS DISTINCT FROM status_novo_id),
    CONSTRAINT fk_historico_status_relato
        FOREIGN KEY (relato_id) REFERENCES relato (id) ON DELETE CASCADE,
    CONSTRAINT fk_historico_status_anterior
        FOREIGN KEY (status_anterior_id) REFERENCES status_relato (id),
    CONSTRAINT fk_historico_status_novo
        FOREIGN KEY (status_novo_id) REFERENCES status_relato (id)
);

CREATE INDEX ix_historico_status_relato ON historico_status (relato_id, alterado_em);

-- ---------------------------------------------------------------------
-- Dados iniciais (espelham os Enums do backend)
-- ---------------------------------------------------------------------

INSERT INTO categoria (nome) VALUES
    ('Infraestrutura'),
    ('Iluminação'),
    ('Limpeza Urbana'),
    ('Trânsito'),
    ('Segurança'),
    ('Meio Ambiente');

INSERT INTO prioridade (nome, ordem) VALUES
    ('Alta',  1),
    ('Média', 2),
    ('Baixa', 3);

INSERT INTO status_relato (nome, ordem) VALUES
    ('Recebido',     1),
    ('Classificado', 2),
    ('Em andamento', 3),
    ('Resolvido',    4);

COMMIT;