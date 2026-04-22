-- =====================================================
-- Schema do Dashboard de Envios de Email
-- Copie e cole no SQL Editor do Supabase
-- =====================================================

-- Tabela de emails enviados
CREATE TABLE IF NOT EXISTS emails_enviados (
    id BIGSERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    categoria TEXT NOT NULL,
    cidade TEXT NOT NULL,
    telefone TEXT,
    tipo_email TEXT NOT NULL, -- 'cnpj' ou 'comercial'
    template TEXT NOT NULL,
    data_envio TIMESTAMPTZ DEFAULT NOW(),
    email_aberto BOOLEAN DEFAULT FALSE,
    data_abertura TIMESTAMPTZ,
    qtd_aberturas INTEGER DEFAULT 0,
    tracking_id TEXT UNIQUE, -- ID unico para tracking pixel
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Index para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_emails_enviados_email ON emails_enviados(email);
CREATE INDEX IF NOT EXISTS idx_emails_enviados_categoria ON emails_enviados(categoria);
CREATE INDEX IF NOT EXISTS idx_emails_enviados_cidade ON emails_enviados(cidade);
CREATE INDEX IF NOT EXISTS idx_emails_enviados_data ON emails_enviados(data_envio);
CREATE INDEX IF NOT EXISTS idx_emails_enviados_aberto ON emails_enviados(email_aberto);

-- Tabela de estatísticas diárias (opcional, para relatórios)
CREATE TABLE IF NOT EXISTS stats_diarias (
    id BIGSERIAL PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    qtd_enviados INTEGER DEFAULT 0,
    qtd_abertos INTEGER DEFAULT 0,
    taxa_abertura DECIMAL(5,2),
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

-- View para estatísticas gerais
CREATE OR REPLACE VIEW vw_stats_gerais AS
SELECT
    COUNT(*) as total_enviados,
    COUNT(*) FILTER (WHERE email_aberto = TRUE) as total_abertos,
    ROUND(COUNT(*) FILTER (WHERE email_aberto = TRUE)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 2) as taxa_abertura_pct,
    MAX(data_envio) as ultimo_envio,
    COUNT(DISTINCT categoria) as categorias_abrangidas,
    COUNT(DISTINCT cidade) as cidades_abrangidas
FROM emails_enviados;

-- View para emails por categoria
CREATE OR REPLACE VIEW vw_por_categoria AS
SELECT
    categoria,
    COUNT(*) as total_enviados,
    COUNT(*) FILTER (WHERE email_aberto = TRUE) as total_abertos,
    ROUND(COUNT(*) FILTER (WHERE email_aberto = TRUE)::DECIMAL / NULLIF(COUNT(*), 0) * 100, 2) as taxa_abertura_pct
FROM emails_enviados
GROUP BY categoria
ORDER BY total_enviados DESC;

-- View para próximos a reenviar (não abertos em 7+ dias)
CREATE OR REPLACE VIEW vw_reenvio_sugerido AS
SELECT
    nome,
    email,
    categoria,
    cidade,
    tipo_email,
    data_envio,
    EXTRACT(DAY FROM (NOW() - data_envio)) as dias_sem_abrir
FROM emails_enviados
WHERE email_aberto = FALSE
  AND data_envio < NOW() - INTERVAL '7 days'
ORDER BY data_envio ASC;
