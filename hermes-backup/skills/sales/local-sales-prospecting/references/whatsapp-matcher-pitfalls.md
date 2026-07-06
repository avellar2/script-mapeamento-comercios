# WhatsApp Matcher — Pitfalls & Correções

## 1. Perfil bloqueado por Chrome anterior

Se um processo Chrome/Chromium anterior ainda está rodando com `profiles/whatsapp_match`, o Playwright crasha ao tentar abrir (`exitCode=21`).

**Solução:** antes de iniciar o sincronizador, verificar:
```bash
wmic process where "name='chrome.exe'" get processid,commandline | grep whatsapp_match
```
Encerrar o processo antigo:
```bash
taskkill //F //PID <PID>
```
Aguardar 3s antes de reabrir.

## 2. Lock do sincronizador preso após SIGTERM

Após matar o processo do sincronizador, o arquivo `output/avgestao/whatsapp_match.lock` pode ficar preso.

**Solução:**
```bash
rm -f output/avgestao/whatsapp_match.lock
```

## 3. Buffer do Python sem saída em tempo real

O `sincronizar_abordados_whatsapp.py` usa `logging` que faz buffer. Se o processo demorar, o output pode não aparecer por minutos.

**Solução:** executar com:
```bash
PYTHONUNBUFFERED=1 python -u sincronizar_abordados_whatsapp.py ...
```

## 4. Modal "As etiquetas agora são as Listas"

Popup de marketing do WhatsApp com `role="dialog" aria-modal="true"` e `data-testid="confirm-popup"` que intercepta pointer events.

**Estratégia de fechamento (em ordem):**
1. Escape
2. Seletores CSS com aria-label seguro (Fechar, Close, OK, Continuar, etc.)
3. Ícone X (`data-icon="x"`/`"close"`) dentro do `confirm-popup`
4. JavaScript fallback com allowlist de textos seguros
5. Se persistir → `modal_blocked`

**REGRAS DE SEGURANÇA:**
- Nunca clicar no primeiro botão visível como fallback
- Nunca clicar em botão sem texto/aria-label/data-testid conhecido
- Nunca clicar em: Enviar, Apagar, Excluir, Bloquear, Denunciar, Sair, Desconectar
- Só considerar fechado quando `dialog.count() == 0`
- Exigir correspondência POSITIVA com allowlist — não usar `:not()` como único filtro

## 5. `extrair_telefone_confirmado_chat` com modal ativo

Antes de clicar no header para abrir o painel de informações, o código verifica se existe modal. Se sim, tenta fechar. Se não conseguir, retorna `modal_blocked` imediatamente (timeout de 5s no header click, não 30s).

## 6. Variante de busca obrigatória

O campo de busca do WhatsApp Web aceita APENAS o formato nacional (DDD+número, sem +55). Passar `5521991312099` retorna 0 resultados.

Sempre usar:
```python
from utils.phone_utils import variantes_busca_telefone
variantes = variantes_busca_telefone("5521991312099")  # → ["21991312099"]
```

## 7. `mascarar_telefone` não existe

Em `utils/phone_utils.py` só existem: `normalizar_telefone_br`, `variantes_busca_telefone`, `gerar_link_whatsapp`, `extrair_telefone_lead`.

Para mascarar inline:
```python
tel[:5] + "***" + tel[-4:]
```

## 8. `confirmar_numero` retorna 3 valores

A partir do commit `af71eb6`, `confirmar_numero()` retorna `(bool, Optional[str], str)` — o terceiro valor é o tipo de evidência:
- `"phone_profile"` — número explícito no painel de informações
- `"tel_link"` — link `tel:` no painel
- `"aria_label"` — aria-label contendo telefone
- `"jid"` — JID no DOM
- `"modal_blocked"` — modal persistente bloqueou a extração
- `"none"` — não foi possível confirmar

## 9. Sequência correta para iniciar dry-run

1. Verificar se não há Chrome rodando com o perfil `whatsapp_match`
2. Verificar se não há Python rodando o sincronizador
3. Remover `whatsapp_match.lock` se existir
4. Confirmar que `.env` tem `SUPABASE_URL` e `SUPABASE_ANON_KEY`
5. Executar com `PYTHONUNBUFFERED=1 python -u sincronizar_abordados_whatsapp.py --dry-run --resume --limit N`

## 10. Ciclo de vida do navegador

O `setup_playwright()` reutiliza o navegador em todo o lote:
- `launch_persistent_context` chamado UMA ÚNICA VEZ
- Reutiliza página já aberta em `web.whatsapp.com`
- Fecha `about:blank` após confirmar WhatsApp ativo
- Limpa campo de busca entre leads com `limpar_campo_busca()`
- Context e page fechados somente no `finally`

**Verificação:** usar `scripts/dry_run_lifecycle.py` que registra métricas de ciclo de vida.
