#!/usr/bin/env python3
"""Descobre automaticamente um controle positivo no WhatsApp Web"""
import os, sys, json, time, re
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
PROFILE = BASE / "profiles" / "whatsapp_match"
OUTPUT = BASE / "output" / "avgestao" / "sincronizador" / "controle_positivo"
OUTPUT.mkdir(parents=True, exist_ok=True)

# Limpar locks
for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
    p = PROFILE / lock
    if p.exists(): p.unlink()

print("=" * 60)
print("  CONTROLE POSITIVO - Descoberta automatica")
print("=" * 60)

with sync_playwright() as pw:
    browser = pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        viewport={"width": 1000, "height": 800},
        locale="pt-BR",
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)

    # Verificar login
    bt = page.inner_text("body", timeout=5000).lower()[:200]
    if "escaneie" in bt or "conectar" in bt:
        print("⚠️ QR Code! Escaneie no celular...")
        for _ in range(60):
            time.sleep(5)
            bt = page.inner_text("body", timeout=5000).lower()[:200]
            if "escaneie" not in bt and "conectar" not in bt:
                print("✅ Conectado!")
                break
        else:
            print("❌ QR nao escaneado")
            browser.close()
            sys.exit(1)

    print("✅ WhatsApp Web autenticado")
    
    # Listar conversas recentes
    time.sleep(3)
    
    # Tentar encontrar conversas individuais com mensagens de saida
    # Procurar por elementos de chat na lista
    chats = page.locator('div[data-testid="chat-list"] > div')
    chat_count = chats.count()
    print(f"Conversas visiveis: {chat_count}")
    
    encontrado = False
    for i in range(min(chat_count, 15)):
        try:
            chat = chats.nth(i)
            chat_text = chat.inner_text(timeout=3000)
            chat.click()
            time.sleep(2)
            
            # Verificar se eh conversa individual (nao grupo)
            # Grupos tem "você" ou "voce" nas mensagens
            body_text = page.inner_text("body", timeout=5000).lower()
            
            # Verificar se tem mensagem de saida
            # Mensagens enviadas tem o texto da mensagem
            # Procurar por mensagens que comecam com "Boa tarde" ou "Aqui é"
            msg_area = page.locator('[data-testid="conversation-panel-messages"]')
            if msg_area.count() > 0:
                msgs = msg_area.inner_text(timeout=5000)
                # Verificar se tem mensagem de saida (nao eh grupo vazio)
                if len(msgs.strip()) > 20:
                    # Tentar extrair telefone do painel de info
                    # Clicar no nome do contato no topo
                    header = page.locator('header')
                    if header.count() > 0:
                        header.first.click()
                        time.sleep(2)
                        
                        # Procurar telefone no painel
                        panel_text = page.inner_text("body", timeout=5000)
                        phone_match = re.search(r'(55\d{2})\d{4,5}\d{4}', panel_text)
                        if phone_match:
                            phone_full = phone_match.group(0)
                            phone_masked = phone_full[:4] + "****" + phone_full[-4:]
                            print(f"\n✅ Controle positivo encontrado!")
                            print(f"   Chat #{i+1}")
                            print(f"   Telefone mascarado: {phone_masked}")
                            print(f"   Primeiras linhas da conversa: {msgs[:100]}...")
                            
                            # Salvar diagnostico
                            diag = {
                                "chat_index": i,
                                "phone_masked": phone_masked,
                                "phone_variant": phone_full,
                                "has_outbound": True,
                                "status": "confirmed"
                            }
                            (OUTPUT / "controle_positivo.json").write_text(json.dumps(diag, indent=2))
                            
                            # Salvar variavel de ambiente para o matcher
                            os.environ["WHATSAPP_MATCH_TEST_PHONE"] = phone_full
                            
                            encontrado = True
                            break
                        else:
                            print(f"   Chat #{i+1}: sem telefone no painel, tentando outro...")
                            # Fechar painel
                            page.keyboard.press("Escape")
                            time.sleep(1)
                    else:
                        print(f"   Chat #{i+1}: sem header")
                else:
                    print(f"   Chat #{i+1}: conversa vazia")
            else:
                print(f"   Chat #{i+1}: sem painel de mensagens")
        except Exception as e:
            print(f"   Chat #{i+1}: erro - {str(e)[:50]}")
            continue
    
    if not encontrado:
        print("\n❌ Nenhum controle positivo encontrado em 15 conversas")
        # Salvar diagnostico
        page.screenshot(path=str(OUTPUT / "falha_controle_positivo.png"))
        (OUTPUT / "controle_positivo.json").write_text(json.dumps({"status": "not_found", "chats_checked": min(chat_count, 15)}))
    
    browser.close()

if encontrado:
    print("\n✅ Controle positivo salvo em output/avgestao/sincronizador/controle_positivo/")
else:
    print("\n❌ Falha no controle positivo")
