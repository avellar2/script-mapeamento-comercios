#!/usr/bin/env python3
# =============================================================================
# INSTRUCOES PARA O HERMES (agente executor)
# -----------------------------------------------------------------------------
# Comando para rodar:
#   python enviar_auto_avgestao.py            (padrao: 30 leads)
#   python enviar_auto_avgestao.py 100        (envia 100 leads hoje)
#
# O que o script faz:
#   - Abre o Chrome JA LOGADO no WhatsApp Business (perfil .whatsapp_business_profile)
#   - Envia N mensagens (escolhido via argumento; padrao 30) com 7 min entre cada
#   - SEM pausa de bloco — vai direto do primeiro ao ultimo, 7 min entre cada
#   - Marca cada lead como "abordado" no Supabase apos envio
#   - Marca como "perdido" se for telefone fixo (DDD 21 sem o 9) ou numero invalido
#   - Mantem UM unico navegador aberto pra todos os leads (nao abre/fecha a cada lead)
#   - Consulta os campos "categoria" E "nicho" do Supabase (busca unificada OR — usa o que estiver preenchido)
#   - Categorias cobertas: oficina mecanica/autoeletrica, serralheria, marcenaria,
#     eletricista, pintor, encanador, loja de celulares (assistencia tecnica),
#     material de construcao, loja de moveis/moveis planejados, vidracaria,
#     restaurante, pizzaria, lanchonete (cardapio digital),
#     confeitaria, padaria (encomendas/cardapio),
#     otica (orcamento), refrigeracao/ar-condicionado (chamado)
#
# Regras IMPORTANTES:
#   - NAO rode o script mais de uma vez ao mesmo tempo. Ele tem lock de instancia
#     unica (.enviar_auto.pid) e vai abortar se ja houver outra instancia rodando.
#   - Se aparecer QR Code na tela, AVISE O Vanderson para escanear pelo celular.
#     O script espera ate 4 minutos pelo QR.
#   - headless=False: o navegador fica visivel de proposito. Nao altere.
#   - Se o navegador fechar sozinho, nao tente reabrir. Avise o Vanderson com o
#     erro exato e o PID que aparece no console.
#   - NAO altere INTERVALO_SEG (7 min) sem ordem explicita do Vanderson.
#
# Diagnostico do bug anterior (resolvido em 23/06/2026):
#   O navegador fechava apos a 1a mensagem porque havia 5 instancias do script
#   rodando ao mesmo tempo, todas disputando o mesmo perfil .whatsapp_business_profile
#   com launch_persistent_context. Alem disso, o Chromium bundled do Playwright
#   (v~136) era mais velho que o perfil (Chrome 148), causando crash silencioso.
#   Correcao: lock de instancia unica + channel="chrome" (Chrome 149 instalado)
#   + navegador unico mantido aberto durante toda a sessao.
#
# Assinatura: opencode/glm-5.2 — 24/06/2026 (novas frases + sem pausa de bloco + qtd via argumento)
# =============================================================================
"""
Envio automatico WhatsApp - AVGESTAO
Um unico navegador mantido aberto para todos os leads da sessao.
Lock de instancia unica via PID file. Usa Chrome instalado (channel=chrome)
para evitar incompatibilidade de versao do perfil.
"""
import os, json, urllib.request, ssl, time, random, sys, argparse
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timezone

ENVIAR_HOJE = 30
INTERVALO_SEG = 420

BASE_DIR = Path(__file__).parent
PROFILE_DIR = BASE_DIR / ".whatsapp_business_profile"

# Integração lead_outreach: lock global do perfil, normalização unificada,
# campaign_key centralizada, reserva atômica antes de abrir o WhatsApp,
# settle atômico após envio. Nenhum PATCH separado em leads.
sys.path.insert(0, str(BASE_DIR))
from config.lock_whatsapp_sender import LockWhatsAppSender
from sender_int import normalizar_telefone_lead, obter_campaign_key, reserve_lead, settle_lead

