# WhatsApp Matcher Optimization

Técnicas para otimizar o matcher de conversas no WhatsApp Web (playwright-based).
Reduziu tempo de ~94s/lead para ~10-14s/lead sem perder confiabilidade.

## Problemas Identificados

1. **TIMEOUT_CURTO = 5000ms** — cada `encontrar_seletor()` esperava 5s por seletor. Com 8+ seletores por etapa, pior caso = 40s+ só em seletores não encontrados.
2. **8 variantes de telefone** — `variantes_busca_telefone()` gerava +55, 55, DDD, formato visual, sem nono, com nono. Cada variante = 1 busca completa. Para leads sem conversa: 8 × ~7s = ~56s.
3. **Esperas sequenciais em `abrir_conversa()`** — 1.5s fixo + loading 5s + header 5s = ~26s.
4. **`detectar_grupo()` esperava 5s por cada indicador** — 6 indicadores × 5s = 30s no pior caso.
5. **`detectar_mensagem_saida()` não encontrava outbound** — dependia de `wait_for_selector` com 5s timeout.

## Soluções

### 1. Reduzir timeouts

```python
TIMEOUT_CURTO = 1000     # was 5000
TIMEOUT_RAPIDO = 500     # novo, para checks instantâneos
```

### 2. `encontrar_seletor_rapido()` — count() antes de wait_for_selector

```python
async def encontrar_seletor_rapido(page, selectors, timeout=500):
    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = await locator.count()  # instantâneo se elemento já existe
            if count > 0:
                return selector
            # Só espera se count=0
            el = await page.wait_for_selector(selector, timeout=timeout)
            if el:
                return selector
        except Exception:
            continue
    return None
```

### 3. Variantes de telefone: 8 → 1

Usar UMA variante nacional: `DDD + número` (sem 55, sem +).
- Celular: 11 dígitos (DDD + 9 dígitos)
- Fixo: 10 dígitos (DDD + 8 dígitos)
- Telefone inválido: rejeitar (lista vazia), não pesquisar

```python
def variantes_busca_telefone(tel: str) -> list[str]:
    if not tel or not tel.startswith("55") or len(tel) < 12:
        return []
    ddd_numero = tel[2:]
    if len(ddd_numero) not in (10, 11):
        return []
    if not _validar_ddd(ddd_numero):
        return []
    return [ddd_numero]  # UMA variante
```

### 4. Espera composta em `abrir_conversa()` — asyncio.gather

Em vez de esperar sequencialmente header (5s) + mensagens (5s) + loading (5s):
disparar as 3 esperas em paralelo com orçamento global de 8s.

```python
await asyncio.wait_for(
    asyncio.gather(wait_header(), wait_messages(), wait_loading_gone()),
    timeout=8.0
)
```

### 5. `detectar_grupo()` — count() imediato

Testar todos os indicadores com `count()` (instantâneo). Classifica tipo:
- `community` → MatchStatus.COMMUNITY
- `channel` → MatchStatus.CHANNEL
- `group` → MatchStatus.GROUP

### 6. `detectar_mensagem_saida()` — DOM real + fallback JS

Camada 1: `count()` nos seletores CSS (`data-testid*="out"`, `message-out`).
Camada 2: Fallback JS que inspeciona o DOM real:

```javascript
() => {
    const outMsgs = document.querySelectorAll(
        'div[data-testid*="out"], div.message-out, div[class*="message-out"]'
    );
    if (outMsgs.length > 0) return outMsgs.length;
    // Fallback: container com justify-content: flex-end
    const panels = document.querySelectorAll(
        'div[data-testid="conversation-panel-messages"] > div'
    );
    for (const panel of panels) {
        const style = window.getComputedStyle(panel);
        if (style.justifyContent === 'flex-end') return 1;
    }
    return 0;
}
```

### 7. Early exit global

- Conversa encontrada → não testar variantes restantes
- Telefone confirmado → não testar seletores restantes
- Outbound encontrado → parar imediatamente
- Grupo/canal confirmado → retornar status específico

### 8. Instrumentação de tempos

Cada etapa mede tempo separado e armazena em `result.timings`:

```python
timings = {
    "search": 1.16,
    "group_detect": 0.02,
    "open_chat": 7.25,
    "confirm_phone": 5.31,
    "outbound_detect": 0.01,
    "fingerprint": 0.00,
    "total": 13.74
}
```

## Resultados Medidos

| Métrica | Antes | Depois |
|---------|-------|--------|
| Controle positivo (TECM) | ~94s | 13.71s |
| Dry-run sem conversa (por lead) | ~66s | ~10s |
| Variantes por lead | 8 | 1 |
| Timeout por seletor | 5s | 1s / 500ms |

## Perfil do WhatsApp

Usar `profiles/whatsapp_match` (não o perfil de envio).
Autenticação via QR Code — aguardar campo de busca `#side input[role="textbox"]` aparecer.

## Commits Relevantes

- `f49169e` — otimização inicial (timeout, count(), espera composta, early exit)
- `19555c2` — variante única nacional (8→1)
- Branch: `feat/protecao-duplicidade-whatsapp`