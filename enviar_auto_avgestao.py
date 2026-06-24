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
import os, json, urllib.request, ssl, time, random, sys, atexit, signal, ctypes, argparse
from ctypes import wintypes
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timedelta

ENVIAR_HOJE = 30
INTERVALO_SEG = 420

BASE_DIR = Path(__file__).parent
PROFILE_DIR = BASE_DIR / ".whatsapp_business_profile"
PID_FILE = BASE_DIR / ".enviar_auto.pid"

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


def _pid_alive(pid):
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    code = wintypes.DWORD()
    kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    kernel32.CloseHandle(handle)
    return code.value == STILL_ACTIVE


def acquire_lock():
    if PID_FILE.exists():
        try:
            old = int(PID_FILE.read_text().strip())
            if old != os.getpid() and _pid_alive(old):
                print(f"❌ Outra instancia rodando (PID {old}). Abortando.")
                print(f"   Mate com: Stop-Process -Id {old} -Force")
                sys.exit(1)
        except (ValueError, OSError):
            pass
    PID_FILE.write_text(str(os.getpid()))


def release_lock():
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except OSError:
        pass


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


def is_celular(tel):
    if not tel:
        return False
    d = tel.replace("55", "", 1) if tel.startswith("55") else tel
    return d.startswith("21") and len(d) >= 11 and d[2] == "9"


def marcar(lead_id, status, obs=None):
    now = datetime.now().isoformat()
    body = {"status": status, "ultimo_contato_em": now}
    if status == "abordado":
        body["proximo_followup_em"] = (datetime.now() + timedelta(days=3)).isoformat()
    if obs:
        body["observacoes"] = obs
    req = urllib.request.Request(
        f"{API_URL}?id=eq.{lead_id}",
        data=json.dumps(body).encode(),
        headers={**HEADERS, "Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, context=CTX):
        pass


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
    tel = lead.get("telefone_normalizado") or lead.get("telefone") or ""
    if not is_celular(tel):
        print("   ⏭️ Fixo - pulando")
        marcar(lead["id"], "perdido", "Telefone fixo")
        return False
    msg = _escolher_msg(lead)
    url = f"https://web.whatsapp.com/send?phone={tel}&text={quote(msg)}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
    except Exception as e:
        print(f"   ❌ Erro navegando: {str(e)[:90]}")
        return False

    if not _wait_qr(page):
        return False

    bt = _body_text(page, 300)
    if "inválido" in bt or "invalid" in bt or "não é válido" in bt:
        print("   ⚠️ Número inválido")
        marcar(lead["id"], "perdido", "Número inválido")
        return False

    try:
        page.wait_for_selector('div[contenteditable="true"]', timeout=35000)
    except Exception:
        print("   ⚠️ Campo de texto nao apareceu")
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
            return False

    time.sleep(4)
    marcar(lead["id"], "abordado")
    print("   ✅ Marcado no Supabase")
    return True


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

    acquire_lock()
    atexit.register(release_lock)

    def _sig(sig, frame):
        release_lock()
        sys.exit(0)
    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

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
    cels = [l for l in all_leads if is_celular(l.get("telefone_normalizado") or l.get("telefone") or "")]
    print(f"   Disponiveis: {len(all_leads)} | Com WhatsApp (cel 21 c/ 9): {len(cels)}")
    if not cels:
        print("   Nada para enviar hoje.")
        release_lock()
        return
    random.shuffle(cels)
    leads = cels[:qtd]
    print(f"\n📋 {len(leads)} leads hoje | 7min cada | sem pausa de bloco\n")

    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        p = PROFILE_DIR / lock
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    from playwright.sync_api import sync_playwright

    total_ok = 0
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
        release_lock()

    print(f"\n{'='*60}")
    print(f"  ✅ Enviados: {total_ok}/{len(leads)}")
    print(f"  ⏰ {datetime.now().strftime('%H:%M')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