env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
API_URL = f"{SUPABASE_URL}/rest/v1/leads"
CTX = ssl.create_default_context()
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def msg_oficina(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar oficinas e serviços automotivos.\n\n"
        f"Com ele vocês registram o veículo, abrem a ordem de serviço, enviam o orçamento para aprovação e acompanham os serviços, peças e valores até a entrega.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um veículo real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_producao(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar serviços sob medida.\n\n"
        f"Com ele vocês registram medidas, materiais e alterações, montam o orçamento e enviam um link para o cliente aprovar antes de iniciar o trabalho.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um serviço real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_prestador(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar clientes, orçamentos e serviços.\n\n"
        f"Com ele vocês montam o orçamento, enviam um link para aprovação e acompanham quais serviços estão pendentes, em andamento, concluídos ou aguardando pagamento.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um serviço real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_assistencia(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.\n\n"
        f"Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_material_construcao(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar clientes e orçamentos.\n\n"
        f"Com ele vocês montam orçamentos com todos os produtos, quantidades e valores e enviam um link para o cliente conferir e aprovar.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um orçamento real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_moveis(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar orçamentos e serviços personalizados.\n\n"
        f"Com ele vocês registram medidas, acabamentos e observações, montam o orçamento e enviam um link para o cliente conferir e aprovar antes da produção.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um pedido real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_vidracaria(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar serviços e orçamentos.\n\n"
        f"Com ele vocês registram as medidas e observações, montam o orçamento e enviam um link para o cliente aprovar e acompanhar o andamento do serviço.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um serviço real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_cardapio(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar pedidos e pagamentos.\n\n"
        f"Com o cardápio digital, o cliente escolhe os produtos pelo link e o pedido entra organizado no sistema para vocês acompanharem o preparo, a entrega e o pagamento.\n\n"
        f"Para facilitar, eu mesmo configuro o cardápio inicial e deixo tudo pronto para vocês testarem com pedidos reais durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_confeitaria(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar pedidos e encomendas.\n\n"
        f"Com ele vocês disponibilizam o cardápio digital, recebem os pedidos organizados e acompanham o andamento e o pagamento em um só lugar.\n\n"
        f"Para facilitar, eu mesmo configuro os primeiros produtos e deixo tudo pronto para vocês testarem com pedidos reais durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_otica(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar clientes, orçamentos e pedidos.\n\n"
        f"Com ele vocês registram as informações do atendimento, montam o orçamento e enviam um link para o cliente visualizar e aprovar.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

def msg_refrigeracao(lead):
    nome = lead.get("nome") or ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar empresas de manutenção e refrigeração.\n\n"
        f"Com ele vocês registram o cliente e o equipamento, abrem a ordem de serviço, enviam o orçamento para aprovação e mantêm todo o histórico do atendimento.\n\n"
        f"Para facilitar, eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um chamado real durante 15 dias.\n\n"
        f"Posso liberar e configurar o acesso de vocês?"
    )

CAT_MAP = {
    "oficina mecânica": msg_oficina,
    "autoelétrica": msg_oficina,
    "serralheria": msg_producao,
    "marcenaria": msg_producao,
    "eletricista": msg_prestador,
    "pintor": msg_prestador,
    "encanador": msg_prestador,
    "loja de celulares": msg_assistencia,
    "assistência técnica": msg_assistencia,
    "material de construção": msg_material_construcao,
    "loja de móveis": msg_moveis,
    "móveis planejados": msg_moveis,
    "vidraçaria": msg_vidracaria,
    "restaurante": msg_cardapio,
    "pizzaria": msg_cardapio,
    "lanchonete": msg_cardapio,
    "confeitaria": msg_confeitaria,
    "padaria": msg_confeitaria,
    "ótica": msg_otica,
    "refrigeração": msg_refrigeracao,
    "ar-condicionado": msg_refrigeracao,
}


def fetch_leads():
    categorias = [
        "oficina mecânica", "autoelétrica", "serralheria", "marcenaria",
        "eletricista", "pintor", "encanador",
        "loja de celulares", "assistência técnica",
        "material de construção", "loja de móveis", "móveis planejados", "vidraçaria",
        "restaurante", "pizzaria", "lanchonete", "confeitaria", "padaria",
        "ótica", "refrigeração", "ar-condicionado",
    ]
    all_leads = []
    seen_ids = set()
    for categoria in categorias:
        offset = 0
        while True:
            cat_enc = quote(categoria)
            req = urllib.request.Request(
                f"{API_URL}?or=(categoria.ilike.*{cat_enc}*,nicho.ilike.*{cat_enc}*)"
                f"&status=in.(novo,pronto_para_enviar)"
                f"&select=id,nome,telefone,telefone_normalizado,cidade,bairro,categoria,nicho,status"
                f"&limit=1000&offset={offset}",
                headers=HEADERS,
            )
            with urllib.request.urlopen(req, context=CTX) as r:
                data = json.loads(r.read().decode())
                if not data:
                    break
                for lead in data:
                    lid = lead.get("id")
                    if lid and lid not in seen_ids:
                        seen_ids.add(lid)
                        all_leads.append(lead)
                if len(data) < 1000:
                    break
                offset += 1000
    return all_leads


