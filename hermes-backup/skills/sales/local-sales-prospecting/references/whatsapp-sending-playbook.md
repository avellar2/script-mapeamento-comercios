# WhatsApp Sending Playbook via Playwright

## Overview

Envio de mensagens WhatsApp automaticamente via Playwright. Requer perfil autenticado no WhatsApp Web.

## Dois perfis

- `.whatsapp_profile/` — extração de histórico (WhatsApp pessoal)
- `.whatsapp_business_profile/` — envio de mensagens (WhatsApp Business) ← USAR ESTE

## Fluxo Completo de Envio (testado e confirmado em 2025-06-05)

### Sequência que funcionou

1. Limpar locks residuais antes de iniciar
2. Abrir WhatsApp Web (home) e verificar se está logado
3. Se não logado, aguardar escaneamento do QR Code
4. Navegar para URL de envio com mensagem pré-preenchida
5. Clicar no botão `aria-label="Enviar"` (único seletor que funcionou)

### Passo 1: Limpar lock files e abrir navegador

```python
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import quote
import time

# Limpar locks residuais (evita Chromium crash)
for lock in ['SingletonLock', 'SingletonCookie', 'SingletonSocket']:
    p = Path(f'.whatsapp_business_profile/{lock}')
    if p.exists():
        p.unlink()

PROFILE_DIR = Path('.whatsapp_business_profile')

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
        viewport={'width': 800, 'height': 900},
        locale='pt-BR',
    )
    page = browser.pages[0]

    # Primeiro: abrir home e verificar sessão
    page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=90000)
    time.sleep(5)

    page_text = page.inner_text('body')
    if 'escaneie' in page_text.lower() or 'conectar' in page_text.lower():
        print("Sessão expirou. Aguardando QR Code...")
        for i in range(36):
            time.sleep(5)
            page_text = page.inner_text('body')[:200].lower()
            if 'escaneie' not in page_text and 'conectar' not in page_text:
                print(f"Conectado após {(i+1)*5}s!")
                break
```

### Passo 2: Navegar para conversa com mensagem pré-preenchida

```python
    tel = '5521968410983'
    msg = 'Olá, tudo bem? Vi sua pizzaria no Google...'
    url = f'https://web.whatsapp.com/send?phone={tel}&text={quote(msg)}'
    page.goto(url, wait_until='networkidle', timeout=60000)
    time.sleep(8)
```

### Passo 3: Clicar no botão enviar

O único seletor que funcionou na sessão de 2025-06-05 foi `button[aria-label="Enviar"]`. O `data-testid="send"` NÃO existe na versão atual do WhatsApp Web.

```python
    # Verificar o estado da página
    page_text = page.inner_text('body')[:300]
    print(f"Página: {page_text}")

    # Listar botões disponíveis (debug)
    for btn in page.locator('button').all()[:15]:
        try:
            print(f"  btn: aria={btn.get_attribute('aria-label')} testid={btn.get_attribute('data-testid')}")
        except:
            pass

    # Clicar no botão enviar
    send_btn = page.locator('button[aria-label="Enviar"]')
    if send_btn.count() > 0:
        send_btn.first.click()
        print("Mensagem enviada!")
    else:
        # Fallback: clicar na caixa de texto e pressionar Enter
        editable = page.locator('div[contenteditable="true"]')
        if editable.count() > 0:
            editable.first.click()
            page.keyboard.press('Enter')
            print("Mensagem enviada via Enter!")
        else:
            print("ERRO: Não encontrou elemento de envio")

    time.sleep(3)
    browser.close()
```

## Armadilhas

### wa.me NÃO funciona para envio automatizado

`https://wa.me/{tel}?text={msg}` redireciona para página intermediária "Compartilhe no WhatsApp" que não tem a caixa de texto nem permite envio programático. SEMPRE usar `web.whatsapp.com/send?phone={tel}&text={quote(msg)}`.

### Sessão expira frequentemente

Se a página mostrar "Escaneie para entrar", a sessão expirou.

### Chromium crash com lock files

```bash
taskkill /F /IM chrome.exe 2>/dev/null
rm -f .whatsapp_business_profile/SingletonLock
rm -f .whatsapp_business_profile/SingletonCookie
rm -f .whatsapp_business_profile/SingletonSocket
```

### Sessão estabelecida (2025-06-05)

Perfil `.whatsapp_business_profile` conectado com sucesso. Envio automático deve funcionar até expirar.

### Home-check antes de enviar

Sempre abrir primeiro `https://web.whatsapp.com` e verificar se está logado antes de navegar para a URL de envio.直接.navigate para `web.whatsapp.com/send?phone=...` sem verificar a sessão pode resultar em página em branco ou erro.

---

## Lendo Mensagens Recebidas

### Fluxo para ler respostas

```python
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

PROFILE = Path('.whatsapp_business_profile')

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=False,
        args=['--no-sandbox'],
        viewport={'width': 900, 'height': 900},
        locale='pt-BR',
    )
    page = browser.pages[0]

    # Navegar para conversa específica
    tel = '5521968410983'
    page.goto(f'https://web.whatsapp.com/send?phone={tel}', wait_until='networkidle', timeout=60000)
    time.sleep(5)

    # Scrollar para carregar todas as mensagens
    page.evaluate('document.querySelector("[data-testid=conversation-panel-messages]").scrollTop = 9999999')
    time.sleep(2)

    # Pegar todo o texto da conversa
    conversa = page.locator('[data-testid="conversation-panel-messages"]')
    texto = conversa.inner_text()
    print(texto)
```

### Sinais de resposta

| Tipo | Exemplos |
|------|---------|
| **Positiva** | "sim manda", "pode", "quero ver", "como funciona", "quanto custa", "tenho interesse", "tenho dúvidas" |
| **Negativa** | "não preciso", "já tenho", "não tenho interesse", "não quero" |
| **Neutra** | "mais informações", "me explica", "o que é", "não entendi" |

### Exemplo real (2025-06-06)

Lead respondeu: **"Eu tenho dúvidas, como seria? E o preço?"** — resposta positiva. Fluxo seguido: seguir para Instagram → fotos → LP → vídeo → WhatsApp.

### Limitações

- `inner_text()` retorna apenas o texto visível (scrollar para carregar mais)
- Imagens/PDFs aparecem como marcadores no texto
- Mensagens apagadas aparecem como "Mensagem apagada"
