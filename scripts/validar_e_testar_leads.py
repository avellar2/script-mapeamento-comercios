#!/usr/bin/env python3
"""
Valida autenticacao do perfil persistente e testa os 4 leads inconclusivos.
NAO envia mensagens. NAO escreve no Supabase.
"""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.async_api import async_playwright
from dotenv import load_dotenv

DOTENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(DOTENV)

PROFILE_DIR = Path(r"C:\projetos\script-mapear-comercios-whatsapp-dedup\profiles\whatsapp_match")

# Lead IDs dos 4 inconclusivos
LEADS = [
    "51d1a2ba-1944-45ee-93f1-d51519b2b437",  # Erica Freire
    "a39427c6-66a6-46f4-9444-6d4c212351ac",  # Danielle Lopes Pilates
    "da373706-ad67-4377-a16c-7833761fdda4",  # Lift Life
    "7ae99928-9fd3-4455-8ddd-b33f206f70a8",  # Betapetsbr Banho e Tosa
]

async def esperar_whatsapp_carregado(page, timeout=30000):
    """Aguarda WhatsApp Web totalmente carregado."""
    try:
        await page.wait_for_selector("#side", timeout=timeout)
        await page.wait_for_selector('#side input[role="textbox"]', timeout=timeout)
        print("  [OK] #side e campo de busca carregados")
        return True
    except Exception as e:
        print(f"  [ERRO] WhatsApp nao carregou: {e}")
        return False

async def validar_autenticacao(context):
    """Valida se o perfil esta autenticado."""
    print("\n=== VALIDACAO DE AUTENTICACAO ===")
    page = await context.new_page()
    
    try:
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded", timeout=15000)
        print("  Pagina aberta")
        
        # Verifica se ha QR code
        qr = page.locator('canvas[aria-label*="QR code"], img[alt="QR code"]')
        qr_count = await qr.count()
        
        if qr_count > 0:
            print("  [QR CODE DETECTADO] Escaneie o QR Code agora")
            print("  Aguardando escaneamento...")
            # Espera o QR sumir (ate 120s)
            try:
                await qr.wait_for(state="hidden", timeout=120000)
                print("  [OK] QR Code escaneado e sumiu")
            except Exception as e:
                print(f"  [ERRO] QR Code ainda presente apos 120s: {e}")
                await page.screenshot(path="output/qr_timeout.png")
                return False
            
            # Aguarda carregamento completo
            loaded = await esperar_whatsapp_carregado(page, timeout=30000)
            if not loaded:
                return False
        else:
            print("  [OK] Sem QR Code - ja autenticado")
            # Verifica se #side existe
            try:
                await page.wait_for_selector("#side", timeout=10000)
                await page.wait_for_selector('#side input[role="textbox"]', timeout=10000)
                print("  [OK] #side e campo de busca encontrados")
            except Exception as e:
                print(f"  [ERRO] Autenticado mas elementos nao encontrados: {e}")
                return False
        
        print("  [OK] Autenticacao valida")
        return True
        
    finally:
        await page.close()