def _body_text(page, limit=400):
    try:
        return page.inner_text("body", timeout=5000)[:limit].lower()
    except Exception:
        return ""


def _wait_qr(page):
    bt = _body_text(page, 200)
    if not any(k in bt for k in ("escaneie", "conectar", "use o whatsapp", "scan the qr")):
        return True
    print("   ⚠️ QR Code! Escaneie no celular...")
    for _ in range(48):
        time.sleep(5)
        bt = _body_text(page, 200)
        if not any(k in bt for k in ("escaneie", "conectar", "use o whatsapp", "scan the qr")):
            print("   ✅ Conectado!")
            return True
    print("   ❌ QR nao escaneado em 4min")
    return False


def _escolher_msg(lead):
    valor = (lead.get("categoria") or lead.get("nicho") or "").strip().lower()
    if not valor:
        return msg_prestador(lead)
    fn = CAT_MAP.get(valor)
    if fn:
        return fn(lead)
    for chave, func in CAT_MAP.items():
        if chave in valor:
            return func(lead)
    return msg_prestador(lead)


def enviar_um(page, lead):
    nome = lead["nome"]
    tel_norm = normalizar_telefone_lead(lead)
    if not tel_norm:
        print("   ⏭️ Telefone inválido - pulando")
        return False
    if not (tel_norm.startswith("5521") and len(tel_norm) == 13):
        print("   ⏭️ Fixo / não-celular DDD 21 - pulando")
        return False

    campaign_key = obter_campaign_key(lead)
    msg = _escolher_msg(lead)

    # Reserva atômica ANTES de abrir o WhatsApp — nenhuma abertura antes da reserva.
    reserve = reserve_lead(tel_norm, campaign_key, lead["id"], "sender:auto")
    if not reserve or reserve.get("outcome") != "reserved":
        outcome = reserve.get("outcome", "erro") if reserve else "sem cliente"
        print(f"   ⚠️ Reserva recusada: {outcome}")
        return False

    reservation_id = reserve.get("reservation_id")
    reservation_token = reserve.get("reservation_token")

    url = f"https://web.whatsapp.com/send?phone={tel_norm}&text={quote(msg)}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
    except Exception as e:
        print(f"   ❌ Erro navegando: {str(e)[:90]}")
        settle_lead(reservation_id, reservation_token, "failed", obs="erro_navegacao")
        return False

    if not _wait_qr(page):
        settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="qr_nao_escaneado")
        return False

    bt = _body_text(page, 300)
    if "inválido" in bt or "invalid" in bt or "não é válido" in bt:
        print("   ⚠️ Número inválido")
        settle_lead(reservation_id, reservation_token, "failed", obs="numero_invalido")
        return False

    try:
        page.wait_for_selector('div[contenteditable="true"]', timeout=35000)
    except Exception:
        print("   ⚠️ Campo de texto nao apareceu")
        settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="campo_nao_apareceu")
        return False
    time.sleep(2)

    btn = page.locator('button[aria-label="Enviar"], button[aria-label="Send"]')
    if btn.count() > 0:
        btn.first.click()
        print("   ✅ Enviado!")
    else:
        ed = page.locator('div[contenteditable="true"]')
        if ed.count() > 0:
            ed.first.click()
            time.sleep(1)
            page.keyboard.press("Enter")
            print("   ✅ Enviado via Enter!")
        else:
            print("   ❌ Botão/campo nao encontrado")
            settle_lead(reservation_id, reservation_token, "needs_reconciliation", obs="botao_nao_encontrado")
            return False

    time.sleep(4)
    # Finaliza via settle_outreach (transação única). NENHUM PATCH separado em leads.
    settle = settle_lead(
        reservation_id, reservation_token, "sent",
        message_timestamp=datetime.now(timezone.utc).isoformat(),
        obs="enviado_auto_avgestao",
    )
    if settle and settle.get("outcome") in ("settled", "already_settled"):
        print("   ✅ Confirmado no Supabase")
        return True
    print(f"   ⚠️ Falha ao finalizar: {settle}")
    return False


