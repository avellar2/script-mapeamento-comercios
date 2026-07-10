#!/usr/bin/env python3
"""
Extrai historio de conversas do WhatsApp Web (Business).

Objetivo: coletar telefones de contatos ja abordados via WhatsApp
para importar no Supabase como historio de abordagem.

SEGURANCA:
- Apenas le dados, nao envia nem modifica nada.
- Nao clica em botoes de envio, nao responde, nao arquiva.
- Gera CSV para revisao antes de qualquer importacao.
- Nunca envia mensagens automaticamente.

PERFIL SEPARADO:
- Usa .whatsapp_business_profile/ por padrao (WhatsApp Business)
- Nao mistura com o WhatsApp pessoal
- O perfil deve estar logado no numero comercial
- Na primeira vez, escaneie o QR Code com o WhatsApp Business

Uso:
    python extrair_historico_whatsapp.py --limite 50
    python extrair_historico_whatsapp.py --limite 10
    python extrair_historico_whatsapp.py --limite 10 --perfil .whatsapp_business_profile
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

# Lock global do perfil compartilhado .whatsapp_business_profile.
# Este script é SOMENTE LEITURA (não envia, não clica em Enviar, não digita em
# contenteditable) — mas usa o mesmo perfil dos senders, então deve adquirir o
# mesmo lock para não disputar o Chromium com um sender ativo.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.lock_whatsapp_sender import LockWhatsAppSender


# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

OUTPUT_DIR = Path("output/whatsapp")
PROFILE_DIR = Path(".whatsapp_business_profile")
CHAT_LIST_SELECTOR = 'div[data-testid="chat-list"] >> xpath=./div[contains(@class,"copyable-area")]/div[2]//div[@aria-label]'
CHAT_ITEM_SELECTOR = 'div[data-testid="chat-list-item"]'
CONTACT_NAME_SELECTOR = 'span[data-testid="conversation-info-header-chat-title"]'
PHONE_FROM_PROFILE_SELECTOR = 'div[data-testid="panel-header-title"] span[title*="+"]'


def normalizar_telefone_br(valor: str) -> str | None:
    """Normaliza telefone para formato 5521XXXXXXXXX."""
    if not valor:
        return None
    numeros = re.sub(r"\D", "", str(valor))
    if not numeros:
        return None
    # Se já começa com 55 e tem 12+ dígitos, mantém
    if numeros.startswith("55") and len(numeros) >= 12:
        return numeros
    # Remove 0 inicial se existir
    if numeros.startswith("0"):
        numeros = numeros[1:]
    # Celular com DDD (11 dígitos) → prepend 55
    if len(numeros) == 11:
        return "55" + numeros
    # Fixo com DDD (10 dígitos) → prepend 55
    if len(numeros) == 10:
        return "55" + numeros
    return None


def ler_telefone_da_conversa(page) -> str | None:
    """Abre perfil da conversa e tenta extrair o telefone."""
    try:
        # Clica no header do chat (nome do contato) para abrir perfil
        header = page.locator('div[data-testid="conversation-header"]')
        if header.count() == 0:
            return None
        header.click(timeout=3000)
        time.sleep(0.5)

        # Procura o botão de info do perfil
        info_btn = page.locator('[data-testid="info-panel"]').first
        if info_btn.count() > 0:
            info_btn.click(timeout=3000)
            time.sleep(0.8)

        # Tenta encontrar telefone no painel de perfil
        phone_elem = page.locator('span[title*="+"]').first
        if phone_elem.count() > 0:
            phone_text = phone_elem.get_attribute("title")
            if phone_text:
                return normalizar_telefone_br(phone_text)

        # Tenta fechar o painel com ESC
        page.keyboard.press("Escape")
        time.sleep(0.3)
        return None
    except Exception:
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        return None


def extrair_historico(limite: int, perfil: Path, headless: bool) -> tuple[list, list]:
    """
    Abre WhatsApp Web, extrai até `limite` conversas.
    Retorna (leads_com_telefone, contatos_sem_numero).
    """
    leads = []
    sem_numero = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(perfil),
            headless=headless,
            args=[
                "--no-sandbox",
            ],
            viewport={"width": 1280, "height": 800},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

        # Aguarda QR Code ou chats carregarem
        print()
        print("Aguardando WhatsApp Business Web carregar...")
        print("   Se pedir QR Code, escaneie com o WhatsApp Business.")
        print("   Se ja logou antes, apenas aguarde os chats carregarem.")
        print()

        try:
            # Espera ate aparecer lista de conversas (3 minutos para escanear QR)
            print("Aguardando ate 3 minutos...\n")
            page.wait_for_selector(
                'div[data-testid="chat-list"]',
                timeout=180000,  # 3 minutos
            )
            print("WhatsApp Business conectado!\n")
        except Exception:
            print("Nao conseguiu detectar lista de conversas.")
            print("Verifique se o QR Code foi escaneado com o WhatsApp Business.")
            print("Tentando continuar mesmo assim...\n")

        time.sleep(3)

        # Abordagem: extrair nomes e tel diretamente do DOM da lista de chats
        # O WhatsApp Web mudou o HTML — chat-list-item nem sempre existe
        # Vamos usar spans com title dentro da lista de conversas
        print(f"Extraindo contatos da lista de conversas (limite: {limite})...")

        # Scroll para carregar mais conversas
        chat_list_container = page.query_selector('div[data-testid="chat-list"]')
        if chat_list_container:
            last_count = 0
            for scroll_iter in range(15):
                page.evaluate("""
                    const list = document.querySelector('div[data-testid="chat-list"]');
                    if (list) list.scrollTop += 800;
                """)
                time.sleep(0.8)
                current_spans = len(page.query_selector_all('div[data-testid="chat-list"] span[title]'))
                if current_spans >= limite or current_spans == last_count:
                    break
                last_count = current_spans
            print(f"   Carregados {last_count}+ itens na lista.\n")

        # Extrai todos os spans com title da lista de conversas
        # Cada span[title] na chat-list é um nome de conversa
        chat_names = page.evaluate("""
            () => {
                const chatList = document.querySelector('div[data-testid="chat-list"]');
                if (!chatList) return [];
                const spans = chatList.querySelectorAll('span[title]');
                const results = [];
                const seen = new Set();
                spans.forEach(s => {
                    const title = s.getAttribute('title') || '';
                    if (title && !seen.has(title)) {
                        seen.add(title);
                        results.push(title);
                    }
                });
                return results;
            }
        """)

        total_chats = len(chat_names)
        print(f"   {total_chats} conversas encontradas na lista.\n")

        # Limitar ao máximo solicitado
        chat_names = chat_names[:limite]

        # Agora vamos clicar em cada conversa para extrair o telefone do perfil
        for i, nome in enumerate(chat_names, 1):
            telefone = None
            observacao = ""

            print(f"  [{i}/{len(chat_names)}] {nome[:45]}...", end=" ")

            try:
                # Clicar na conversa pelo nome usando span[title]
                # Buscar o span com o title exato dentro da chat-list
                clicked = page.evaluate(f"""
                    () => {{
                        const chatList = document.querySelector('div[data-testid="chat-list"]');
                        if (!chatList) return false;
                        const spans = chatList.querySelectorAll('span[title]');
                        for (const s of spans) {{
                            if (s.getAttribute('title') === {json.dumps(nome)}) {{
                                // Clicar no elemento pai (o item da conversa)
                                s.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}
                """)

                if not clicked:
                    print("[X] nao encontrou")
                    continue

                time.sleep(1.5)

                # Tenta extrair telefone do header ou painel lateral
                telefone_info = page.evaluate("""
                    () => {
                        // Tenta encontrar telefone no header da conversa
                        const phoneSpans = document.querySelectorAll('span[title*="+"]');
                        for (const span of phoneSpans) {
                            const title = span.getAttribute('title') || '';
                            if (title.includes('+')) return title;
                        }
                        // Tenta no painel de perfil (se aberto)
                        const profileSpans = document.querySelectorAll('[data-testid="profile-panel"] span[title*="+"]');
                        for (const span of profileSpans) {
                            const title = span.getAttribute('title') || '';
                            if (title.includes('+')) return title;
                        }
                        // Tenta qualquer span com telefone
                        const allSpans = document.querySelectorAll('span[title]');
                        for (const span of allSpans) {
                            const title = span.getAttribute('title') || '';
                            if (title.match(/\\+?\\d{10,}/)) return title;
                        }
                        return null;
                    }
                """)

                if telefone_info:
                    telefone = normalizar_telefone_br(telefone_info)

                if telefone:
                    if len(telefone) > 14:
                        observacao = "Possível grupo (número longo demais)"
                        telefone = None
                        print("? grupo")
                    else:
                        leads.append({
                            "telefone": telefone,
                            "status": "abordado",
                            "observacao": observacao,
                        })
                        print(f"[OK] {telefone}")
                else:
                    # Verificar se parece grupo
                    if any(g in nome.lower() for g in ["grupo", "família", "trabalho", "whatsapp", "comunidade"]):
                        sem_numero.append({
                            "nome": nome,
                            "status": "abordado",
                            "observacao": "Grupo — ignorado",
                        })
                        print("≅ grupo (ignorado)")
                    else:
                        sem_numero.append({
                            "nome": nome,
                            "status": "abordado",
                            "observacao": "Telefone não identificado automaticamente",
                        })
                        print("? sem telefone")

            except Exception as e:
                print(f"[X] erro: {e}")

            # Volta para lista — clicar em área vazia ou pressionar ESC
            try:
                page.keyboard.press("Escape")
                time.sleep(0.3)
                # Clicar na lista de chats para garantir foco
                chat_list_el = page.query_selector('div[data-testid="chat-list"]')
                if chat_list_el:
                    chat_list_el.click()
                time.sleep(0.3)
            except Exception:
                pass

        browser.close()

    return leads, sem_numero


def salvar_csv(leads: list, sem_numero: list, output_dir: Path):
    """Salva os CSVs de saída."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Historico com telefone
    hist_path = output_dir / "historico_whatsapp.csv"
    if leads:
        with open(hist_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["telefone", "status", "observacao"])
            writer.writeheader()
            writer.writerows(leads)
    elif hist_path.exists():
        # Remove arquivo anterior se vazio
        hist_path.unlink()

    # Contatos sem número
    sem_path = output_dir / "contatos_sem_numero.csv"
    if sem_numero:
        with open(sem_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["nome", "status", "observacao"])
            writer.writeheader()
            writer.writerows(sem_numero)
    elif sem_path.exists():
        sem_path.unlink()

    return hist_path, sem_path


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Extrai histórico do WhatsApp Web para CSV")
    parser.add_argument(
        "--limite",
        type=int,
        default=50,
        help="Quantas conversas processar (default: 50)",
    )
    parser.add_argument(
        "--perfil",
        type=str,
        default=".whatsapp_business_profile",
        help="Pasta para perfil persistente (default: .whatsapp_business_profile)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Rodar em modo invisível (não recomendado na primeira vez)",
    )
    args = parser.parse_args()

    perfil = Path(args.perfil)
    limite = max(1, min(args.limite, 200))

    print("=" * 60)
    print("Extrair Historio do WhatsApp Business")
    print("=" * 60)
    print(f"   Limite de conversas: {limite}")
    print(f"   Perfil persistente:  {perfil}")
    print(f"   Modo:                {'Invisivel' if args.headless else 'Visivel'}")
    print(f"   Saida:               {OUTPUT_DIR}/historico_whatsapp.csv")
    print()
    print("   PERFIL: .whatsapp_business_profile/ (WhatsApp Business)")
    print("   NAO mistura com WhatsApp pessoal.")
    print("   Se for a primeira vez, escaneie o QR Code com o WhatsApp Business.")
    print("=" * 60)
    print()

    # Adquire o lock global do perfil dos senders antes de abrir o Chromium
    # (este script é somente leitura, mas compartilha o perfil .whatsapp_business_profile).
    with LockWhatsAppSender() as lock:
        if not lock.acquired:
            print("❌ Já existe um sender/processo ativo usando o perfil WhatsApp. Abortando.")
            sys.exit(1)
        leads, sem_numero = extrair_historico(limite, perfil, args.headless)

    hist_path, sem_path = salvar_csv(leads, sem_numero, OUTPUT_DIR)

    print()
    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"   Contatos com telefone: {len(leads)}")
    print(f"   Contatos sem telefone: {len(sem_numero)}")
    if hist_path.exists():
        print(f"   Salvo em: {hist_path}")
    if sem_path.exists():
        print(f"   Salvo em: {sem_path}")
    print()
    print("   CSV pronto para revisao manual.")
    print("   Depois use: python importar_historico_whatsapp.py")
    print()


if __name__ == "__main__":
    main()