async def testar_lead(context, lead_id):
    """Testa um lead individual e retorna resultado."""
    page = await context.new_page()
    result = {
        "lead_id": lead_id,
        "chat_found": False,
        "phone_extracted": None,
        "evidence_type": None,
        "canonico_match": False,
        "outbound_found": False,
        "campaign_match": False,
        "status": "unknown",
        "tempo": 0,
        "erro": None,
    }
    
    t0 = time.time()
    
    try:
        await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded", timeout=15000)
        
        # Fecha modal se existir
        try:
            dialog = page.locator('[role="dialog"]')
            if await dialog.count() > 0:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(500)
        except:
            pass
        
        # Aguarda campo de busca
        try:
            await page.wait_for_selector('#side input[role="textbox"]', timeout=30000)
        except:
            result["status"] = "search_field_not_found"
            result["erro"] = "Campo de busca nao encontrado"
            return result
        from supabase import create_client
        supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
        resp = supabase.table("leads").select("id,nome,telefone").eq("id", lead_id).execute()
        
        if not resp.data:
            result["status"] = "lead_not_found"
            result["erro"] = "Lead nao encontrado"
            return result
        
        lead = resp.data[0]
        telefone_raw = lead.get("telefone", "")
        
        # Normaliza telefone
        from utils.phone_utils import normalizar_telefone_br, variantes_busca_telefone
        def mascarar(tel):
            if not tel or len(tel) < 4: return "***"
            return tel[:5] + "***" + tel[-4:]
        
        telefone_canonico = normalizar_telefone_br(telefone_raw)
        variantes = variantes_busca_telefone(telefone_canonico) if telefone_canonico else []
        
        result["telefone_raw"] = mascarar(telefone_canonico) if telefone_canonico else telefone_raw[:6]+"***"
        result["telefone_canonico"] = telefone_canonico
        
        if not variantes:
            result["status"] = "error"
            result["erro"] = f"Telefone invalido: {mascarar(telefone_canonico)}"
            return result
        
        variante = variantes[0]  # Usa primeira variante nacional
        
        # Pesquisa telefone
        print(f"  Buscando: {variante[:6]}...")
        search_box = page.locator('#side input[role="textbox"]')
        search_count = await search_box.count()
        print(f"  Campo busca count: {search_count}")
        
        if search_count == 0:
            result["status"] = "search_field_not_found"
            result["erro"] = "Campo de busca count=0"
            return result
        
        await search_box.first.fill(variante)
        await page.wait_for_timeout(3000)
        
        # Verifica se ha resultados
        chat_items = page.locator('[data-testid="chat-list-item"]')
        count = await chat_items.count()
        print(f"  Resultados busca: {count}")
        
        if count == 0:
            result["status"] = "no_chat"
            return result
        
        result["chat_found"] = True
        
        # Abre o primeiro resultado
        await chat_items.first.click()
        await page.wait_for_timeout(1500)
        
        # Extrai telefone do chat
        # Camada 1: Painel de informacoes
        try:
            header = page.locator('div[data-testid="conversation-panel-header"]')
            if await header.count() > 0:
                await header.first.click()
                await page.wait_for_timeout(500)
                
                # Procura telefone
                phone_el = page.locator('span[title*="+"]').first
                if await phone_el.count() > 0:
                    phone_title = await phone_el.get_attribute("title")
                    if phone_title:
                        tel_found = normalizar_telefone_br(phone_title)
                        if tel_found:
                            result["phone_extracted"] = mascarar(tel_found)
                            result["evidence_type"] = "profile"
                            result["canonico_match"] = (tel_found == telefone_canonico)
                
                # Volta
                back = page.locator('[data-testid="btn-back"]')
                if await back.count() > 0:
                    await back.first.click()
                    await page.wait_for_timeout(300)
        except Exception as e:
            result["erro"] = f"Extração perfil: {e}"
        
        # Camada 2: Link tel:
        if not result["phone_extracted"]:
            try:
                tel_links = page.locator('a[href*="tel:"]')
                if await tel_links.count() > 0:
                    href = await tel_links.first.get_attribute("href")
                    if href:
                        tel_str = href.replace("tel:", "").replace("+", "")
                        tel_found = normalizar_telefone_br(tel_str)
                        if tel_found:
                            result["phone_extracted"] = mascarar(tel_found)
                            result["evidence_type"] = "tel_link"
                            result["canonico_match"] = (tel_found == telefone_canonico)
            except:
                pass
        
        # Camada 3: aria-label
        if not result["phone_extracted"]:
            try:
                aria = page.locator('[aria-label*="+55"]')
                count = await aria.count()
                for i in range(count):
                    label = await aria.nth(i).get_attribute("aria-label")
                    if label:
                        tel_found = normalizar_telefone_br(label)
                        if tel_found:
                            result["phone_extracted"] = mascarar(tel_found)
                            result["evidence_type"] = "aria_label"
                            result["canonico_match"] = (tel_found == telefone_canonico)
                            break
            except:
                pass
        
        # Camada 4: JID
        if not result["phone_extracted"]:
            try:
                jid_els = page.locator('[data-id*="@s.whatsapp.net"]')
                count = await jid_els.count()
                for i in range(count):
                    data_id = await jid_els.nth(i).get_attribute("data-id")
                    if data_id:
                        jid_num = data_id.split("@")[0]
                        if jid_num.startswith("55"):
                            tel_found = normalizar_telefone_br(jid_num)
                            if tel_found:
                                result["phone_extracted"] = mascarar(tel_found)
                                result["evidence_type"] = "jid"
                                result["canonico_match"] = (tel_found == telefone_canonico)
                                break
            except:
                pass
        
        # Detecta outbound
        try:
            outgoing = page.locator('[data-testid="outgoing"]')
            if await outgoing.count() > 0:
                result["outbound_found"] = True
        except:
            pass
        
        # Determina status
        if result["canonico_match"] and result["outbound_found"]:
            result["status"] = "matched"
        elif result["canonico_match"] and not result["outbound_found"]:
            result["status"] = "no_outbound"
        elif result["chat_found"] and not result["canonico_match"]:
            result["status"] = "ambiguous_contact"
        elif not result["chat_found"]:
            result["status"] = "no_chat"
        else:
            result["status"] = "unknown"
        
        result["tempo"] = round(time.time() - t0, 1)
        
        return result
        
    except Exception as e:
        result["status"] = "error"
        result["erro"] = str(e)[:100]
        result["tempo"] = round(time.time() - t0, 1)
        return result
    finally:
        await page.close()

