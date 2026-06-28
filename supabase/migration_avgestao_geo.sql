-- =====================================================
-- Migration AVGESTAO GEO - colunas geograficas na tabela leads
-- Execute no SQL Editor do Supabase.
-- Idempotente (ADD COLUMN IF NOT EXISTS + CREATE INDEX IF NOT EXISTS).
-- Nao quebra dados existentes nem o modo landing pages.
--
-- NAO cria nova restricao UNIQUE (a dedup acontece no cliente via
-- config/dedup.py; telefone_normalizado UNIQUE existente permanece).
--
-- Campos adicionados:
--   uf           — sigla da UF (ex: 'RJ')
--   estado       — nome do estado (ex: 'Rio de Janeiro')
--   regiao       — regiao geografica (norte|nordeste|centro_oeste|sudeste|sul)
--   source_query — query do Google Maps que originou o lead
--   source_scope — escopo do run (cidade|cidades|uf|ufs|regiao|brasil|arquivo)
--   run_id       — id da execucao (run_YYYYMMDD_HHMMSS_xxxxxx)
--   captured_at — timestamp de captura (TIMESTAMPTZ)
--   place_id     — Google Maps place_id (identificador forte p/ dedup global)
--   maps_url     — URL do Google Maps (identificador forte p/ dedup global)
-- =====================================================

-- Unidade federativa (sigla)
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS uf TEXT DEFAULT '';

-- Nome do estado por extenso
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS estado TEXT DEFAULT '';

-- Regiao geografica (norte|nordeste|centro_oeste|sudeste|sul)
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS regiao TEXT DEFAULT '';

-- Query do Google Maps que originou o lead (para auditoria/dedup global)
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS source_query TEXT DEFAULT '';

-- Escopo do run que originou o lead
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS source_scope TEXT DEFAULT '';

-- Id da execucao (permite agrupar/retomar por run)
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS run_id TEXT DEFAULT '';

-- Timestamp de captura do lead
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS captured_at TIMESTAMPTZ;

-- Google Maps place_id (identificador forte de dedup global)
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS place_id TEXT DEFAULT '';

-- URL do Google Maps (identificador forte de dedup global)
ALTER TABLE leads
    ADD COLUMN IF NOT EXISTS maps_url TEXT DEFAULT '';

-- ── Indexes seguros (CREATE INDEX IF NOT EXISTS) ─────────────────
-- Apenas para os campos pedidos: uf, run_id, place_id.
-- Nao cria UNIQUE novo.

CREATE INDEX IF NOT EXISTS idx_leads_uf ON leads(uf);
CREATE INDEX IF NOT EXISTS idx_leads_run_id ON leads(run_id);
CREATE INDEX IF NOT EXISTS idx_leads_place_id ON leads(place_id);