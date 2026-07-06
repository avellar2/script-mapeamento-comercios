# WhatsApp Web Selector Patterns (Live DOM)

## Search Box
```
#side input[role="textbox"]
#side [aria-label*="Pesquisar" i]
#side [aria-label*="Search" i]
div[contenteditable="true"][data-tab="3"]
```

## Chat Items
```
div[data-testid="chat-list-item"]
div[role="row"][tabindex="-1"]
```

## Conversation Header
```
div[data-testid="conversation-header"]
header[data-testid="conversation-header"]
```

## Phone in Profile
```
div[data-testid="info-panel"] span[title*="+"]
span[title*="+55"]
```

## Outbound Messages (priority order)
```
div[data-testid*="out"]          # data-testid containing "out"
div.message-out                   # explicit class
div[class*="message-out"]         # partial class match
```

## Group/Channel/Community Indicators
```
div[data-testid="group-icon"]
div[data-testid="community-icon"]
div[data-testid="channel-icon"]
span[data-testid="icon-group"]
```

## Loading Indicators
```
div[data-testid="conversation-loading"]
div[role="progressbar"]
```

## Back Button
```
button[aria-label*="voltar" i]
button[aria-label*="back" i]
div[data-testid="btn-back"]
```

## QR Code / Login Screen
```
canvas[aria-label*="escaneie" i]
div[data-testid="qrcode"]
```

## Dialog/Modal (Marketing Popup — "As etiquetas agora são as Listas")
```
div[role="dialog"][aria-modal="true"]
div[data-testid="confirm-popup"]
```

**Botões seguros para fechar:** `Fechar`, `Close`, `OK`, `Continuar`, `Agora não`, `Not now`, `Mais tarde`, `Maybe later`
**NUNCA clicar:** `Enviar`, `Delete`, `Block`, `Report`
**Primeira opção:** `Escape` via `page.keyboard.press("Escape")`

## Performance Notes

- WhatsApp Web DOM changes frequently — centralize ALL selectors in one file
- `count()` is instant (~0ms) vs `wait_for_selector` (up to timeout)
- Composite waits (`asyncio.gather`) beat sequential waits
- Early exit at every stage saves cumulative seconds
- Never depend on delivery icons (check/double-check) for outbound detection — use DOM structure
