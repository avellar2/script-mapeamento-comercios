# Tabelas principais
- `leads`: fonte da verdade dos leads. Campos: id, nome, telefone, telefone_normalizado, whatsapp, status, score, nicho, produto, grupo, subnicho, cidade, bairro, etc. Confidence: 0.95
- `lead_outreach`: protecao contra duplicidade, reservas, tokens e TTL. Constraint UNIQUE parcial (phone_normalized, campaign_key) WHERE status ativo. Confidence: 0.95
- `lead_interactions`: trilha de auditoria de interacoes (importacao, abordagem, follow_up, resposta, proposta, convertido, perdido). Confidence: 0.95
- `emails_enviados`: tracking de e-mail com pixel de abertura. Confidence: 0.95
- `campaigns`: registro de importacoes. Confidence: 0.90

# RPCs de escrita (apenas service_role)
- `reserve_outreach(phone, campaign_key, lead_id, source)`: reserva atomica com token de posse, TTL 30min, UNIQUE ON CONFLICT, valida lead/telefone/campanha. Confidence: 0.95
- `settle_outreach(reservation_id, token, new_status, ...)`: finalizacao atomica, retry-idempotente (hash do token), atualiza lead status + cria interacao, transicao de estados validada. Confidence: 0.95
- `confirm_outreach_from_whatsapp(...)`: reconciliacao retroativa para sincronizador, idempotente. Confidence: 0.90

# RPC de leitura
- `get_outreach_state(phone, campaign_key)`: consulta segura de estado (sem token, sem erros internos). Confidence: 0.90

# Funcoes auxiliares (SECURITY DEFINER)
- `normalizar_telefone_br_sql(TEXT)`: espelho SQL da normalizacao Python. Confidence: 0.85
- `validate_lead_campaign(UUID, TEXT, TEXT)`: valida lead_id + telefone + campaign_key. Confidence: 0.85
- `outreach_transition_allowed(TEXT, TEXT)`: maquina de estados de transicao. Confidence: 0.85

# Views
- `vw_leads_para_abordar`: leads com status novo/pronto_para_enviar. Confidence: 0.85
- `vw_followups_hoje`: follow-ups pendentes ate hoje. Confidence: 0.85
- `vw_telefones_conflitos`: relatorio de telefones legados divergentes. Confidence: 0.85

# Seguranca
- RLS habilitado em todas as tabelas. Confidence: 0.90
- lead_outreach sem acesso anon (toda escrita via RPCs SECURITY DEFINER com service_role). Confidence: 0.95
- Nao inventar RPC inexistente. Investigar schema e codigo antes de propor solucao. Confidence: 0.90
- Sempre preservar atomicidade das operacoes de reserva/settle. Confidence: 0.95
- Status validos de outreach: reserved, sent, confirmed_from_whatsapp, failed, released, needs_reconciliation. Confidence: 0.90
- Transicoes de estado controladas por outreach_transition_allowed. Confidence: 0.85