async def main():
    print("=" * 60)
    print("VALIDACAO DE AUTENTICACAO + TESTE DOS 4 LEADS")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Abre contexto persistente
        print(f"\nAbrindo perfil: {PROFILE_DIR}")
        context = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        
        # Valida autenticacao
        auth_ok = await validar_autenticacao(context)
        
        if not auth_ok:
            print("\n[ERRO] Autenticacao falhou. Corrija antes de continuar.")
            await context.close()
            return
        
        # Testa persistencia (fecha e abre novamente)
        print("\n=== TESTE DE PERSISTENCIA ===")
        await context.close()
        
        context2 = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        
        page_test = await context2.new_page()
        try:
            await page_test.goto("https://web.whatsapp.com/", wait_until="domcontentloaded", timeout=15000)
            qr = page_test.locator('canvas[aria-label*="QR code"], img[alt="QR code"]')
            if await qr.count() > 0:
                print("  [ERRO] QR Code apareceu novamente - sessao nao persistiu")
                await context2.close()
                return
            await page_test.wait_for_selector("#side", timeout=10000)
            print("  [OK] Sessao persistiu - sem QR Code")
        finally:
            await page_test.close()
        
        # Testa os 4 leads
        print("\n=== TESTE DOS 4 LEADS ===\n")
        
        resultados = []
        for lead_id in LEADS:
            print(f"Testando lead: {lead_id[:8]}...")
            res = await testar_lead(context2, lead_id)
            resultados.append(res)
            
            # Mostra resultado
            status_icon = "✓" if res["status"] in ("matched", "no_outbound") else "?"
            print(f"  {status_icon} Status: {res['status']}")
            print(f"  Chat: {res['chat_found']} | Phone: {res['phone_extracted']} | Evid: {res['evidence_type']}")
            print(f"  Canonico: {res['canonico_match']} | Outbound: {res['outbound_found']}")
            print(f"  Tempo: {res['tempo']}s")
            if res.get("erro"):
                print(f"  Erro: {res['erro']}")
            print()
            
            # Pausa entre leads
            await asyncio.sleep(2)
        
        await context2.close()
        
        # Relatorio final
        print("\n" + "=" * 60)
        print("RELATORIO FINAL")
        print("=" * 60)
        
        for i, res in enumerate(resultados):
            print(f"\n{i+1}. Lead: {LEADS[i][:8]}...")
            print(f"   Status: {res['status']}")
            print(f"   Chat encontrado: {res['chat_found']}")
            print(f"   Telefone extraido: {res.get('phone_extracted', 'N/A')}")
            print(f"   Tipo evidência: {res.get('evidence_type', 'N/A')}")
            print(f"   Igualdade canônica: {res['canonico_match']}")
            print(f"   Outbound: {res['outbound_found']}")
            print(f"   Campaign match: {res['campaign_match']}")
            print(f"   Tempo: {res['tempo']}s")
        
        matched = [r for r in resultados if r["campaign_match"]]
        if matched:
            print(f"\n\nCANDIDATOS PARA APPLY: {len(matched)}")
            for r in matched:
                print(f"  - {r['lead_id'][:8]}... ({r['status']})")
        else:
            print("\n\nNenhum lead com campaign_match=true")

if __name__ == "__main__":
    asyncio.run(main())
