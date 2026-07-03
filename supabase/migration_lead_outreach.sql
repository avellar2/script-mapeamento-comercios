-- ============================================================
-- migration_lead_outreach.sql
-- Proteção contra mensagens duplicadas no WhatsApp (AVGESTÃO)
-- Owner: postgres (role de migração do Supabase)
-- search_path seguro; sem SQL dinâmica; sem escrita direta anon.
-- Rerodável: CREATE IF NOT EXISTS / CREATE OR REPLACE / IF NOT EXISTS
-- ============================================================

-- ============================================================
-- 1. TABELA lead_outreach
-- ============================================================
CREATE TABLE IF NOT EXISTS public.lead_outreach (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id                   UUID REFERENCES public.leads(id) ON DELETE SET NULL,
  phone_normalized          TEXT NOT NULL,
  campaign_key              TEXT NOT NULL,
  status                    TEXT NOT NULL DEFAULT 'reserved'
                            CHECK (status IN ('reserved','sent','confirmed_from_whatsapp',
                                              'failed','released','needs_reconciliation')),
  reservation_token         UUID,
  settlement_token_hash     TEXT,
  source                    TEXT,
  message_direction         TEXT,
  message_timestamp         TIMESTAMPTZ,
  message_fingerprint       TEXT,
  campaign_match            BOOLEAN,
  whatsapp_chat_reference   TEXT,
  reservation_expires_at    TIMESTAMPTZ,
  error_code                TEXT,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 2. TRIGGER updated_at
-- ============================================================
DROP TRIGGER IF EXISTS set_updated_at_lead_outreach ON public.lead_outreach;
CREATE TRIGGER set_updated_at_lead_outreach
  BEFORE UPDATE ON public.lead_outreach
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- 3. ÍNDICES
-- ============================================================
-- Barreira física: um (phone, campaign) ativo só pode ter uma linha bloqueadora.
-- Sem condição temporal no predicado (TTL é responsabilidade da RPC).
CREATE UNIQUE INDEX IF NOT EXISTS uq_lead_outreach_active
  ON public.lead_outreach (phone_normalized, campaign_key)
  WHERE status IN ('reserved','sent','confirmed_from_whatsapp','needs_reconciliation');

CREATE INDEX IF NOT EXISTS idx_lead_outreach_lead
  ON public.lead_outreach (lead_id);

CREATE INDEX IF NOT EXISTS idx_lead_outreach_status
  ON public.lead_outreach (status);

CREATE INDEX IF NOT EXISTS idx_lead_outreach_phone
  ON public.lead_outreach (phone_normalized);

-- ============================================================
-- 4. FUNÇÃO AUXILIAR: normalizar_telefone_br_sql
-- Espelho da lógica Python em utils/phone_utils.normalizar_telefone_br
-- Determinística; mesma entrada => mesma saída.
-- ============================================================
CREATE OR REPLACE FUNCTION public.normalizar_telefone_br_sql(p_valor TEXT)
RETURNS TEXT
LANGUAGE plpgsql IMMUTABLE SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_digitos TEXT;
  v_ddd     TEXT;
BEGIN
  IF p_valor IS NULL THEN
    RETURN NULL;
  END IF;

  v_digitos := regexp_replace(p_valor, '[^0-9]', '', 'g');

  IF v_digitos = '' OR v_digitos IS NULL THEN
    RETURN NULL;
  END IF;

  -- remove prefixo internacional 00
  IF v_digitos LIKE '00%' THEN
    v_digitos := substring(v_digitos FROM 3);
  END IF;

  -- já com 55 e tamanho válido (12 = fixo, 13 = celular)
  IF v_digitos LIKE '55%' AND length(v_digitos) IN (12, 13) THEN
    v_ddd := substring(v_digitos FROM 3 FOR 2);
    IF v_ddd ~ '^(1[1-9]|[2-9][0-9])$' THEN
      RETURN v_digitos;
    END IF;
    RETURN NULL;
  END IF;

  -- remove um 0 à frente (ex: 021...)
  IF v_digitos LIKE '0%' THEN
    v_digitos := substring(v_digitos FROM 2);
  END IF;

  -- adiciona 55 quando ausente
  IF length(v_digitos) = 11 OR length(v_digitos) = 10 THEN
    v_ddd := substring(v_digitos FROM 1 FOR 2);
    IF v_ddd ~ '^(1[1-9]|[2-9][0-9])$' THEN
      RETURN '55' || v_digitos;
    END IF;
  END IF;

  RETURN NULL;
END;
$$;

-- ============================================================
-- 5. FUNÇÃO AUXILIAR: interaction_type_from_campaign_key
-- Mapeia o tipo de abordagem da campaign_key para o enum de lead_interactions.
-- 'primeiro_contato' -> 'primeira_abordagem'
-- 'follow_up'        -> 'follow_up'
-- outro              -> erro (retorna NULL)
-- ============================================================
CREATE OR REPLACE FUNCTION public.interaction_type_from_campaign_key(p_campaign_key TEXT)
RETURNS TEXT
LANGUAGE plpgsql IMMUTABLE SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_parts TEXT[];
  v_tipo  TEXT;
BEGIN
  IF p_campaign_key IS NULL THEN
    RETURN NULL;
  END IF;

  v_parts := string_to_array(p_campaign_key, ':');

  IF array_length(v_parts, 1) < 3 THEN
    RETURN NULL;
  END IF;

  v_tipo := v_parts[3];

  IF v_tipo = 'primeiro_contato' THEN
    RETURN 'primeira_abordagem';
  END IF;

  IF v_tipo = 'follow_up' THEN
    RETURN 'follow_up';
  END IF;

  RETURN NULL;
END;
$$;

-- ============================================================
-- 6. FUNÇÃO AUXILIAR: validate_lead_campaign
-- Valida lead_id existe, telefone canônico corresponde, produto/grupo compatíveis.
-- Retorna 'ok' ou código de erro.
-- ============================================================
CREATE OR REPLACE FUNCTION public.validate_lead_campaign(
  p_lead_id          UUID,
  p_phone_normalized TEXT,
  p_campaign_key     TEXT
) RETURNS TEXT
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_telefone TEXT;
  v_whatsapp TEXT;
  v_produto  TEXT;
  v_grupo    TEXT;
  v_canon    TEXT;
  v_parts    TEXT[];
BEGIN
  IF p_phone_normalized IS NULL OR p_phone_normalized !~ '^\d{12,13}$' THEN
    RETURN 'invalid_phone';
  END IF;

  IF p_lead_id IS NULL THEN
    RETURN 'lead_not_found';
  END IF;

  SELECT telefone, whatsapp, produto, grupo
    INTO v_telefone, v_whatsapp, v_produto, v_grupo
    FROM public.leads
   WHERE id = p_lead_id;

  IF NOT FOUND THEN
    RETURN 'lead_not_found';
  END IF;

  -- calcula o canônico a partir dos dados do lead
  v_canon := COALESCE(
    public.normalizar_telefone_br_sql(v_whatsapp),
    public.normalizar_telefone_br_sql(v_telefone)
  );

  IF v_canon IS NULL OR v_canon <> p_phone_normalized THEN
    RETURN 'phone_mismatch';
  END IF;

  -- valida que produto e grupo da campaign_key batem com o lead
  v_parts := string_to_array(p_campaign_key, ':');

  IF array_length(v_parts, 1) IS DISTINCT FROM 4 THEN
    RETURN 'campaign_mismatch';
  END IF;

  IF COALESCE(v_produto, '') IS DISTINCT FROM v_parts[1] THEN
    RETURN 'campaign_mismatch';
  END IF;

  IF COALESCE(v_grupo, '') IS DISTINCT FROM v_parts[2] THEN
    RETURN 'campaign_mismatch';
  END IF;

  RETURN 'ok';
END;
$$;

-- ============================================================
-- 7. FUNÇÃO AUXILIAR: outreach_transition_allowed
-- Máquina de estados. Finais: sent, confirmed_from_whatsapp.
-- ============================================================
CREATE OR REPLACE FUNCTION public.outreach_transition_allowed(p_from TEXT, p_to TEXT)
RETURNS BOOLEAN
LANGUAGE sql IMMUTABLE SET search_path = public, pg_temp, extensions
AS $$
  SELECT (p_from, p_to) IN (
    ('reserved','sent'),
    ('reserved','failed'),
    ('reserved','released'),
    ('reserved','needs_reconciliation'),
    ('needs_reconciliation','confirmed_from_whatsapp'),
    ('needs_reconciliation','released')
  ) OR (p_from = p_to);
$$;

-- ============================================================
-- 8. RPC: reserve_outreach
-- Reserva atômica com token de posse. TTL fixo no servidor (30 min).
-- Exige service role (não anon).
-- ============================================================
CREATE OR REPLACE FUNCTION public.reserve_outreach(
  p_phone_normalized TEXT,
  p_campaign_key     TEXT,
  p_lead_id          UUID,
  p_source           TEXT DEFAULT 'sender:auto'
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_existing   public.lead_outreach%ROWTYPE;
  v_validation TEXT;
  v_now        TIMESTAMPTZ := now();
  v_ttl        CONSTANT INTEGER := 1800;
  v_token      UUID := gen_random_uuid();
  v_id         UUID;
BEGIN
  -- validação de parâmetros
  IF p_phone_normalized IS NULL OR p_phone_normalized !~ '^\d{12,13}$' THEN
    RETURN jsonb_build_object('outcome', 'invalid_phone');
  END IF;

  IF p_campaign_key IS NULL
     OR p_campaign_key !~ '^[a-z0-9_]+:[a-z0-9_]+:[a-z0-9_]+:v[0-9]+$'
  THEN
    RETURN jsonb_build_object('outcome', 'invalid_campaign_key');
  END IF;

  IF p_lead_id IS NULL THEN
    RETURN jsonb_build_object('outcome', 'invalid_lead_id');
  END IF;

  IF p_source IS NULL OR p_source NOT IN ('sender:auto','sender:manual','sender:test') THEN
    RETURN jsonb_build_object('outcome', 'invalid_source');
  END IF;

  -- validação lead/telefone/campanha no banco
  v_validation := public.validate_lead_campaign(p_lead_id, p_phone_normalized, p_campaign_key);

  IF v_validation <> 'ok' THEN
    RETURN jsonb_build_object('outcome', 'invalid_lead_match', 'reason', v_validation);
  END IF;

  -- procura registro bloqueador ativo (único pelo índice parcial) e trava
  SELECT * INTO v_existing
    FROM public.lead_outreach
   WHERE phone_normalized = p_phone_normalized
     AND campaign_key = p_campaign_key
     AND status IN ('reserved','sent','confirmed_from_whatsapp','needs_reconciliation')
   ORDER BY created_at DESC
   LIMIT 1
   FOR UPDATE;

  IF FOUND THEN
    CASE v_existing.status
      WHEN 'sent' THEN
        RETURN jsonb_build_object('outcome', 'already_sent');
      WHEN 'confirmed_from_whatsapp' THEN
        RETURN jsonb_build_object('outcome', 'already_confirmed');
      WHEN 'needs_reconciliation' THEN
        RETURN jsonb_build_object('outcome', 'needs_reconciliation');
      WHEN 'reserved' THEN
        -- NULL de expires_at => válida (bloqueia). Só reclaim se vencida.
        IF v_existing.reservation_expires_at IS NOT NULL
           AND v_existing.reservation_expires_at < v_now
        THEN
          UPDATE public.lead_outreach
             SET status = 'released',
                 error_code = 'stale_reclaimed',
                 reservation_token = NULL,
                 reservation_expires_at = NULL,
                 updated_at = v_now
           WHERE id = v_existing.id;
          -- cai para o INSERT abaixo (nova reserva com novo token)
        ELSE
          RETURN jsonb_build_object('outcome', 'reserved_by_other');
        END IF;
      ELSE
        RETURN jsonb_build_object('outcome', 'reserved_by_other');
    END CASE;
  END IF;

  -- tenta reservar (barreira física ON CONFLICT DO NOTHING)
  INSERT INTO public.lead_outreach
        (lead_id, phone_normalized, campaign_key, status, source,
         message_direction, reservation_token, reservation_expires_at)
  VALUES (p_lead_id, p_phone_normalized, p_campaign_key, 'reserved', p_source,
          'outbound', v_token, v_now + make_interval(secs => v_ttl))
  ON CONFLICT (phone_normalized, campaign_key)
  WHERE status IN ('reserved','sent','confirmed_from_whatsapp','needs_reconciliation')
  DO NOTHING
  RETURNING id INTO v_id;

  IF v_id IS NULL THEN
    -- concorrência: outra transação criou bloqueadora entre SELECT e INSERT
    RETURN jsonb_build_object('outcome', 'reserved_by_other');
  END IF;

  RETURN jsonb_build_object(
    'outcome', 'reserved',
    'reservation_id', v_id,
    'reservation_token', v_token,
    'expires_at', v_now + make_interval(secs => v_ttl)
  );
EXCEPTION WHEN OTHERS THEN
  RETURN jsonb_build_object('outcome', 'error', 'error_code', 'reserve_exception');
END;
$$;

-- ============================================================
-- 9. RPC: settle_outreach
-- Finalização atômica numa transação.
-- Exige reservation_id + reservation_token.
-- Retry-idempotente: após commit + queda, mesma chamada => already_settled.
-- Token diferente => invalid_token.
-- ============================================================
CREATE OR REPLACE FUNCTION public.settle_outreach(
  p_reservation_id      UUID,
  p_reservation_token   UUID,
  p_new_status          TEXT,
  p_message_timestamp   TIMESTAMPTZ DEFAULT NULL,
  p_fingerprint         TEXT DEFAULT NULL,
  p_campaign_match      BOOLEAN DEFAULT NULL,
  p_obs                 TEXT DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_row        public.lead_outreach%ROWTYPE;
  v_validation TEXT;
  v_token_hash TEXT;
  v_int_type   TEXT;
BEGIN
  -- validação de parâmetros
  IF p_new_status IS NULL OR p_new_status NOT IN ('sent','failed','released','needs_reconciliation') THEN
    RETURN jsonb_build_object('outcome', 'invalid_status');
  END IF;

  IF p_reservation_id IS NULL OR p_reservation_token IS NULL THEN
    RETURN jsonb_build_object('outcome', 'invalid_args');
  END IF;

  v_token_hash := encode(digest(p_reservation_token::text, 'sha256'), 'hex');

  -- busca a reserva e trava a linha
  SELECT * INTO v_row
    FROM public.lead_outreach
   WHERE id = p_reservation_id
   FOR UPDATE;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('outcome', 'not_found');
  END IF;

  -- ============================================================
  -- RETRY-IDEMPOTÊNCIA: se a linha já foi finalizada
  -- ============================================================
  IF v_row.status <> 'reserved' THEN
    IF v_row.settlement_token_hash IS NOT NULL
       AND v_row.settlement_token_hash = v_token_hash
    THEN
      RETURN jsonb_build_object('outcome', 'already_settled', 'status', v_row.status);
    END IF;

    -- token diferente não finaliza
    RETURN jsonb_build_object('outcome', 'invalid_token');
  END IF;

  -- ============================================================
  -- POSSE: valida token vivo
  -- ============================================================
  IF v_row.reservation_token IS NULL OR v_row.reservation_token <> p_reservation_token THEN
    RETURN jsonb_build_object('outcome', 'invalid_token');
  END IF;

  -- ============================================================
  -- TRANSIÇÃO: valida pela máquina de estados
  -- ============================================================
  IF NOT public.outreach_transition_allowed(v_row.status, p_new_status) THEN
    RETURN jsonb_build_object(
      'outcome', 'invalid_transition',
      'from', v_row.status,
      'to', p_new_status
    );
  END IF;

  -- ============================================================
  -- VALIDAÇÃO: lead/telefone/campanha (só para estados que marcam abordado)
  -- ============================================================
  IF p_new_status IN ('sent', 'confirmed_from_whatsapp') THEN
    v_validation := public.validate_lead_campaign(
      v_row.lead_id, v_row.phone_normalized, v_row.campaign_key
    );

    IF v_validation <> 'ok' THEN
      RETURN jsonb_build_object('outcome', 'invalid_lead_match', 'reason', v_validation);
    END IF;
  END IF;

  -- ============================================================
  -- ATUALIZA lead_outreach (guarda hash de prova; anula token vivo)
  -- ============================================================
  UPDATE public.lead_outreach
     SET status = p_new_status,
         message_timestamp = COALESCE(p_message_timestamp, message_timestamp),
         message_fingerprint = COALESCE(p_fingerprint, message_fingerprint),
         campaign_match = COALESCE(p_campaign_match, campaign_match),
         reservation_token = NULL,
         settlement_token_hash = v_token_hash,
         reservation_expires_at = NULL,
         error_code = CASE
                        WHEN p_new_status IN ('failed','needs_reconciliation')
                        THEN COALESCE(error_code, 'settle_' || p_new_status)
                        ELSE error_code
                      END,
         updated_at = now()
   WHERE id = p_reservation_id;

  -- ============================================================
  -- EFEITOS COLATERAIS: SÓ para estados que confirmam abordagem
  -- ============================================================
  IF p_new_status IN ('sent', 'confirmed_from_whatsapp') THEN
    -- determina o tipo de interação pela campaign_key
    v_int_type := public.interaction_type_from_campaign_key(v_row.campaign_key);

    IF v_int_type IS NULL THEN
      RETURN jsonb_build_object('outcome', 'error', 'error_code', 'unknown_interaction_type');
    END IF;

    UPDATE public.leads
       SET status = 'abordado',
           ultimo_contato_em = COALESCE(p_message_timestamp, now()),
           proximo_followup_em = CASE
                                   WHEN p_new_status = 'sent'
                                   THEN now() + interval '3 days'
                                   ELSE proximo_followup_em
                                 END,
           updated_at = now()
     WHERE id = v_row.lead_id;

    INSERT INTO public.lead_interactions
          (lead_id, tipo, canal, mensagem, observacao, created_at)
    VALUES (v_row.lead_id, v_int_type, 'whatsapp', NULL,
            COALESCE(p_obs, 'auto:' || p_new_status || ' ck=' || v_row.campaign_key),
            now());
  END IF;

  RETURN jsonb_build_object('outcome', 'settled', 'status', p_new_status);
EXCEPTION WHEN OTHERS THEN
  RETURN jsonb_build_object('outcome', 'error', 'error_code', 'settle_exception');
END;
$$;

-- ============================================================
-- 10. RPC: confirm_outreach_from_whatsapp
-- Reconciliação retroativa (sincronizador). Exige service role.
-- Idempotente; atômica; exige campaign_match = TRUE.
-- Seleção determinística de histórico (ORDER BY/LIMIT + regras).
-- ============================================================
CREATE OR REPLACE FUNCTION public.confirm_outreach_from_whatsapp(
  p_phone_normalized   TEXT,
  p_campaign_key       TEXT,
  p_lead_id            UUID,
  p_message_timestamp  TIMESTAMPTZ,
  p_fingerprint        TEXT,
  p_campaign_match     BOOLEAN,
  p_source             TEXT DEFAULT 'whatsapp_reconciliation'
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_row        public.lead_outreach%ROWTYPE;
  v_validation TEXT;
  v_action     TEXT;
  v_id         UUID;
  v_int_type   TEXT;
BEGIN
  -- validação de parâmetros
  IF p_phone_normalized IS NULL OR p_phone_normalized !~ '^\d{12,13}$' THEN
    RETURN jsonb_build_object('outcome', 'invalid_phone');
  END IF;

  IF p_campaign_key IS NULL
     OR p_campaign_key !~ '^[a-z0-9_]+:[a-z0-9_]+:[a-z0-9_]+:v[0-9]+$'
  THEN
    RETURN jsonb_build_object('outcome', 'invalid_campaign_key');
  END IF;

  IF p_lead_id IS NULL THEN
    RETURN jsonb_build_object('outcome', 'invalid_lead_id');
  END IF;

  IF p_source IS NULL OR p_source <> 'whatsapp_reconciliation' THEN
    RETURN jsonb_build_object('outcome', 'invalid_source');
  END IF;

  IF p_campaign_match IS NOT TRUE THEN
    RETURN jsonb_build_object('outcome', 'ambiguous_not_confirmed');
  END IF;

  -- validação lead/telefone/campanha no banco
  v_validation := public.validate_lead_campaign(p_lead_id, p_phone_normalized, p_campaign_key);

  IF v_validation <> 'ok' THEN
    RETURN jsonb_build_object('outcome', 'invalid_lead_match', 'reason', v_validation);
  END IF;

  -- determina o tipo de interação
  v_int_type := public.interaction_type_from_campaign_key(p_campaign_key);

  IF v_int_type IS NULL THEN
    RETURN jsonb_build_object('outcome', 'error', 'error_code', 'unknown_interaction_type');
  END IF;

  -- procura linha bloqueadora ativa (única pelo índice parcial)
  SELECT * INTO v_row
    FROM public.lead_outreach
   WHERE phone_normalized = p_phone_normalized
     AND campaign_key = p_campaign_key
     AND status IN ('reserved','sent','confirmed_from_whatsapp','needs_reconciliation')
   ORDER BY created_at DESC
   LIMIT 1
   FOR UPDATE;

  v_action := 'insert';

  IF FOUND THEN
    CASE v_row.status
      WHEN 'sent' THEN
        RETURN jsonb_build_object('outcome', 'already_confirmed');
      WHEN 'confirmed_from_whatsapp' THEN
        RETURN jsonb_build_object('outcome', 'already_confirmed');
      WHEN 'needs_reconciliation' THEN
        v_action := 'promote';
      WHEN 'reserved' THEN
        -- não roubar reserva válida; NULL de expires_at => válida
        IF v_row.reservation_expires_at IS NULL
           OR v_row.reservation_expires_at >= now()
        THEN
          RETURN jsonb_build_object('outcome', 'reserved_by_other');
        END IF;

        -- vencida: libera a bloqueadora e insere nova confirmed
        UPDATE public.lead_outreach
           SET status = 'released',
               error_code = 'stale_reclaimed_by_reconciliation',
               reservation_token = NULL,
               reservation_expires_at = NULL,
               updated_at = now()
         WHERE id = v_row.id;

        v_action := 'release_then_insert';
      ELSE
        RETURN jsonb_build_object('outcome', 'reserved_by_other');
    END CASE;
  END IF;

  -- executa a ação selecionada
  IF v_action = 'promote' THEN
    UPDATE public.lead_outreach
       SET status = 'confirmed_from_whatsapp',
           message_timestamp = COALESCE(p_message_timestamp, message_timestamp),
           message_fingerprint = COALESCE(p_fingerprint, message_fingerprint),
           campaign_match = TRUE,
           source = p_source,
           reservation_token = NULL,
           reservation_expires_at = NULL,
           updated_at = now()
     WHERE id = v_row.id;
  ELSE
    -- release_then_insert ou insert: insere nova linha confirmed
    INSERT INTO public.lead_outreach
          (lead_id, phone_normalized, campaign_key, status, source, message_direction,
           message_timestamp, message_fingerprint, campaign_match)
    VALUES (p_lead_id, p_phone_normalized, p_campaign_key, 'confirmed_from_whatsapp',
            p_source, 'outbound', p_message_timestamp, p_fingerprint, TRUE)
    ON CONFLICT (phone_normalized, campaign_key)
    WHERE status IN ('reserved','sent','confirmed_from_whatsapp','needs_reconciliation')
    DO NOTHING
    RETURNING id INTO v_id;

    IF v_id IS NULL THEN
      -- raça: outra transação criou bloqueadora
      RETURN jsonb_build_object('outcome', 'reserved_by_other');
    END IF;
  END IF;

  -- atualiza lead + interação (instrução separada, mesma transação)
  UPDATE public.leads
     SET status = 'abordado',
         ultimo_contato_em = COALESCE(p_message_timestamp, now()),
         updated_at = now()
   WHERE id = p_lead_id;

  INSERT INTO public.lead_interactions
        (lead_id, tipo, canal, mensagem, observacao, created_at)
  VALUES (p_lead_id, v_int_type, 'whatsapp', NULL,
          'reconciliation confirmed ck=' || p_campaign_key, now());

  RETURN jsonb_build_object('outcome', 'confirmed');
EXCEPTION WHEN OTHERS THEN
  RETURN jsonb_build_object('outcome', 'error', 'error_code', 'confirm_exception');
END;
$$;

-- ============================================================
-- 11. RPC: release_reconciliation
-- Libera needs_reconciliation quando comprovado que nenhuma mensagem foi enviada.
-- EM v1: NÃO Grant para anon. Uso só por fluxo manual/auditado (service_role).
-- ============================================================
CREATE OR REPLACE FUNCTION public.release_reconciliation(
  p_phone_normalized TEXT,
  p_campaign_key     TEXT,
  p_reason           TEXT DEFAULT 'manual_review'
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_row public.lead_outreach%ROWTYPE;
BEGIN
  IF p_phone_normalized IS NULL OR p_phone_normalized !~ '^\d{12,13}$' THEN
    RETURN jsonb_build_object('outcome', 'invalid_phone');
  END IF;

  IF p_campaign_key IS NULL
     OR p_campaign_key !~ '^[a-z0-9_]+:[a-z0-9_]+:[a-z0-9_]+:v[0-9]+$'
  THEN
    RETURN jsonb_build_object('outcome', 'invalid_campaign_key');
  END IF;

  SELECT * INTO v_row
    FROM public.lead_outreach
   WHERE phone_normalized = p_phone_normalized
     AND campaign_key = p_campaign_key
   ORDER BY created_at DESC
   LIMIT 1
   FOR UPDATE;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('outcome', 'not_found');
  END IF;

  IF v_row.status <> 'needs_reconciliation' THEN
    RETURN jsonb_build_object('outcome', 'invalid_transition', 'from', v_row.status);
  END IF;

  UPDATE public.lead_outreach
     SET status = 'released',
         error_code = 'released_' || p_reason,
         reservation_token = NULL,
         reservation_expires_at = NULL,
         updated_at = now()
   WHERE id = v_row.id;

  RETURN jsonb_build_object('outcome', 'released');
EXCEPTION WHEN OTHERS THEN
  RETURN jsonb_build_object('outcome', 'error', 'error_code', 'release_exception');
END;
$$;

-- ============================================================
-- 12. RPC: get_outreach_state
-- Leitura segura/limitada (sem token, sem erros internos).
-- Única RPC acessível por anon.
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_outreach_state(
  p_phone_normalized TEXT,
  p_campaign_key     TEXT
) RETURNS JSONB
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp, extensions
AS $$
DECLARE
  v_row public.lead_outreach%ROWTYPE;
BEGIN
  IF p_phone_normalized IS NULL OR p_campaign_key IS NULL THEN
    RETURN jsonb_build_object('outcome', 'invalid_args');
  END IF;

  SELECT * INTO v_row
    FROM public.lead_outreach
   WHERE phone_normalized = p_phone_normalized
     AND campaign_key = p_campaign_key
   ORDER BY created_at DESC
   LIMIT 1;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('outcome', 'none');
  END IF;

  RETURN jsonb_build_object(
    'outcome', 'found',
    'status', v_row.status,
    'campaign_match', v_row.campaign_match,
    'message_timestamp', v_row.message_timestamp
  );
  -- jamais retorna reservation_token, settlement_token_hash, error_code, source interno
END;
$$;

-- ============================================================
-- 13. VIEW: vw_telefones_conflitos
-- Relatório de telefones legados divergentes (somente leitura).
-- SEM grant para anon (contém telefone canônico e IDs de leads).
-- ============================================================
CREATE OR REPLACE VIEW public.vw_telefones_conflitos AS
SELECT
  public.normalizar_telefone_br_sql(COALESCE(l.whatsapp, l.telefone)) AS canonical_phone,
  COUNT(*)                                                              AS total_leads,
  COUNT(DISTINCT l.telefone_normalizado)                                AS distinct_normalizado,
  bool_or(l.telefone_normalizado IS NULL)                               AS algum_nulo,
  array_agg(l.id ORDER BY l.created_at)                                AS lead_ids,
  array_agg(l.telefone_normalizado ORDER BY l.created_at)               AS normalizados
FROM public.leads l
WHERE public.normalizar_telefone_br_sql(COALESCE(l.whatsapp, l.telefone)) IS NOT NULL
GROUP BY public.normalizar_telefone_br_sql(COALESCE(l.whatsapp, l.telefone))
HAVING COUNT(*) > 1
   OR COUNT(DISTINCT l.telefone_normalizado) > 1
   OR bool_or(l.telefone_normalizado IS NULL);

-- ============================================================
-- 14. RLS: SEM acesso direto para anon. Toda escrita via RPCs.
-- ============================================================
ALTER TABLE public.lead_outreach ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lead_outreach FORCE ROW LEVEL SECURITY;

REVOKE ALL ON public.lead_outreach FROM anon, authenticated;

-- ============================================================
-- 15. GRANTS E REVOKES
-- ============================================================
-- Funções internas (sem grant para anon)
REVOKE ALL ON FUNCTION public.normalizar_telefone_br_sql(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.validate_lead_campaign(UUID,TEXT,TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.outreach_transition_allowed(TEXT,TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.interaction_type_from_campaign_key(TEXT) FROM PUBLIC;

-- RPCs de escrita: apenas service_role (NÃO anon)
REVOKE ALL ON FUNCTION public.reserve_outreach(TEXT,TEXT,UUID,TEXT) FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION public.reserve_outreach(TEXT,TEXT,UUID,TEXT) TO service_role;

REVOKE ALL ON FUNCTION public.settle_outreach(UUID,UUID,TEXT,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT) FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION public.settle_outreach(UUID,UUID,TEXT,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT) TO service_role;

REVOKE ALL ON FUNCTION public.confirm_outreach_from_whatsapp(TEXT,TEXT,UUID,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT) FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION public.confirm_outreach_from_whatsapp(TEXT,TEXT,UUID,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT) TO service_role;

-- release_reconciliation: em v1 NÃO Grant para anon (só service_role)
REVOKE ALL ON FUNCTION public.release_reconciliation(TEXT,TEXT,TEXT) FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION public.release_reconciliation(TEXT,TEXT,TEXT) TO service_role;

-- RPC de leitura: anon pode consultar (sem token, sem erros internos)
REVOKE ALL ON FUNCTION public.get_outreach_state(TEXT,TEXT) FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION public.get_outreach_state(TEXT,TEXT) TO anon;

-- View de conflitos: SEM grant para anon (dados sensíveis)
REVOKE ALL ON public.vw_telefones_conflitos FROM PUBLIC;

-- ============================================================
-- ROLLBACK COMPLETO (executar em ordem reversa)
-- ============================================================
-- REVOKE EXECUTE ON FUNCTION public.get_outreach_state(TEXT,TEXT) FROM anon;
-- REVOKE EXECUTE ON FUNCTION public.release_reconciliation(TEXT,TEXT,TEXT) FROM service_role;
-- REVOKE EXECUTE ON FUNCTION public.confirm_outreach_from_whatsapp(TEXT,TEXT,UUID,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT) FROM service_role;
-- REVOKE EXECUTE ON FUNCTION public.settle_outreach(UUID,UUID,TEXT,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT) FROM service_role;
-- REVOKE EXECUTE ON FUNCTION public.reserve_outreach(TEXT,TEXT,UUID,TEXT) FROM service_role;
-- DROP FUNCTION IF EXISTS public.get_outreach_state(TEXT,TEXT);
-- DROP FUNCTION IF EXISTS public.release_reconciliation(TEXT,TEXT,TEXT);
-- DROP FUNCTION IF EXISTS public.confirm_outreach_from_whatsapp(TEXT,TEXT,UUID,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT);
-- DROP FUNCTION IF EXISTS public.settle_outreach(UUID,UUID,TEXT,TIMESTAMPTZ,TEXT,BOOLEAN,TEXT);
-- DROP FUNCTION IF EXISTS public.reserve_outreach(TEXT,TEXT,UUID,TEXT);
-- DROP FUNCTION IF EXISTS public.validate_lead_campaign(UUID,TEXT,TEXT);
-- DROP FUNCTION IF EXISTS public.outreach_transition_allowed(TEXT,TEXT);
-- DROP FUNCTION IF EXISTS public.interaction_type_from_campaign_key(TEXT);
-- DROP FUNCTION IF EXISTS public.normalizar_telefone_br_sql(TEXT);
-- DROP VIEW IF EXISTS public.vw_telefones_conflitos;
-- DROP INDEX IF EXISTS public.uq_lead_outreach_active;
-- DROP INDEX IF EXISTS public.idx_lead_outreach_phone;
-- DROP INDEX IF EXISTS public.idx_lead_outreach_status;
-- DROP INDEX IF EXISTS public.idx_lead_outreach_lead;
-- DROP TRIGGER IF EXISTS set_updated_at_lead_outreach ON public.lead_outreach;
-- DROP TABLE IF EXISTS public.lead_outreach;
