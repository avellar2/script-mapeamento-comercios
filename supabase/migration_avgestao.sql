-- =====================================================
-- Migration AVGESTAO - colunas adicionais na tabela leads
-- Execute no SQL Editor do Supabase.
-- Idempotente (ADD COLUMN IF NOT EXISTS). Nao quebra dados existentes.
-- =====================================================

-- produto: 'landing' (comportamento antigo) ou 'avgestao'
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS produto TEXT DEFAULT 'landing';

-- grupo do AVGESTAO: assistencias, refrigeracao, automotivo, sob_medida, servicos_externos
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS grupo TEXT DEFAULT '';

-- subnicho especifico dentro do grupo (ex: 'Assistencia tecnica de celular')
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS subnicho TEXT DEFAULT '';

-- classificacao: CONFIRMADO | PROVAVEL | NAO CONFIRMADO
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS faz_assistencia TEXT DEFAULT '';

-- score especifico do modo AVGESTAO (0-100), independente do score de landing page
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS score_avgestao INTEGER DEFAULT 0;

-- explicacao textual dos motivos do score_avgestao
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS motivos_score TEXT DEFAULT '';

-- nome curto do negocio (para uso em mensagens)
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS nome_curto TEXT DEFAULT '';

-- Indexes para os novos campos
CREATE INDEX IF NOT EXISTS idx_leads_produto ON leads(produto);
CREATE INDEX IF NOT EXISTS idx_leads_grupo ON leads(grupo);
CREATE INDEX IF NOT EXISTS idx_leads_subnicho ON leads(subnicho);
CREATE INDEX IF NOT EXISTS idx_leads_score_avgestao ON leads(score_avgestao DESC);

-- View: leads AVGESTAO prontos para abordar (produto=avgestao, status novo/pronto)
CREATE OR REPLACE VIEW vw_leads_avgestao_para_abordar AS
SELECT
    id, nome, nome_curto, telefone, whatsapp, telefone_normalizado,
    categoria, nicho, subnicho, grupo, cidade, bairro,
    score_avgestao, faz_assistencia, motivos_score,
    mensagem_whatsapp, link_whatsapp, status
FROM leads
WHERE produto = 'avgestao'
  AND status IN ('novo', 'pronto_para_enviar')
ORDER BY score_avgestao DESC;
