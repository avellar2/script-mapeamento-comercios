## 7 — Migration — Tabela lead_outreach

Arquivo: supabase/migration_lead_outreach.sql

Esta migration é **rerodável**: usa CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS, CREATE INDEX IF NOT EXISTS, CREATE OR REPLACE FUNCTION, DROP POLICY IF EXISTS. A seção "Rollback" ao final permite desfazer completamente.

### UP

`sql
-- ============================================================
-- Migration: lead_outreach + RPCs + RLS + grants
-- Rerrodável e idempotente
-- ============================================================

BEGIN;

-- 1. Tabela lead_outreach
CREATE TABLE IF NOT EXISTS public.lead_outreach (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES public.leads(id) ON DELETE SET NULL,
    phone_normalized TEXT NOT NULL,
    campaign_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'reserved'
        CHECK (status IN (
            'reserved',
            'sent',
            'confirmed_from_whatsapp',
            'failed',
            'released',
            'needs_reconciliation'
        )),
    reservation_token UUID,
    settlement_token_hash TEXT,
    source TEXT NOT NULL DEFAULT 'script'
        CHECK (source IN ('script', 'sync_retroativo', 'manual', 'migration')),
    message_direction TEXT
        CHECK (message_direction IS NULL OR message_direction IN ('outbound', 'inbound')),
    message_timestamp TIMESTAMPTZ,
    message_fingerprint TEXT,
    campaign_match BOOLEAN,
    whatsapp_chat_reference TEXT,
    reservation_expires_at TIMESTAMPTZ,
    error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Índices
CREATE UNIQUE INDEX IF NOT EXISTS idx_lead_outreach_blocking
    ON public.lead_outreach (phone_normalized, campaign_key)
    WHERE status IN ('reserved', 'sent', 'confirmed_from_whatsapp', 'needs_reconciliation');

CREATE INDEX IF NOT EXISTS idx_lead_outreach_lead_id ON public.lead_outreach(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_outreach_status ON public.lead_outreach(status);
CREATE INDEX IF NOT EXISTS idx_lead_outreach_campaign ON public.lead_outreach(campaign_key);
CREATE INDEX IF NOT EXISTS idx_lead_outreach_token ON public.lead_outreach(reservation_token);
CREATE INDEX IF NOT EXISTS idx_lead_outreach_source ON public.lead_outreach(source);

-- 3. Trigger updated_at
CREATE OR REPLACE FUNCTION public.lead_outreach_update_updated_at()
RETURNS TRIGGER AS 
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
 LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_lead_outreach_updated_at ON public.lead_outreach;
CREATE TRIGGER trg_lead_outreach_updated_at
    BEFORE UPDATE ON public.lead_outreach
    FOR EACH ROW EXECUTE FUNCTION public.lead_outreach_update_updated_at();
