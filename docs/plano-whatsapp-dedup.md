# Plano Técnico Revisado — Proteção Contra Mensagens Duplicadas (WhatsApp AVGESTÃO)

> **Status:** Plano — NÃO implementar. Somente leitura.  
> **Data:** 30/06/2026  
> **Branch para execução futura:** `feat/rebuild-whatsapp-dedup`  
> **Base commit:** `f101d94b63d5ef51bc49eedb5b94775c95adda37`  
> **Repositório:** `C:\projetos\script-mapear-comércios`  
> **Branch atual:** `feat/captador-geografico-avgestao-v1` (NÃO alterar)

---

## Sumário

1. [Diagnóstico Factual do Repositório Atual](#1--diagnóstico-factual-do-repositório-atual)
2. [Código Anterior — Confirmação de Inexistência](#2--código-anterior--confirmação-de-inexistência)
3. [Causa Raiz das Duplicidades](#3--causa-raiz-das-duplicidades)
4. [Arquitetura Proposta](#4--arquitetura-proposta)
5. [Arquivos a Criar](#5--arquivos-a-criar)
6. [Arquivos a Alterar](#6--arquivos-a-alterar)
7. [Migration — Tabela `lead_outreach`](#7--migration--tabela-lead_outreach)
8. [RPCs — Reserva Atômica e Settlement](#8--rpcs--reserva-atômica-e-settlement)
9. [Máquina de Estados](#9--máquina-de-estados)
10. [Sincronizador Retroativo](#10--sincronizador-retroativo)
11. [Matcher e Seletores do WhatsApp Web](#11--matcher-e-seletores-do-whatsapp-web)
12. [Fingerprint da Abordagem Comercial](#12--fingerprint-da-abordagem-comercial)
13. [Locks Necessários](#13--locks-necessários)
14. [Autorização — Service Role vs Anon Key](#14--autorização--service-role-vs-anon-key)
15. [Testes Necessários](#15--testes-necessários)
16. [Sequência de Implementação](#16--sequência-de-implementação)
17. [Critérios de Aceite](#17--critérios-de-aceite)
18. [Riscos e Limitações](#18--riscos-e-limitações)
19. [Comandos para Execução Futura](#19--comandos-para-execução-futura)
20. [Estratégia de Commit e Push](#20--estratégia-de-commit-e-push)

---

## 1 — Diagnóstico Factual do Repositório Atual

- **Branch atual:** `feat/captador-geografico-avgestao-v1`
- **Commit:** `f101d94b63d5ef51bc49eedb5b94775c95adda37` — "feat: correcao robustez navegacao + lock.py Windows fix + 346 testes" (2026-06-29)
- **Remote:** `https://github.com/avellar2/script-mapeamento-comercios.git`
- **Status:** Working tree limpo, sem stash, sem worktrees extras, sem branches de whatsapp/dedup/outreach

### Tabelas reais no Supabase

Table `leads` with columns: id UUID PK, nome, telefone, whatsapp, telefone_normalizado TEXT UNIQUE, instagram, email, categoria, nicho, cidade, bairro, endereco, tem_site, url_site, avaliacao, num_avaliacoes, score, prioridade, oferta_sugerida, mensagem_whatsapp, link_whatsapp, status TEXT CHECK (novo|pronto_para_enviar|abordado|respondeu|follow_up|interessado|convertido|perdido), origem, ultimo_contato_em TIMESTAMPTZ, proximo_followup_em TIMESTAMPTZ, observacoes, resposta_cliente, created_at, updated_at. Plus AVGESTAO columns: produto DEFAULT 'landing', grupo, subnicho, faz_assistencia, score_avgestao, motivos_score, nome_curto. Plus geo columns: uf, estado, regiao, source_query, source_scope, run_id, captured_at, place_id, maps_url.

Table `lead_interactions` — audit trail: id UUID PK, lead_id UUID FK, tipo CHECK (importacao|primeira_abordagem|primeira_abordagem_manual_antiga|follow_up|resposta_cliente|proposta_enviada|convertido|perdido), canal, mensagem, observacao, created_at.

Table `campaigns` — registro simples: id, nome, data, nicho, cidade, quantidade_leads, observacao.

**Não existe** tabela `lead_outreach`. **Não existe** RPC no banco além da trigger `update_updated_at_column()`.

### RLS atual

Todas as 3 tabelas permitem SELECT/INSERT/UPDATE para role `anon`. DELETE bloqueado.

### Variáveis de ambiente no .env

SUPABASE_URL, SUPABASE_ANON_KEY (set). SUPABASE_SERVICE_ROLE_KEY NÃO existe.

### Scripts que acessam WhatsApp Web — classificação real

**Scripts que ENVIAM mensagens:**
| Script | Perfil | Envia? | Lock? |
|--------|--------|--------|-------|
| `enviar_auto_avgestao.py` | `.whatsapp_business_profile` | ✅ SIM (30/dia) | `.enviar_auto.pid` |
| `enviar_assistencias_hoje.py` | `.whatsapp_business_profile` | ✅ SIM | ❌ |
| `enviar_7_agora.py` | `.whatsapp_business_profile` | ✅ SIM | ❌ |
| `enviar_5_assistencias.py` | `.whatsapp_business_profile` | ✅ SIM | ❌ |
| `enviar_teste_whatsapp_business.py` | `.whatsapp_business_profile` | ✅ SIM | ❌ |

**Scripts que apenas ABREM (não enviam):**
| Script | Perfil | Função |
|--------|--------|--------|
| `abrir_whatsapp.py` | `.whatsapp_business_profile` | Abre para QR scan |

**Scripts que apenas LEEM (não enviam):**
| Script | Perfil | Função |
|--------|--------|--------|
| `extrair_historico_whatsapp.py` | `.whatsapp_business_profile` | Extrai histórico para CSV |

**Geradores de links (não abrem WhatsApp):**
| Script | Função |
|--------|--------|
| `gerar_campanha_avgestao.py` | Gera HTML com links `whatsapp://send?phone=` |
| `gerar_lista_diaria.py` | Gera links `wa.me` |
| `gerar_painel_prospeccao.py` | Gera links `wa.me` |
| `preparar_campanha.py` | Gera links `wa.me` |
| `campanha_diaria.py` | Gera campanha, tem `carregar_telefones_abordados()` |
| `campanha_avgestao.py` | Gera links `web.whatsapp.com/send?phone=` |

**Marcadores manuais (escrevem no Supabase, não abrem WhatsApp):**
| Script | Função |
|--------|--------|
| `marcar_lead_enviado.py` | Marca UM lead como abordado via CLI |
| `marcar_enviados.py` | Marca lista fixa de nomes como abordados |
| `importar_historico_whatsapp.py` | Importa CSV de histórico para Supabase |

### Perfis Chromium reais

- `.whatsapp_business_profile/` — compartilhado por TODOS os scripts de envio + abertura + extração (existe, povoado com Default/, Local State, etc.)
- `.whatsapp_business_profile.bak/` — backup do perfil
- `.whatsapp_profile/` — perfil separado (WhatsApp pessoal, usado pelo extraction playbook)

### Função de normalização de telefone

`utils/phone_utils.normalizar_telefone_br()` — canônica. Aceita 21999999999 → 5521999999999, (21) 99999-9999 → 5521999999999, 5521999999999 → 5521999999999, 021999999999 → 5521999999999. Rejeita sem DDD → None.

Porém há implementações duplicadas inline em: `extrair_historico_whatsapp.py`, `enviar_teste_whatsapp_business.py`, `enviar_auto_avgestao.py` (is_celular), `enviar_assistencias_hoje.py` (is_cel), `enviar_7_agora.py` (is_cel).

### Como leads são marcados atualmente

Fluxo vulnerável: SELECT status IN (novo, pronto_para_enviar) → envia WhatsApp → PATCH status=abordado. Marcação APÓS envio. Se crash entre envio e PATCH, lead permanece novo.

### Como scripts selecionam leads

Query: `status=in.(novo,pronto_para_enviar)` com filtros adicionais por produto=avgestao, grupo, categoria/nicho. `campanha_diaria.py` tem `carregar_telefones_abordados()` que faz `SELECT telefone_normalizado WHERE status IN (abordado,respondeu,follow_up,interessado,convertido,perdido)` — isso é o mais próximo de proteção existente, mas é local (in-memory set), não atômico.

### Lock existente

`config/lock.py` — LockGlobal e LockRun para o CAPTADOR Google Maps (não WhatsApp). Usa `msvcrt.locking()` no Windows com LK_NBLCK. Heartbeat de 30s, detecção de abandono. Este padrão DEVE ser reutilizado para os novos locks.

### Testes existentes

- `tests/test_dedup.py` — 346+ testes, `python tests/test_dedup.py` ou `pytest`
- `tests/test_lock.py` — com `LOCK_DISABLED=1`, `python tests/test_lock.py`
- `tests/test_avgestao.py` — `python tests/test_avgestao.py`

---

## 2 — Código Anterior — Confirmação de Inexistência

Tabela com 14 buscas, todas negativas:

| Busca | Resultado |
|-------|-----------|
| Branch local `whatsapp\|dedup\|outreach` | ❌ |
| Branch remota `whatsapp\|dedup\|outreach` | ❌ |
| Worktree antigo | ❌ |
| Arquivo `sincronizar_abordados_whatsapp.py` | ❌ |
| Arquivo `migration_lead_outreach.sql` | ❌ |
| Pasta `script-mapear-comercios-whatsapp-dedup` | ❌ |
| Padrão `campaign_key` no código | ❌ |
| Padrão `lead_outreach` no código | ❌ |
| Padrão `needs_reconciliation` no código | ❌ |
| Stash | ❌ Vazio |
| Reflog WhatsApp | ❌ Só commits do captador |

**Conclusão: zero código anterior. Reconstrução total.**

---

## 3 — Causa Raiz das Duplicidades

5 causas simultâneas:

1. **TOCTOU race:** gap de ~30s entre SELECT e PATCH. Dois processos paralelos selecionam mesmo lead.
2. **Múltiplos scripts sem coordenação:** 5 scripts de envio independentes, só 1 tem PID lock (e só para si).
3. **Crash sem rollback:** Playwright/Chrome crasha → lead fica `novo` eternamente.
4. **Falta de reserva atômica:** zero proteção no banco; `telefone_normalizado UNIQUE` só vale na importação.
5. **Perfil WhatsApp compartilhado:** todos usam `.whatsapp_business_profile`; Chromium corrompe com acesso paralelo.

---

## 4 — Arquitetura Proposta

### Campaign Key Estável

```
avgestao:assistencias:primeiro_contato:v1
avgestao:assistencias:follow_up:v1
avgestao:refrigeracao:primeiro_contato:v1
avgestao:automotivo:primeiro_contato:v1
```

Formato: `{produto}:{grupo}:{intencao}:{versao}`

- NUNCA contém data, cidade, estado, run_id, batch_hash, salt aleatório.
- Representa intenção comercial + versão da mensagem.
- `v1` → `v2` somente quando a mensagem comercial MUDAR significativamente.
- Subnicho omitido quando a mensagem é a mesma para todos os subnichos do grupo.

### Deduplicação por Telefone, Não por lead_id

Chave de bloqueio: `(phone_normalized, campaign_key)`

Dois leads diferentes com mesmo telefone COMPARTILHAM o mesmo bloqueio. Se a loja X e filial Y têm o mesmo WhatsApp, só a primeira abordagem passa.

### Tabela Única: `lead_outreach`

(Não criar tabela de campanhas separada para contadores.)

### Índice UNIQUE Parcial

```sql
CREATE UNIQUE INDEX idx_lead_outreach_blocking
ON lead_outreach (phone_normalized, campaign_key)
WHERE status IN ('reserved', 'sent', 'confirmed_from_whatsapp', 'needs_reconciliation');
```

Estados bloqueadores: reserved, sent, confirmed_from_whatsapp, needs_reconciliation.
Estados NÃO bloqueadores: failed, released.

### Duas Camadas

**Camada 1 — Sincronizador Retroativo:** WhatsApp Web → lê chats → detecta mensagens de saída → compara fingerprint → marca `confirmed_from_whatsapp` no Supabase. NUNCA envia. Perfil e lock próprios. Dry-run obrigatório.

**Camada 2 — Reserva Atômica:** Antes de cada envio → RPC `reserve_outreach(phone_normalized, campaign_key)` → se reservado, envia → RPC `settle_outreach`. Se já bloqueado, pula.

### Fluxo de Envio Protegido

```
1. Adquire LockWhatsAppSenderGlobal
2. Abre Chromium (perfil .whatsapp_business_profile)
3. Busca leads elegíveis (status novo/pronto_para_enviar)
4. Para cada lead:
   a. Normaliza telefone → phone_normalized
   b. Gera reservation_token = uuid4()
   c. Chama RPC reserve_outreach(phone_normalized, campaign_key, token, lead_id)
      ├── outcome=reserved → CONTINUA
      ├── outcome=already_blocked → PULA
      └── outcome=invalid → PULA
   d. Navega para web.whatsapp.com/send?phone=...
   e. Detecta estado (chat_open / no_chat / needs_login / selector_error)
      ├── chat_open → envia → RPC settle_outreach(token, 'sent')
      ├── no_chat → RPC settle_outreach(token, 'skipped')
      ├── needs_login → aborta lote, NÃO libera reservas
      └── selector_error → fail-fast, aborta lote
5. Libera LockWhatsAppSenderGlobal
```

### Diagrama ASCII

```
┌──────────────────────────────────────────────────────────┐
│                   Supabase                                │
│  ┌──────────┐       ┌───────────────────────────────┐    │
│  │  leads   │       │        lead_outreach           │    │
│  │          │◄──────│  lead_id (FK, nullable)        │    │
│  │ id (PK)  │       │  phone_normalized (NOT NULL)   │    │
│  │ status   │       │  campaign_key (NOT NULL)       │    │
│  │ telefone │       │  status (CHECK)                │    │
│  │ _norm.   │       │  reservation_token (UUID)      │    │
│  └──────────┘       │  settlement_token_hash         │    │
│                      │  message_fingerprint           │    │
│                      │  UNIQUE(phone_norm, camp_key)  │    │
│                      │  WHERE status IN (blocking)    │    │
│                      └───────────────────────────────┘    │
│                           ▲            ▲                  │
│                           │ RPC        │ RPC              │
│                      ┌────┴─────┐ ┌───┴──────────┐       │
│                      │ Sender   │ │ Sincronizador│       │
│                      │(Playwr.) │ │ (Playwright) │       │
│                      │perfil:   │ │perfil:       │       │
│                      │.whatsapp │ │profiles/     │       │
│                      │_business │ │whatsapp_match│       │
│                      │_profile  │ │              │       │
│                      └──────────┘ └──────────────┘       │
└──────────────────────────────────────────────────────────┘
```

---

## 5 — Arquivos a Criar

| # | Arquivo | Descrição |
|---|---------|-----------|
| 1 | `supabase/migration_lead_outreach.sql` | Tabela + índices + RPCs + RLS + grants |
| 2 | `sincronizar_abordados_whatsapp.py` | Sincronizador retroativo com dry-run |
| 3 | `reservar_outreach.py` | Wrappers Python para RPCs + token UUID |
| 4 | `config/whatsapp_lock.py` | LockWhatsAppSenderGlobal + LockWhatsAppMatch |
| 5 | `config/whatsapp_selectors.py` | Seletores centralizados PT-BR/EN |
| 6 | `whatsapp_match/__init__.py` | Pacote do matcher |
| 7 | `whatsapp_match/matcher.py` | Lógica de match: pesquisa, detecção, fingerprint |
| 8 | `utils/campaign_fingerprint.py` | Geração e comparação de fingerprints |
| 9 | `tests/test_lead_outreach.py` | Testes: migration, RPCs, concorrência, token |
| 10 | `tests/test_whatsapp_selectors.py` | Testes unitários de seletores |
| 11 | `tests/test_sincronizador.py` | Testes com mock Playwright |
| 12 | `tests/test_campaign_fingerprint.py` | Testes de fingerprint |

---

## 6 — Arquivos a Alterar

| # | Arquivo | Alteração |
|---|---------|-----------|
| 1 | `enviar_auto_avgestao.py` | +LockWhatsAppSenderGlobal, +reserve_outreach, +settle_outreach, +fingerprint |
| 2 | `enviar_assistencias_hoje.py` | Idem |
| 3 | `enviar_7_agora.py` | Idem |
| 4 | `enviar_5_assistencias.py` | Idem |
| 5 | `enviar_teste_whatsapp_business.py` | +LockWhatsAppSenderGlobal (mas NÃO reserva — é teste) |
| 6 | `.env` | Adicionar `SUPABASE_SERVICE_ROLE_KEY` |
| 7 | `utils/phone_utils.py` | Adicionar `gerar_variantes_busca()`, `validar_ddd()` |
| 8 | `.gitignore` | Adicionar `profiles/`, `output/avgestao/sync_*`, screenshots |

---

## 7 — Migration — Tabela `lead_outreach`

Complete SQL for `supabase/migration_lead_outreach.sql`:

```sql
-- Idempotente: CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS
-- / CREATE OR REPLACE FUNCTION / DROP POLICY IF EXISTS

BEGIN;

-- 1. Tabela
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
        CHECK (message_direction IN ('outbound', 'inbound', NULL)),
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
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_lead_outreach_updated_at ON public.lead_outreach;
CREATE TRIGGER trg_lead_outreach_updated_at
    BEFORE UPDATE ON public.lead_outreach
    FOR EACH ROW EXECUTE FUNCTION public.lead_outreach_update_updated_at();

-- 4. RLS
ALTER TABLE public.lead_outreach ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "lead_outreach_select_anon" ON public.lead_outreach;
CREATE POLICY "lead_outreach_select_anon" ON public.lead_outreach
    FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "lead_outreach_insert_service" ON public.lead_outreach;
CREATE POLICY "lead_outreach_insert_service" ON public.lead_outreach
    FOR INSERT TO service_role WITH CHECK (true);

DROP POLICY IF EXISTS "lead_outreach_update_service" ON public.lead_outreach;
CREATE POLICY "lead_outreach_update_service" ON public.lead_outreach
    FOR UPDATE TO service_role USING (true) WITH CHECK (true);

-- 5. Função PostgreSQL equivalente ao normalizar_telefone_br
CREATE OR REPLACE FUNCTION public.normalize_phone_br(p_phone TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    v_numeros TEXT;
BEGIN
    v_numeros := regexp_replace(p_phone, '\D', '', 'g');
    IF v_numeros IS NULL OR length(v_numeros) < 10 THEN
        RETURN NULL;
    END IF;
    IF v_numeros LIKE '55%' AND length(v_numeros) >= 12 THEN
        RETURN v_numeros;
    END IF;
    IF v_numeros LIKE '0%' THEN
        v_numeros := substring(v_numeros FROM 2);
    END IF;
    IF length(v_numeros) = 11 OR length(v_numeros) = 10 THEN
        RETURN '55' || v_numeros;
    END IF;
    RETURN NULL;
END;
$$;

-- 6. Revoga escrita direta de anon
REVOKE INSERT, UPDATE, DELETE ON public.lead_outreach FROM anon;
GRANT SELECT ON public.lead_outreach TO anon;

COMMIT;
```

---

## 8 — RPCs — Reserva Atômica e Settlement

### RPC 1: `reserve_outreach`

```sql
CREATE OR REPLACE FUNCTION public.reserve_outreach(
    p_phone_normalized TEXT,
    p_campaign_key TEXT,
    p_reservation_token UUID,
    p_lead_id UUID DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
DECLARE
    v_existing RECORD;
    v_valid_lead BOOLEAN := false;
    v_expires_at TIMESTAMPTZ;
BEGIN
    -- 1. Validar telefone
    IF public.normalize_phone_br(p_phone_normalized) IS NULL THEN
        RETURN jsonb_build_object(
            'outcome', 'invalid',
            'reason', 'invalid_phone'
        );
    END IF;

    -- 2. Validar campaign_key
    IF p_campaign_key IS NULL OR p_campaign_key = '' THEN
        RETURN jsonb_build_object(
            'outcome', 'invalid',
            'reason', 'invalid_campaign_key'
        );
    END IF;

    -- 3. Validar lead_id (se fornecido): comprovar que telefone pertence ao lead
    IF p_lead_id IS NOT NULL THEN
        SELECT EXISTS(
            SELECT 1 FROM public.leads
            WHERE id = p_lead_id
              AND telefone_normalizado = p_phone_normalized
        ) INTO v_valid_lead;
        IF NOT v_valid_lead THEN
            RETURN jsonb_build_object(
                'outcome', 'invalid',
                'reason', 'lead_phone_mismatch'
            );
        END IF;
    END IF;

    -- 4. Verificar estados bloqueadores
    SELECT status, reservation_token INTO v_existing
    FROM public.lead_outreach
    WHERE phone_normalized = p_phone_normalized
      AND campaign_key = p_campaign_key
      AND status IN ('reserved', 'sent', 'confirmed_from_whatsapp', 'needs_reconciliation')
    LIMIT 1;

    IF FOUND THEN
        RETURN jsonb_build_object(
            'outcome', 'already_blocked',
            'existing_status', v_existing.status,
            'existing_token', v_existing.reservation_token
        );
    END IF;

    -- 5. Recuperar reserva vencida (se houver 'reserved' expirada)
    UPDATE public.lead_outreach
    SET status = 'released',
        updated_at = now()
    WHERE phone_normalized = p_phone_normalized
      AND campaign_key = p_campaign_key
      AND status = 'reserved'
      AND reservation_expires_at < now();

    -- 6. Criar reserva atômica
    v_expires_at := now() + interval '30 minutes';

    INSERT INTO public.lead_outreach (
        lead_id, phone_normalized, campaign_key, status,
        reservation_token, source, reservation_expires_at
    ) VALUES (
        p_lead_id, p_phone_normalized, p_campaign_key, 'reserved',
        p_reservation_token, 'script', v_expires_at
    )
    ON CONFLICT (phone_normalized, campaign_key)
    WHERE status IN ('reserved', 'sent', 'confirmed_from_whatsapp', 'needs_reconciliation')
    DO NOTHING
    RETURNING id INTO v_existing;

    IF v_existing.id IS NULL THEN
        -- Concorrência: outro processo reservou entre a verificação e o INSERT
        RETURN jsonb_build_object(
            'outcome', 'already_blocked',
            'reason', 'concurrent_reservation'
        );
    END IF;

    RETURN jsonb_build_object(
        'outcome', 'reserved',
        'reservation_id', v_existing.id,
        'reservation_token', p_reservation_token,
        'expires_at', v_expires_at
    );
END;
$$;

REVOKE ALL ON FUNCTION public.reserve_outreach FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.reserve_outreach TO service_role;
```

### RPC 2: `settle_outreach`

```sql
CREATE OR REPLACE FUNCTION public.settle_outreach(
    p_reservation_id UUID,
    p_reservation_token UUID,
    p_new_status TEXT,
    p_message_fingerprint TEXT DEFAULT NULL,
    p_settlement_token_hash TEXT DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
DECLARE
    v_record RECORD;
BEGIN
    -- 1. Validar token
    SELECT * INTO v_record
    FROM public.lead_outreach
    WHERE id = p_reservation_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'outcome', 'invalid',
            'reason', 'reservation_not_found'
        );
    END IF;

    IF v_record.reservation_token IS DISTINCT FROM p_reservation_token THEN
        RETURN jsonb_build_object(
            'outcome', 'invalid',
            'reason', 'invalid_token'
        );
    END IF;

    -- 2. Validar transição
    IF v_record.status != 'reserved' THEN
        RETURN jsonb_build_object(
            'outcome', 'already_settled',
            'current_status', v_record.status,
            'settled_at', v_record.updated_at
        );
    END IF;

    IF p_new_status NOT IN ('sent', 'failed', 'released', 'needs_reconciliation') THEN
        RETURN jsonb_build_object(
            'outcome', 'invalid',
            'reason', 'invalid_transition'
        );
    END IF;

    -- 3. Atualizar lead_outreach
    UPDATE public.lead_outreach
    SET status = p_new_status,
        settlement_token_hash = COALESCE(p_settlement_token_hash, settlement_token_hash),
        message_fingerprint = COALESCE(p_message_fingerprint, message_fingerprint),
        updated_at = now()
    WHERE id = p_reservation_id
      AND reservation_token = p_reservation_token;

    -- 4. Se 'sent': atualizar leads + criar lead_interactions (mesma transação)
    IF p_new_status = 'sent' AND v_record.lead_id IS NOT NULL THEN
        UPDATE public.leads
        SET status = 'abordado',
            ultimo_contato_em = now(),
            proximo_followup_em = now() + interval '7 days',
            updated_at = now()
        WHERE id = v_record.lead_id
          AND status NOT IN ('convertido', 'perdido');

        INSERT INTO public.lead_interactions (lead_id, tipo, canal, observacao)
        VALUES (
            v_record.lead_id,
            'primeira_abordagem',
            'whatsapp',
            'Envio automático protegido — campaign=' || v_record.campaign_key
        );
    END IF;

    RETURN jsonb_build_object(
        'outcome', 'settled',
        'status', p_new_status,
        'settled_at', now()
    );
END;
$$;

REVOKE ALL ON FUNCTION public.settle_outreach FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.settle_outreach TO service_role;
```

### RPC 3: `reconcile_outreach` (sincronizador)

```sql
CREATE OR REPLACE FUNCTION public.reconcile_outreach(
    p_phone_normalized TEXT,
    p_campaign_key TEXT,
    p_new_status TEXT,  -- 'confirmed_from_whatsapp' ou 'needs_reconciliation'
    p_message_fingerprint TEXT DEFAULT NULL,
    p_message_direction TEXT DEFAULT 'outbound',
    p_message_timestamp TIMESTAMPTZ DEFAULT NULL,
    p_whatsapp_chat_reference TEXT DEFAULT NULL,
    p_campaign_match BOOLEAN DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
BEGIN
    INSERT INTO public.lead_outreach (
        phone_normalized, campaign_key, status,
        source, message_direction, message_timestamp,
        message_fingerprint, whatsapp_chat_reference,
        campaign_match
    ) VALUES (
        p_phone_normalized, p_campaign_key, p_new_status,
        'sync_retroativo', p_message_direction, p_message_timestamp,
        p_message_fingerprint, p_whatsapp_chat_reference,
        p_campaign_match
    )
    ON CONFLICT (phone_normalized, campaign_key)
    WHERE status IN ('reserved', 'sent', 'confirmed_from_whatsapp', 'needs_reconciliation')
    DO UPDATE SET
        status = CASE
            WHEN lead_outreach.status = 'reserved' THEN lead_outreach.status
            ELSE p_new_status
        END,
        message_fingerprint = COALESCE(p_message_fingerprint, lead_outreach.message_fingerprint),
        campaign_match = COALESCE(p_campaign_match, lead_outreach.campaign_match),
        source = 'sync_retroativo',
        updated_at = now();

    RETURN jsonb_build_object('outcome', 'reconciled');
END;
$$;

REVOKE ALL ON FUNCTION public.reconcile_outreach FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.reconcile_outreach TO service_role;
```

### RPC 4: `release_reconciliation` (admin apenas)

```sql
CREATE OR REPLACE FUNCTION public.release_reconciliation(
    p_phone_normalized TEXT,
    p_campaign_key TEXT
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
BEGIN
    UPDATE public.lead_outreach
    SET status = 'released',
        updated_at = now()
    WHERE phone_normalized = p_phone_normalized
      AND campaign_key = p_campaign_key
      AND status = 'needs_reconciliation';

    IF FOUND THEN
        RETURN jsonb_build_object('outcome', 'released');
    END IF;
    RETURN jsonb_build_object('outcome', 'not_found_or_not_needs_reconciliation');
END;
$$;

REVOKE ALL ON FUNCTION public.release_reconciliation FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.release_reconciliation TO service_role;
```

---

## 9 — Máquina de Estados

```
                         reserve_outreach()
                               │
                    ┌──────────▼──────────┐
                    │      reserved        │
                    │  (expira em 30 min)  │
                    └────┬──────┬────┬─────┘
                         │      │    │
              ┌──────────┼──────┼────┼──────────────┐
              ▼          ▼      ▼    ▼              ▼
          ┌──────┐ ┌────────┐ ┌──────────┐ ┌─────────────────────┐
          │ sent │ │ failed │ │ released │ │needs_reconciliation │
          └──────┘ └───┬────┘ └──────────┘ └──────────┬──────────┘
                       │                               │
                       │ (novo token,          ┌───────▼────────┐
                       │  nova reserva)        │ confirmed_from │
                       ▼                       │  _whatsapp     │
                  ┌─────────┐                  │ (via sincroniz.)│
                  │ reserved │                  └────────────────┘
                  └─────────┘
                  
   confirmed_from_whatsapp ←── reconcile_outreach() (sincronizador)
   needs_reconciliation    ←── settle_outreach(token, 'needs_reconciliation')
   released                ←── release_reconciliation() (service_role apenas)
```

Estados BLOQUEADORES (impedem nova reserva): `reserved`, `sent`, `confirmed_from_whatsapp`, `needs_reconciliation`
Estados NÃO bloqueadores: `failed`, `released`

`needs_reconciliation` NUNCA é liberado automaticamente. Só via `release_reconciliation()` com service_role.

---

## 10 — Sincronizador Retroativo

### Arquivo: `sincronizar_abordados_whatsapp.py`

### Modos de operação

```
python sincronizar_abordados_whatsapp.py --dry-run --limit 10   # SÓ LEITURA
python sincronizar_abordados_whatsapp.py --apply --limit 50     # ESCRITA (requer service_role)
```

### Fluxo

```
1. Adquire LockWhatsAppMatch (lock dedicado, NÃO compartilhado com envio)
2. Abre Chromium com perfil profiles/whatsapp_match (PERFIL PRÓPRIO)
3. Navega para web.whatsapp.com
4. Se QR Code → espera até 3 min, aborta se não escaneado
5. Carrega lista de leads do Supabase (apenas com telefone, status != convertido/perdido)
6. Para cada lead (até --limit):
   a. Normaliza telefone (utils/phone_utils)
   b. Pesquisa telefone no campo de busca do WhatsApp Web
   c. Determina estado:
      - matched: chat encontrado, conversa pertence ao número
      - no_chat: busca concluída, zero resultados
      - no_outbound: chat existe mas sem mensagem de saída
      - ambiguous: tem mensagem de saída mas fingerprint não confere
      - confirmed: fingerprint da campanha atual detectado
      - selector_error: campo de busca não encontrado → ABORTAR LOTE
      - login_required: QR Code → ABORTAR LOTE
      - group/channel/community/status: chat não é conversa individual
   d. Se matched + fingerprint compatível:
      - dry-run: registra em CSV
      - apply: chama reconcile_outreach(status='confirmed_from_whatsapp')
   e. Se matched + mensagem de saída mas fingerprint diferente:
      - registra como ambiguous
      - NÃO confirma automaticamente
   f. Salva checkpoint a cada 10 leads (JSON)
7. Gera relatório CSV + JSON
8. Libera LockWhatsAppMatch
```

### Dry-run zero-write

No modo `--dry-run`:
- Usa APENAS SUPABASE_URL + SUPABASE_ANON_KEY
- NÃO carrega SUPABASE_SERVICE_ROLE_KEY
- NENHUMA escrita: sem INSERT, UPDATE, DELETE, RPC de escrita
- Apenas SELECT para ler leads
- Saídas: `output/avgestao/sync_dryrun.csv`, `output/avgestao/sync_dryrun.json`

### Pré-migration

Se a tabela `lead_outreach` não existir (erro 404 na REST API):
- Registra `indisponivel_pre_migration` no relatório
- Continua usando a tabela `leads.status` como fallback
- NÃO tenta aplicar migration automaticamente

### Checkpoint e Resume

- `output/avgestao/sync_checkpoint.json`
- Salvo a cada 10 leads processados
- Se interrompido, retoma do último índice
- Campos: `last_index`, `processed_phones`, `errors`, `stats`

---

## 11 — Matcher e Seletores do WhatsApp Web

### Arquivo: `config/whatsapp_selectors.py`

```python
"""Seletores centralizados para WhatsApp Web — PT-BR e EN."""

# ── Campo de busca (barra lateral) ──
SEARCH_BOX_SELECTORS = [
    # data-testid (mais estável)
    'div[data-testid="chat-list-search"] div[contenteditable="true"]',
    # role + context
    'div[role="textbox"][title="Pesquisar conversa"]',
    'div[role="textbox"][title="Search chat"]',
    # aria-label
    'div[aria-label="Pesquisar conversa"]',
    'div[aria-label="Search chat"]',
]

# ── Indicadores de chat aberto ──
CHAT_OPEN_SELECTORS = [
    'header[data-testid="conversation-header"]',
    'div[data-testid="conversation-panel-wrapper"]',
]

# ── Lista de chats ──
CHAT_LIST_ITEMS = 'div[data-testid="chat-list-item"]'

# ── Nome do contato no painel ──
CONTACT_NAME_SELECTORS = [
    'span[data-testid="conversation-info-header-chat-title"]',
    'header span[dir="auto"]',
]

# ── Telefone no painel de perfil ──
PHONE_SELECTORS = [
    'span[title*="+55"]',
    'span[title*="55"]',
    'div[data-testid="panel-header-title"] span[title]',
]

# ── Indicadores de número inválido ──
NO_CHAT_INDICATORS = [
    "inválido", "invalid",
    "não está no WhatsApp", "not on WhatsApp",
    "inexistente", "doesn't exist",
    "número de telefone não encontrado",
]

# ── Indicadores de QR Code ──
QR_CODE_INDICATORS = [
    "escaneie", "conectar", "QR code",
    "scan", "log in", "entrar",
]

# ── Indicadores de grupo/comunidade ──
GROUP_INDICATORS = [
    'span[data-testid="group-info-drawer"]',
    'span[title*="grupo"]',
]

# ── Mensagens no chat ──
CHAT_MESSAGES = 'div[data-testid="msg-container"]'
OUTBOUND_MESSAGE_INDICATORS = [
    'div[data-testid="msg-check"]',
    'div[data-testid="msg-dblcheck"]',
    'span[aria-label*="Entregue"]',
    'span[aria-label*="Lida"]',
    'span[aria-label*="Delivered"]',
    'span[aria-label*="Read"]',
]
```

### Arquivo: `whatsapp_match/matcher.py`

```python
"""Lógica de match: pesquisa, detecção de estado, fingerprint."""

from enum import Enum

class MatchState(Enum):
    MATCHED = "matched"
    NO_CHAT = "no_chat"
    NO_OUTBOUND = "no_outbound"
    AMBIGUOUS = "ambiguous"
    CONFIRMED = "confirmed"
    SELECTOR_ERROR = "selector_error"
    SEARCH_FIELD_NOT_FOUND = "search_field_not_found"
    LOGIN_REQUIRED = "login_required"
    PAGE_NOT_READY = "page_not_ready"
    GROUP = "group"
    CHANNEL = "channel"
    COMMUNITY = "community"
    STATUS = "status"

def pesquisar_telefone(page, phone_normalized: str, timeout: int = 15) -> MatchState:
    """
    Pesquisa telefone no WhatsApp Web e determina o estado.
    
    Regras obrigatórias:
    - no_chat SOMENTE após: campo encontrado + digitado + busca concluída + zero resultados
    - selector_error NUNCA vira no_chat
    - Se campo global quebrado: salva diagnóstico 1x, interrompe lote
    - Timeout: 15-30s por lead
    """
    # 1. Encontrar campo de busca
    search_box = _find_search_box(page)
    if not search_box:
        _salvar_diagnostico(page, "search_field_not_found")
        return MatchState.SEARCH_FIELD_NOT_FOUND  # → abortar lote
    
    # 2. Digitar telefone e buscar
    search_box.click()
    search_box.fill("")
    search_box.type(phone_normalized, delay=50)
    page.wait_for_timeout(2000)
    
    # 3. Verificar se algum chat apareceu
    chat_items = page.locator(CHAT_LIST_ITEMS)
    if chat_items.count() == 0:
        # Verificar se é "número inválido" vs "sem resultados"
        body_text = page.inner_text("body").lower()
        if any(ind in body_text for ind in NO_CHAT_INDICATORS):
            return MatchState.NO_CHAT
        return MatchState.NO_CHAT  # busca concluída, zero resultados
    
    # 4. Verificar se é grupo/comunidade/status
    ...
    
    # 5. Clicar no chat, extrair telefone do perfil
    ...
    
    return MatchState.MATCHED
```

**Regra de fail-fast:** se `SEARCH_FIELD_NOT_FOUND` ou `SELECTOR_ERROR` ocorrer para 2+ leads consecutivos → abortar lote IMEDIATAMENTE. Não esperar 2 minutos por lead.

---

## 12 — Fingerprint da Abordagem Comercial

### Arquivo: `utils/campaign_fingerprint.py`

```python
"""Fingerprint da mensagem comercial AVGESTÃO."""

import hashlib
import re

# Frases-chave estáveis da mensagem atual (NÃO armazenar texto completo)
AVGESTAO_KEY_PHRASES = [
    "criador do AVGESTÃO",
    "sistema feito para organizar assistências técnicas",
    "registram o aparelho",
    "abrem a ordem de serviço",
    "orçamento para aprovação",
    "cliente acompanha",
    "pelo próprio link",
    "configure a conta",
    "15 dias",
    "testar",
]

def gerar_fingerprint(texto: str) -> str:
    """SHA-256 das frases-chave encontradas no texto."""
    normalizado = _normalizar_para_fingerprint(texto)
    frases_encontradas = [
        frase for frase in AVGESTAO_KEY_PHRASES
        if _normalizar_para_fingerprint(frase) in normalizado
    ]
    if not frases_encontradas:
        return ""
    payload = "|".join(sorted(frases_encontradas))
    return hashlib.sha256(payload.encode()).hexdigest()

def comparar_fingerprint(
    fingerprint_encontrado: str,
    fingerprint_esperado: str
) -> bool:
    """Compara fingerprints. Vazio = sem match."""
    if not fingerprint_encontrado or not fingerprint_esperado:
        return False
    return fingerprint_encontrado == fingerprint_esperado

def _normalizar_para_fingerprint(texto: str) -> str:
    """Normaliza para comparação: lowercase, sem acentos, sem pontuação, espaços únicos."""
    import unicodedata
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ASCII", "ignore").decode("ASCII")
    texto = re.sub(r"[^a-z0-9\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto
```

**Regras:**
- NUNCA armazenar texto completo da conversa
- Apenas hash e metadados (quais frases-chave foram encontradas)
- Mensagem de saída antiga sem fingerprint compatível → `ambiguous`
- Fingerprint vazio → `ambiguous`
- Somente fingerprint compatível → `confirmed`

---

## 13 — Locks Necessários

Reutilizar a implementação segura de `config/lock.py` (msvcrt.locking no Windows, fcntl no POSIX, non-blocking, heartbeat, detecção de abandono).

### Novo módulo: `config/whatsapp_lock.py`

```python
"""Locks para scripts WhatsApp — reutiliza padrão de config/lock.py."""

from config.lock import _lock_arquivo, _unlock_arquivo, _ler_metadados, _escrever_metadados

WHATSAPP_SENDER_LOCK = Path("output/avgestao/whatsapp_sender_global.lock")
WHATSAPP_MATCH_LOCK = Path("output/avgestao/whatsapp_match.lock")

class LockWhatsAppSenderGlobal:
    """Lock global para TODOS os scripts que usam .whatsapp_business_profile."""
    # Mesmo padrão de LockGlobal: msvcrt, heartbeat 30s, detecção de abandono
    ...

class LockWhatsAppMatch:
    """Lock dedicado para o sincronizador (perfil profiles/whatsapp_match)."""
    # NUNCA compartilhado com LockWhatsAppSenderGlobal
    ...
```

### Regras

- Lock ocupado: RECUSA nova execução. NÃO mata processo. NÃO apaga lock ativo.
- NÃO usar erro do Chromium como mecanismo de lock.
- NÃO usar somente arquivo com PID e timeout.
- NÃO usar `os.kill(pid, 0)` no Windows.
- Todo script que usar `.whatsapp_business_profile` DEVE adquirir `LockWhatsAppSenderGlobal`.

### Isolamento de perfis

| Perfil | Lock | Scripts |
|--------|------|---------|
| `.whatsapp_business_profile` | `whatsapp_sender_global.lock` | Todos os `enviar_*.py` + `abrir_whatsapp.py` |
| `profiles/whatsapp_match` | `whatsapp_match.lock` | `sincronizar_abordados_whatsapp.py` |
| Chromium efêmero | `captador_global.lock` | `mapear_comercios.py` |

NENHUM compartilhamento entre estes três.

---

## 14 — Autorização — Service Role vs Anon Key

| Operação | Role | Detalhe |
|----------|------|---------|
| SELECT em leads, lead_outreach, lead_interactions | `anon` | Leituras permitidas |
| SELECT para dry-run do sincronizador | `anon` | Zero escrita |
| `reserve_outreach` RPC | `service_role` | Escrita privilegiada. Sender usa service_role keyção |
| `settle_outreach` RPC | `service_role` | Idempotente por token. Sender usa service_role key |
| `reconcile_outreach` RPC | `service_role` | Escrita privilegiada |
| `release_reconciliation` RPC | `service_role` | Administrativo |
| INSERT/UPDATE/DELETE direto em lead_outreach | `service_role` | Anon revogado |

### Regras para SUPABASE_SERVICE_ROLE_KEY

- Só existe no `.env` (`.gitignore` já cobre `.env`)
- NUNCA vai ao navegador (Playwright não tem acesso)
- NUNCA vai a logs, CSV, checkpoint, JSON de saída
- NUNCA vai ao Git
- NUNCA é carregada em modo `--dry-run`
- Sincronizador só carrega em modo `--apply`

### RPCs SECURITY DEFINER

Todas as RPCs:
- `SET search_path = 'public'` (fixo, mínimo)
- Tabelas e funções schema-qualificadas (`public.`)
- `REVOKE ALL ... FROM PUBLIC`
- `GRANT EXECUTE` apenas a `service_role` (reserve, settle, reconcile, release). Anon NUNCA tem permissao de escrita via RPC
- NENHUMA SQL dinâmica
- Parâmetros validados dentro da função
- NENHUMA escrita direta de `anon` em `lead_outreach` (revogada na migration)

---

## 15 — Testes Necessários

| # | Teste | Arquivo | Tipo |
|---|-------|---------|------|
| 1 | normalizar_telefone_br — casos canônicos | `test_lead_outreach.py` | Unit |
| 2 | normalize_phone_br PostgreSQL = Python | `test_lead_outreach.py` | Integração |
| 3 | campaign_key estável (não contém data/cidade) | `test_lead_outreach.py` | Unit |
| 4 | fingerprint: frases-chave encontradas | `test_campaign_fingerprint.py` | Unit |
| 5 | fingerprint: texto diferente → vazio | `test_campaign_fingerprint.py` | Unit |
| 6 | migration: up + down + re-up (idempotente) | `test_lead_outreach.py` | Integração |
| 7 | migration: rollback não perde dados existentes | `test_lead_outreach.py` | Integração |
| 8 | reserve_outreach: reserva criada | `test_lead_outreach.py` | Integração |
| 9 | reserve_outreach: segunda chamada → already_blocked | `test_lead_outreach.py` | Integração |
| 10 | reserve_outreach: lead_id não confere com telefone → invalid | `test_lead_outreach.py` | Integração |
| 11 | reserve_outreach: dois leads mesmo telefone → segundo bloqueado | `test_lead_outreach.py` | Integração |
| 12 | reserve_outreach: concorrência real (2 threads) | `test_lead_outreach.py` | Integração |
| 13 | settle_outreach: token correto → sent | `test_lead_outreach.py` | Integração |
| 14 | settle_outreach: repete mesmo token → already_settled (idempotente) | `test_lead_outreach.py` | Integração |
| 15 | settle_outreach: token diferente → invalid_token | `test_lead_outreach.py` | Integração |
| 16 | settle_outreach: sent atualiza leads.status + lead_interactions | `test_lead_outreach.py` | Integração |
| 17 | settle_outreach: repete NÃO cria lead_interactions duplicada | `test_lead_outreach.py` | Integração |
| 18 | needs_reconciliation: bloqueia nova reserva | `test_lead_outreach.py` | Integração |
| 19 | release_reconciliation: anon → rejeitado | `test_lead_outreach.py` | Integração |
| 20 | release_reconciliation: service_role → sucesso | `test_lead_outreach.py` | Integração |
| 21 | lock global: segunda instância recusada | `test_lead_outreach.py` | Unit |
| 22 | lock global: não usa os.kill(pid, 0) | `test_lead_outreach.py` | Unit |
| 23 | seletores PT-BR: search field encontrado | `test_whatsapp_selectors.py` | Unit |
| 24 | seletores EN: search field encontrado | `test_whatsapp_selectors.py` | Unit |
| 25 | selector_error ≠ no_chat | `test_whatsapp_selectors.py` | Unit |
| 26 | no_chat só após busca concluída | `test_whatsapp_selectors.py` | Unit |
| 27 | login_required detectado | `test_whatsapp_selectors.py` | Unit |
| 28 | grupo/canal/comunidade/status detectados | `test_whatsapp_selectors.py` | Unit |
| 29 | dry-run: zero INSERT/UPDATE/DELETE | `test_sincronizador.py` | Mock |
| 30 | dry-run: service_role NÃO carregada | `test_sincronizador.py` | Mock |
| 31 | dry-run: funciona sem migration (fallback leads.status) | `test_sincronizador.py` | Mock |
| 32 | sync --apply: reconcile_outreach chamado | `test_sincronizador.py` | Mock |
| 33 | sync: envia 0 mensagens | `test_sincronizador.py` | Mock |
| 34 | sender: reserve antes de abrir WhatsApp | `test_lead_outreach.py` | Mock |
| 35 | sender: settle após envio | `test_lead_outreach.py` | Mock |
| 36 | regressão: test_dedup.py continua passando | `test_dedup.py` | Existente |
| 37 | regressão: test_lock.py continua passando | `test_lock.py` | Existente |
| 38 | regressão: test_avgestao.py continua passando | `test_avgestao.py` | Existente |

⚠️ NUNCA usar Supabase de produção. Usar project de dev ou mock HTTP.

---

## 16 — Sequência de Implementação

| Etapa | Ação | Depende de |
|-------|------|------------|
| 0 | Criar branch `feat/rebuild-whatsapp-dedup` a partir de `f101d94` | — |
| 0.1 | Criar worktree irmão `script-mapear-comercios-whatsapp-dedup` | 0 |
| 1 | Criar `supabase/migration_lead_outreach.sql` | — |
| 2 | Aplicar migration via SQL Editor do Supabase (NÃO script local) | 1 |
| 3 | Criar `config/whatsapp_selectors.py` | — |
| 4 | Criar `tests/test_whatsapp_selectors.py` e executar | 3 |
| 5 | Criar `config/whatsapp_lock.py` (reutilizar config/lock.py) | — |
| 6 | Criar `utils/campaign_fingerprint.py` | — |
| 7 | Criar `tests/test_campaign_fingerprint.py` e executar | 6 |
| 8 | Criar `tests/test_lead_outreach.py` (todos os 20+ testes de RPC) | 2 |
| 9 | Executar `pytest tests/test_lead_outreach.py` | 8 |
| 10 | Criar `reservar_outreach.py` (wrappers Python) | 2 |
| 11 | Criar `whatsapp_match/__init__.py` e `whatsapp_match/matcher.py` | 3 |
| 12 | Criar `sincronizar_abordados_whatsapp.py` | 5, 10, 11 |
| 13 | Criar `tests/test_sincronizador.py` e executar | 12 |
| 14 | Refatorar `enviar_auto_avgestao.py` (+lock + reserve + settle) | 5, 10 |
| 15 | Refatorar `enviar_assistencias_hoje.py` | 5, 10 |
| 16 | Refatorar `enviar_7_agora.py` | 5, 10 |
| 17 | Refatorar `enviar_5_assistencias.py` | 5, 10 |
| 18 | Executar TODOS os testes: `pytest tests/` | 4, 7, 9, 13 |
| 19 | Verificar regressão: `pytest tests/test_dedup.py tests/test_lock.py tests/test_avgestao.py` | 18 |
| 20 | Dry-run do sincronizador: `python sincronizar_abordados_whatsapp.py --dry-run --limit 5` | 12 |
| 21 | Revisar CSV do dry-run | 20 |
| 22 | (após aprovação) Executar sincronizador: `--apply --limit 50` | 21 |
| 23 | Commit e push | 22 |

---

## 17 — Critérios de Aceite

| # | Critério | Verificação |
|---|----------|-------------|
| 1 | Todos os 38+ testes passam | `pytest tests/ -v` |
| 2 | Testes existentes sem regressão | `pytest tests/test_dedup.py tests/test_lock.py tests/test_avgestao.py` |
| 3 | reserve_outreach atômico: 2 chamadas simultâneas → 1 reserved, 1 already_blocked | Teste de concorrência |
| 4 | settle_outreach idempotente: repetir token → already_settled | Teste |
| 5 | settle_outreach NÃO cria lead_interactions duplicada | Teste |
| 6 | Índice UNIQUE parcial bloqueia INSERT direto duplicado | Teste de constraint |
| 7 | needs_reconciliation bloqueia nova reserva | Teste |
| 8 | release_reconciliation rejeitado para anon | Teste |
| 9 | LockWhatsAppSenderGlobal: segunda instância recusada | Teste |
| 10 | Sincronizador --dry-run: zero INSERT/UPDATE/DELETE | Mock |
| 11 | Sincronizador NUNCA contém keyboard.press("Enter") ou botão Enviar | Inspeção de código |
| 12 | Sincronizador não compartilha perfil com scripts de envio | Inspeção |
| 13 | selector_error ≠ no_chat | Teste + inspeção |
| 14 | Fail-fast: seletor quebrado → aborta lote em 2 erros consecutivos | Teste |
| 15 | Timeout por lead ≤ 30s | Teste |
| 16 | Dry-run funciona sem migration (fallback leads.status) | Teste |
| 17 | SUPABASE_SERVICE_ROLE_KEY não aparece em logs/CSV/checkpoint | Inspeção |
| 18 | campaign_key não contém data, cidade, batch_hash | Inspeção |
| 19 | Fingerprint vazio → ambiguous, não confirmed | Teste |
| 20 | Mensagem de saída antiga sem fingerprint compatível → ambiguous | Teste |

---

## 18 — Riscos e Limitações

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| WhatsApp Web mudar seletores | Média | Alto | Seletores centralizados em UM arquivo; atualizar resolve |
| Perfil Chromium corromper com lock paralelo | Baixa | Alto | Lock OS real, perfis separados |
| service_role vazar em log/CSV | Baixa | Crítico | Dry-run não carrega; apply usa env var local apenas |
| Dois sincronizadores simultâneos | Baixa | Médio | LockWhatsAppMatch dedicado |
| Script antigo (sem proteção) rodar após deploy | Alta | Alto | Refatorar TODOS os senders na mesma branch |
| Sincronizador classificar grupo como chat individual | Média | Médio | Seletores específicos para grupo/canal/comunidade/status |
| Migration quebrar dados existentes | Zero | — | CREATE TABLE IF NOT EXISTS; zero ALTER em tabelas existentes |
| RPCs SECURITY DEFINER com search_path vulnerável | Baixa | Crítico | search_path fixo 'public'; funções schema-qualificadas |
| needs_reconciliation acumular sem liberação | Média | Baixo | Relatório periódico; release_reconciliation manual |
| Fingerprint falso-positivo (frases comuns) | Baixa | Médio | 10 frases específicas combinadas; SHA-256 |

---

## 19 — Comandos para Execução Futura

```bash
# ── Isolamento ──
git checkout -b feat/rebuild-whatsapp-dedup f101d94b63d5ef51bc49eedb5b94775c95adda37
git worktree add ../script-mapear-comercios-whatsapp-dedup feat/rebuild-whatsapp-dedup
cd ../script-mapear-comercios-whatsapp-dedup

# ── Criar diretórios ──
mkdir -p profiles/whatsapp_match
mkdir -p output/avgestao
mkdir -p whatsapp_match

# ── Migration (aplicar via SQL Editor do Supabase, NÃO via script) ──
# Copiar conteúdo de supabase/migration_lead_outreach.sql

# ── Adicionar ao .env ──
# SUPABASE_SERVICE_ROLE_KEY=<chave do Supabase Dashboard → Settings → API>

# ── Testes ──
pytest tests/test_whatsapp_selectors.py -v
pytest tests/test_campaign_fingerprint.py -v
pytest tests/test_lead_outreach.py -v
pytest tests/test_sincronizador.py -v

# ── Regressão ──
pytest tests/test_dedup.py tests/test_lock.py tests/test_avgestao.py -v

# ── Todos ──
pytest tests/ -v

# ── Dry-run do sincronizador ──
python sincronizar_abordados_whatsapp.py --dry-run --limit 5

# ── Sincronizador real (após aprovação do dry-run) ──
python sincronizar_abordados_whatsapp.py --apply --limit 50

# ── Commit e push ──
git add -A
git commit -m "feat: protecao contra mensagens duplicadas WhatsApp (reserva atomica + sincronizador retroativo)"
git push origin feat/rebuild-whatsapp-dedup
```

---

## 20 — Estratégia de Commit e Push

| Item | Valor |
|------|-------|
| **Branch** | `feat/rebuild-whatsapp-dedup` |
| **Base** | `f101d94b63d5ef51bc49eedb5b94775c95adda37` |
| **Worktree** | `C:\projetos\script-mapear-comercios-whatsapp-dedup\` |
| **Branch principal** | `feat/captador-geografico-avgestao-v1` — NÃO alterada |
| **Push** | Somente após TODOS os testes passarem + dry-run aprovado |
| **Merge** | Somente após validação em produção |
| **Mensagem** | `feat: protecao contra mensagens duplicadas WhatsApp (reserva atomica + sincronizador retroativo)` |

### Gitignore — adicionar

```
# Perfis WhatsApp (contêm sessão logada)
profiles/

# Output do sincronizador
output/avgestao/sync_*
output/avgestao/whatsapp_*.lock

# Screenshots de diagnóstico
output/avgestao/screenshots/

# HTML de diagnóstico
output/avgestao/diagnostics/
```

### O que NÃO fazer

- ❌ NÃO dar checkout do commit diretamente na pasta principal
- ❌ NÃO aplicar migration antes dos testes
- ❌ NÃO enviar mensagens durante testes
- ❌ NÃO fazer merge até validação
- ❌ NÃO commitar `.env`, `profiles/`, `output/`, screenshots, CSVs com dados reais

---

> **Fim do plano revisado.** Este documento descreve 2 camadas (sincronizador retroativo + reserva atômica), 12 arquivos a criar, 8 a alterar, 1 migration, 4 RPCs, 38+ testes, e 23 etapas de implementação. A execução deve seguir a sequência da Seção 16, validar contra os critérios da Seção 17, e mitigar os riscos da Seção 18.