def _countdown(segundos, label):
    for s in range(segundos, 0, -1):
        if s % 60 == 0 or s <= 10:
            print(f"   {label}: {s//60}min {s%60:02d}s", end="\r")
        time.sleep(1)
    print()


def main():
    parser = argparse.ArgumentParser(description="Envio automatico WhatsApp AVGESTAO")
    parser.add_argument("quantidade", nargs="?", type=int, default=ENVIAR_HOJE,
                        help=f"Quantos leads enviar hoje (padrao: {ENVIAR_HOJE})")
    parser.add_argument("--excluir", type=str, default="",
                        help="Nichos/categorias para excluir (separados por virgula). Ex: --excluir \"oficina mecânica,refrigeração\"")
    args = parser.parse_args()
    qtd = max(1, args.quantidade)
    excluir = [e.strip().lower() for e in args.excluir.split(",") if e.strip()]

    print("=" * 60)
    print(f"  🚗 Envio Automatico AVGESTAO - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  📋 Meta de hoje: {qtd} leads | 7min entre cada (sem pausa de bloco)")
    if excluir:
        print(f"  🚫 Excluindo nichos: {', '.join(excluir)}")
    print("=" * 60)
    print("\n📡 Buscando leads...")
    all_leads = fetch_leads()
    if excluir:
        antes = len(all_leads)
        all_leads = [
            l for l in all_leads
            if not any(
                e in (l.get("categoria") or "").lower() or e in (l.get("nicho") or "").lower()
                for e in excluir
            )
        ]
        print(f"   ⚠️ Filtrados: {antes - len(all_leads)} leads excluidos por nicho")

    # Filtro por normalização unificada (celular DDD 21 com nono dígito)
    cels = []
    for l in all_leads:
        tel_norm = normalizar_telefone_lead(l)
        if tel_norm and tel_norm.startswith("5521") and len(tel_norm) == 13:
            cels.append(l)
    print(f"   Disponiveis: {len(all_leads)} | Com WhatsApp (cel 21 c/ 9): {len(cels)}")
    if not cels:
        print("   Nada para enviar hoje.")
        return
    random.shuffle(cels)
    leads = cels[:qtd]
    print(f"\n📋 {len(leads)} leads hoje | 7min cada | sem pausa de bloco\n")

    from playwright.sync_api import sync_playwright

    total_ok = 0
    # Lock global do perfil dos senders — ANTES de remover SingletonLock/abrir Chromium.
    # Substitui o antigo lock PID-only (.enviar_auto.pid) por um lock de perfil unificado.
    with LockWhatsAppSender() as lock:
        if not lock.acquired:
            print("❌ Já existe um sender ativo usando o perfil WhatsApp. Abortando.")
            sys.exit(1)

        for lockf in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
            p = PROFILE_DIR / lockf
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

        browser = None
        try:
            with sync_playwright() as pw:
                try:
                    browser = pw.chromium.launch_persistent_context(
                        user_data_dir=str(PROFILE_DIR),
                        channel="chrome",
                        headless=False,
                        args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--new-instance"],
                        viewport={"width": 800, "height": 900},
                        locale="pt-BR",
                    )
                except Exception as e:
                    print(f"   channel=chrome falhou ({str(e)[:80]}), tentando chromium bundled...")
                    browser = pw.chromium.launch_persistent_context(
                        user_data_dir=str(PROFILE_DIR),
                        headless=False,
                        args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--new-instance"],
                        viewport={"width": 800, "height": 900},
                        locale="pt-BR",
                    )
                page = browser.pages[0] if browser.pages else browser.new_page()

                for i, lead in enumerate(leads):
                    print(f"\n[{i+1}/{len(leads)}] {lead['nome']}")
                    print(f"   📍 {lead.get('cidade','')} | 📞 {lead.get('telefone_normalizado') or lead.get('telefone')}")
                    try:
                        ok = enviar_um(page, lead)
                    except Exception as e:
                        print(f"   ❌ Erro inesperado: {str(e)[:90]}")
                        ok = False
                    if ok:
                        total_ok += 1

                    if i < len(leads) - 1:
                        print(f"   ⏳ 7min...")
                        _countdown(INTERVALO_SEG, "proximo")

                try:
                    browser.close()
                except Exception:
                    pass
        finally:
            pass  # LockWhatsAppSender liberado no __exit__

    print(f"\n{'='*60}")
    print(f"  ✅ Enviados: {total_ok}/{len(leads)}")
    print(f"  ⏰ {datetime.now().strftime('%H:%M')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
