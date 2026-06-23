#!/usr/bin/env python3
# =============================================================================
# INSTRUCOES PARA O HERMES (agente executor)
# -----------------------------------------------------------------------------
# Comando para rodar:
#   python enviar_auto_avgestao.py
#
# O que o script faz:
#   - Abre o Chrome JA LOGADO no WhatsApp Business (perfil .whatsapp_business_profile)
#   - Envia 30 mensagens hoje (7 min entre cada, bloco de 10 + 1h de pausa)
#   - Marca cada lead como "abordado" no Supabase apos envio
#   - Marca como "perdido" se for telefone fixo (DDD 21 sem o 9) ou numero invalido
#   - Mantem UM unico navegador aberto pra todos os leads (nao abre/fecha a cada lead)
#   - Consulta o campo "categoria" do Supabase (NAO "nicho" — esse esta vazio em todos os leads)
#   - Categorias cobertas: oficina mecanica, serralheria, marcenaria, eletricista, pintor,
#     encanador, loja de celulares (assistencia tecnica), material de construcao,
#     loja de moveis, vidracaria, restaurante, pizzaria, lanchonete, confeitaria,
#     padaria (cardapio digital), otica (orcamento)
#
# Regras IMPORTANTES:
#   - NAO rode o script mais de uma vez ao mesmo tempo. Ele tem lock de instancia
#     unica (.enviar_auto.pid) e vai abortar se ja houver outra instancia rodando.
#   - Se aparecer QR Code na tela, AVISE O Vanderson para escanear pelo celular.
#     O script espera ate 4 minutos pelo QR.
#   - headless=False: o navegador fica visivel de proposito. Nao altere.
#   - Se o navegador fechar sozinho, nao tente reabrir. Avise o Vanderson com o
#     erro exato e o PID que aparece no console.
#   - NAO altere ENVIAR_HOJE, INTERVALO_SEG, BLOCO_TAMANHO ou PAUSA_BLOCO_SEG sem
#     ordem explicita do Vanderson.
#
# Diagnostico do bug anterior (resolvido em 23/06/2026):
#   O navegador fechava apos a 1a mensagem porque havia 5 instancias do script
#   rodando ao mesmo tempo, todas disputando o mesmo perfil .whatsapp_business_profile
#   com launch_persistent_context. Alem disso, o Chromium bundled do Playwright
#   (v~136) era mais velho que o perfil (Chrome 148), causando crash silencioso.
#   Correcao: lock de instancia unica + channel="chrome" (Chrome 149 instalado)
#   + navegador unico mantido aberto durante toda a sessao.
#
# Assinatura: opencode/glm-5.2 — 23/06/2026
# =============================================================================
"""
Envio automatico WhatsApp - AVGESTAO
Um unico navegador mantido aberto para todos os leads da sessao.
Lock de instancia unica via PID file. Usa Chrome instalado (channel=chrome)
para evitar incompatibilidade de versao do perfil.
"""
import os, json, urllib.request, ssl, time, random, sys, atexit, signal, ctypes
from ctypes import wintypes
from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timedelta

ENVIAR_HOJE = 30
INTERVALO_SEG = 420
BLOCO_TAMANHO = 10
PAUSA_BLOCO_SEG = 3600

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
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Em uma oficina, perder o controle do que foi autorizado, do que já foi feito e do que o cliente ainda deve gera retrabalho e discussão na entrega.\n\n"
        f"No AVGESTÃO vocês abrem a ordem de serviço, registram peças e valores, e enviam um link para o cliente aprovar o orçamento antes de começar.\n\n"
        f"O teste é gratuito por 15 dias. Posso liberar o acesso de vocês?"
    )

def msg_producao(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Uma medida, alteração ou observação perdida no WhatsApp pode gerar orçamento errado, retrabalho e prejuízo no material.\n\n"
        f"No AVGESTÃO vocês registram cada medida e observação, montam o orçamento e enviam um link para o cliente aprovar antes da produção.\n\n"
        f"São 15 dias grátis para testar. Posso criar o acesso?"
    )

def msg_prestador(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Quem pediu orçamento, quem aprovou e quem ainda não pagou — perder esse controle custa dinheiro e gera trabalho dobrado.\n\n"
        f"No AVGESTÃO vocês organizam os clientes, criam orçamento, abrem ordem de serviço e acompanham num painel o que tá pendente e o que já foi pago.\n\n"
        f"O teste é gratuito por 15 dias. Posso liberar o acesso?"
    )

def msg_assistencia(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Quando entram aparelhos para reparo, pode ficar difícil controlar o defeito informado, o orçamento aprovado e a etapa de cada serviço.\n\n"
        f"No AVGESTÃO vocês abrem a ordem de serviço, registram o aparelho e enviam um link para o cliente aprovar o orçamento e acompanhar o andamento.\n\n"
        f"São 15 dias grátis. Posso criar o acesso de vocês?"
    )

def msg_material_construcao(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Em orçamentos grandes, um item, quantidade ou valor anotado errado pode gerar retrabalho e problema com o cliente.\n\n"
        f"No AVGESTÃO vocês montam o orçamento item por item e enviam um link para o cliente conferir e aprovar.\n\n"
        f"O teste é gratuito por 15 dias. Posso liberar o acesso de vocês?"
    )

