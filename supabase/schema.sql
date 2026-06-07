-- =====================================================
-- Schema de Leads no Supabase
-- Execute no SQL Editor do Supabase
-- Estende o schema existente (emails_enviados, stats_diarias)
-- =====================================================

-- Habilitar extensão para gerar UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- TABELA: leads
-- Fonte da verdade para todos os leads de prospecção
-- =====================================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL DEFAULT '',
    telefone TEXT DEFAULT '',
    whatsapp TEXT DEFAULT '',
    telefone_normalizado TEXT UNIQUE,
    instagram TEXT DEFAULT '',
    email TEXT DEFAULT '',
    categoria TEXT DEFAULT '',
    nicho TEXT DEFAULT '',
    cidade TEXT DEFAULT '',
    bairro TEXT DEFAULT '',
    endereco TEXT DEFAULT '',
    tem_site BOOLEAN DEFAULT FALSE,
    url_site TEXT DEFAULT '',
    avaliacao NUMERIC(3,1) DEFAULT 0,
    num_avaliacoes INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    prioridade TEXT DEFAULT '',
    oferta_sugerida TEXT DEFAULT '',
    mensagem_whatsapp TEXT DEFAULT '',
    link_whatsapp TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'novo'
        CHECK (status IN (
            'novo',
            'pronto_para_enviar',
            'abordado',
            'respondeu',
            'follow_up',
            'interessado',
            'convertido',
            'perdido'
        )),
    origem TEXT DEFAULT '',
    ultimo_contato_em TIMESTAMPTZ,
    proximo_followup_em TIMESTAMPTZ,
    observacoes TEXT DEFAULT '',
    resposta_cliente TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_categoria ON leads(categoria);
CREATE INDEX IF NOT EXISTS idx_leads_cidade ON leads(cidade);
CREATE INDEX IF NOT EXISTS idx_leads_nicho ON leads(nicho);
CREATE INDEX IF NOT EXISTS idx_leads_proximo_followup ON leads(proximo_followup_em);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_origem ON leads(origem);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON leads;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- TABELA: lead_interactions
-- Histórico de todas as interações com cada lead
-- =====================================================
CREATE TABLE IF NOT EXISTS lead_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL
        CHECK (tipo IN (
            'importacao',
            'primeira_abordagem',
            'primeira_abordagem_manual_antiga',
            'follow_up',
            'resposta_cliente',
            'proposta_enviada',
            'convertido',
            'perdido'
        )),
    canal TEXT DEFAULT '',
    mensagem TEXT DEFAULT '',
    observacao TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON lead_interactions(lead_id);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON lead_interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_tipo ON lead_interactions(tipo);

-- =====================================================
-- TABELA: campaigns
-- Registro de cada importação/campanha
-- =====================================================
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL DEFAULT '',
    data DATE DEFAULT CURRENT_DATE,
    nicho TEXT DEFAULT '',
    cidade TEXT DEFAULT '',
    quantidade_leads INTEGER DEFAULT 0,
    observacao TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- RLS (Row Level Security)
-- Permitir SELECT, INSERT, UPDATE para anon (mesmo padrão do projeto)
-- Não permitir DELETE (proteger contra exclusão acidental)
-- =====================================================

-- Habilitar RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Políticas para leads
CREATE POLICY "Leads: select para anon" ON leads
    FOR SELECT TO anon USING (true);

CREATE POLICY "Leads: insert para anon" ON leads
    FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Leads: update para anon" ON leads
    FOR UPDATE TO anon USING (true) WITH CHECK (true);

-- Políticas para lead_interactions
CREATE POLICY "Interactions: select para anon" ON lead_interactions
    FOR SELECT TO anon USING (true);

CREATE POLICY "Interactions: insert para anon" ON lead_interactions
    FOR INSERT TO anon WITH CHECK (true);

-- Políticas para campaigns
CREATE POLICY "Campaigns: select para anon" ON campaigns
    FOR SELECT TO anon USING (true);

CREATE POLICY "Campaigns: insert para anon" ON campaigns
    FOR INSERT TO anon WITH CHECK (true);

-- =====================================================
-- VIEW: leads para abordar (status novo ou pronto_para_enviar)
-- =====================================================
CREATE OR REPLACE VIEW vw_leads_para_abordar AS
SELECT
    id, nome, telefone, whatsapp, telefone_normalizado,
    categoria, nicho, cidade, bairro, score, prioridade,
    oferta_sugerida, mensagem_whatsapp, link_whatsapp, status
FROM leads
WHERE status IN ('novo', 'pronto_para_enviar')
ORDER BY score DESC, prioridade;

-- =====================================================
-- VIEW: follow-ups de hoje
-- =====================================================
CREATE OR REPLACE VIEW vw_followups_hoje AS
SELECT
    l.id, l.nome, l.telefone, l.whatsapp, l.telefone_normalizado,
    l.categoria, l.nicho, l.cidade, l.score, l.prioridade,
    l.oferta_sugerida, l.mensagem_whatsapp, l.link_whatsapp,
    l.status, l.proximo_followup_em, l.ultimo_contato_em
FROM leads l
WHERE l.proximo_followup_em <= NOW()
  AND l.status NOT IN ('convertido', 'perdido')
ORDER BY l.proximo_followup_em ASC, l.score DESC;

-- =====================================================
-- VIEW: resumo por status
-- =====================================================
CREATE OR REPLACE VIEW vw_leads_resumo_status AS
SELECT
    status,
    COUNT(*) as total,
    AVG(score) as score_medio
FROM leads
GROUP BY status
ORDER BY total DESC;