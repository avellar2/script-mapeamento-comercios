# WhatsApp Match Validation Workflow

## Ordem de execução

1. **Verificar sessão ativa** — antes de qualquer teste, confirme que o WhatsApp está autenticado
2. **Executar controle positivo** — `scripts/validar_controle_positivo.py` ou `scripts/controle_positivo_tecm.py`
3. **Dry-run pequeno** — `sincronizar_abordados_whatsapp.py --dry-run --limit 10`
4. **Dry-run completo** — sem `--limit`

## Sessão ativa vs. expirada

**Sessão ativa:** `launch_persistent_context` abre direto no WhatsApp, `#side` visível em ~2s.
**Sessão expirada:** QR code visível, `wait_for_selector("#side")` timeout em 30s, todos os leads retornam `login_required`.

Se a sessão expirou:
1. Escaneie o QR code na janela que o Playwright abriu
2. Aguarde até `#side` aparecer
3. Rode os scripts normalmente

**PITFALL:** `launch_persistent_context` abre uma instância Chromium ISOLADA — não compartilha sessão com abas WhatsApp já abertas no Chrome normal. Se o QR code expirou, escanear NA JANELA DO PLAYWRIGHT, não no Chrome normal.

## Scripts de validação

Located at: `C:\projetos\script-mapear-comercios-whatsapp-dedup\scripts\`

| Script | Uso |
|---------|-----|
| `controle_positivo_tecm.py` | Abre WhatsApp, aguarda até 5min por QR code, testa TECM |
| `validar_controle_positivo.py` | Requer WhatsApp já autenticado; testa TECM direto |
| `repetir_4_leads_v2.py` | Testa 4 leads específicos (Érica, Danielle, Lift Life, Betapetsbr) |
| `diagnostico_busca.py` | Testa se campo de busca funciona após fechar modal |

## Expected results

| Resultado | Significado |
|-----------|-------------|
| `matched` | Telefone confirmado no painel de informações |
| `ambiguous_contact` | Chat encontrado por nome, mas número não confirmou em nenhuma camada |
| `no_chat` | Busca não encontrou conversa |
| `search_field_not_found` | Campo de busca bloqueado por modal ou DOM mudou |
| `login_required` | Sessão expirada (QR code) |

## Failure modes

- `login_required` → Escaneie QR code na janela do Playwright
- `search_field_not_found` → Fecha modal "As etiquetas agora são as Listas" com Escape; se persistir, DOM mudou
- `ambiguous_contact` → Estado **correto** quando o chat existe mas o número no WhatsApp não bate com o canônico do lead — não forçar confirmação
- `no_chat` → Lead genuinamente sem conversa no WhatsApp

## Nota sobre `ambiguous_contact`

Este não é um estado de erro — é o comportamento esperado quando:
- O contato está no WhatsApp com outro número salvo
- O nome é o mesmo mas o telefone é diferente
- O número do lead mudou no celular do contato

**Não forçar confirmação.** Manter `ambiguous_contact` evita falsos positivos na reconciliação de campaign_match.