def msg_moveis(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Uma medida, acabamento ou alteração esquecida pode gerar atraso, retrabalho e prejuízo com material.\n\n"
        f"No AVGESTÃO vocês registram as informações, montam o orçamento e enviam um link para o cliente conferir e aprovar.\n\n"
        f"São 15 dias grátis para testar. Posso criar o acesso?"
    )

def msg_vidracaria(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Uma medida ou alteração perdida no WhatsApp pode resultar em vidro produzido errado e desperdício de material.\n\n"
        f"No AVGESTÃO vocês registram o serviço, montam o orçamento e enviam um link para o cliente visualizar e aprovar.\n\n"
        f"O teste é gratuito por 15 dias. Posso liberar o acesso?"
    )

def msg_cardapio(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Pedidos espalhados pelo WhatsApp podem causar itens esquecidos, anotações erradas e demora no atendimento.\n\n"
        f"Com o AVGESTÃO, o cliente escolhe pelo cardápio digital e o pedido entra organizado no sistema, com controle do andamento e pagamento.\n\n"
        f"São 15 dias grátis. Posso criar o acesso de vocês?"
    )

def msg_otica(lead):
    nome = lead.get("nome") or ""
    cidade = lead.get("cidade") or ""
    local = f" Atendo empresas em {cidade} e região." if cidade else ""
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Aqui é o Vanderson, criador do AVGESTÃO.{local}\n\n"
        f"Quando modelos, lentes, valores e observações ficam espalhados, aumenta o risco de erro e fica difícil encontrar o histórico do cliente.\n\n"
        f"No AVGESTÃO vocês organizam as informações, montam o orçamento e enviam um link para o cliente visualizar e aprovar.\n\n"
        f"O teste é gratuito por 15 dias. Posso liberar o acesso?"
    )

CAT_MAP = {
    "oficina mecânica": msg_oficina,
    "serralheria": msg_producao,
    "marcenaria": msg_producao,
    "eletricista": msg_prestador,
    "pintor": msg_prestador,
    "encanador": msg_prestador,
    "loja de celulares": msg_assistencia,
    "material de construção": msg_material_construcao,
    "loja de móveis": msg_moveis,
    "vidraçaria": msg_vidracaria,
    "restaurante": msg_cardapio,
    "pizzaria": msg_cardapio,
    "lanchonete": msg_cardapio,
    "confeitaria": msg_cardapio,
    "padaria": msg_cardapio,
    "ótica": msg_otica,
}


def fetch_leads():
    categorias = [
        "oficina mecânica", "serralheria", "marcenaria",
        "eletricista", "pintor", "encanador",
        "loja de celulares",
        "material de construção", "loja de móveis", "vidraçaria",
        "restaurante", "pizzaria", "lanchonete", "confeitaria", "padaria",
        "ótica",
    ]
    all_leads = []
    for categoria in categorias:
        offset = 0
        while True:
            cat_enc = quote(categoria)
            req = urllib.request.Request(
                f"{API_URL}?categoria=ilike.*{cat_enc}*&status=in.(novo,pronto_para_enviar)"
                f"&select=id,nome,telefone,telefone_normalizado,cidade,bairro,categoria,status"
                f"&limit=1000&offset={offset}",
                headers=HEADERS,
            )
            with urllib.request.urlopen(req, context=CTX) as r:
                data = json.loads(r.read().decode())
                if not data:
                    break
                all_leads.extend(data)
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


def enviar_um(page, lead):
    nome = lead["nome"]
    tel = lead.get("telefone_normalizado") or lead.get("telefone") or ""
    categoria = lead.get("categoria", "")
    if not is_celular(tel):
        print("   ⏭️ Fixo - pulando")
        marcar(lead["id"], "perdido", "Telefone fixo")
        return False
    msg = CAT_MAP.get(categoria, msg_prestador)(lead)
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
    acquire_lock()
    atexit.register(release_lock)

    def _sig(sig, frame):
        release_lock()
        sys.exit(0)
    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    print("=" * 60)
    print(f"  🚗 Envio Automatico AVGESTAO - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)
    print("\n📡 Buscando leads...")
    all_leads = fetch_leads()
    cels = [l for l in all_leads if is_celular(l.get("telefone_normalizado") or l.get("telefone") or "")]
    print(f"   Disponiveis: {len(all_leads)} | Com WhatsApp (cel 21 c/ 9): {len(cels)}")
    if not cels:
        print("   Nada para enviar hoje.")
        release_lock()
        return
    random.shuffle(cels)
    leads = cels[:ENVIAR_HOJE]
    print(f"\n📋 {len(leads)} leads hoje | 7min cada | bloco de 10 + 1h pausa\n")

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
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                    viewport={"width": 800, "height": 900},
                    locale="pt-BR",
                )
            except Exception as e:
                print(f"   channel=chrome falhou ({str(e)[:80]}), tentando chromium bundled...")
                browser = pw.chromium.launch_persistent_context(
                    user_data_dir=str(PROFILE_DIR),
                    headless=False,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
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
                    if (i + 1) % BLOCO_TAMANHO == 0:
                        prox = (datetime.now() + timedelta(seconds=PAUSA_BLOCO_SEG)).strftime("%H:%M")
                        print(f"\n⏸️  Bloco feito. Pausa 1h. Proximo: {prox}")
                        _countdown(PAUSA_BLOCO_SEG, "pausa")
                    else:
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
