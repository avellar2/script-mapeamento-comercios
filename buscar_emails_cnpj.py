"""
Busca emails via CNPJ + API ReceitaWS + Scrape de site
=======================================================
Estrategias:
1. Se tem site -> raspar email do site (requests)
2. Buscar CNPJ no Bing
3. Com CNPJ -> API ReceitaWS (email direto em JSON)
4. Fallback -> cnpj.biz via Playwright
"""

import csv
import json
import re
import sys
import os
import time
import random
import requests as req_lib
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent / "output"
CSV_FILE = OUTPUT_DIR / "leads_baixada_20260421_193841.csv"
PROGRESS_FILE = OUTPUT_DIR / "progresso_emails_cnpj.json"

BLACKLIST = {
    "test@test.com", "email@email.com", "example@example.com",
    "noreply@google.com", "no-reply@google.com",
}


def extract_emails(text):
    if not text:
        return []
    t = text.lower()
    t = t.replace("[at]", "@").replace("(at)", "@")
    t = t.replace("[arroba]", "@").replace("(arroba)", "@")
    t = t.replace(" at ", "@")
    raw = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", t)
    valid = []
    seen = set()
    for email in raw:
        email = email.strip(".")
        if len(email) > 80 or email in BLACKLIST:
            continue
        if "quemfazsite" in email or "placeholder" in email:
            continue
        domain = email.split("@")[-1]
        if len(domain) < 4 or "." not in domain:
            continue
        ext = "." + domain.rsplit(".", 1)[-1]
        if ext in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".css"}:
            continue
        if email not in seen:
            seen.add(email)
            valid.append(email)
    return valid


def extract_cnpj(text):
    if not text:
        return ""
    match = re.search(r"(\d{2}\.?\d{3}\.?\d{3}[\/\\]?\d{4}-?\d{2})", text)
    if match:
        cnpj = re.sub(r"[^\d]", "", match.group(1))
        if len(cnpj) == 14:
            return cnpj
    return ""


def validar_email(email):
    if not email:
        return ""
    email = str(email).strip().lower()
    if email in BLACKLIST:
        return ""
    if len(email) > 80 or len(email) < 6:
        return ""
    # Rejeitar falsos positivos (codigo JS, modulos, etc)
    fakes = ["segmenter", "loader", "module", "webpack", "require", "exports"]
    if any(f in email for f in fakes):
        return ""
    # Dominio deve ter pelo menos 2 chars depois do ponto
    if not re.match(r"^[\w.+-]+@[\w-]+\.[\w-]{2,}$", email):
        return ""
    return email


def limpar_nome(nome):
    """Limpa nome SEO do Google Maps."""
    n = nome.split("|")[0].split("(")[0].strip()
    n = re.sub(r"\b(amil|hapvida|metlife|primavida|sulamérica|unimed|bradesco)\b.*", "", n, flags=re.I)
    n = n.strip()
    return n


# === ESTRATEGIA 1: Scrape do site ===
def scrape_site_email(url, domain):
    """Raspa email da homepage e /contato."""
    if not url:
        return ""
    urls_to_try = [url]
    if domain:
        urls_to_try.append(f"https://{domain}/contato")
        urls_to_try.append(f"https://{domain}/contact")

    for u in urls_to_try:
        try:
            resp = req_lib.get(u, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0"
            })
            if resp.status_code == 200:
                emails = extract_emails(resp.text)
                # Validar cada email
                for e in emails:
                    valid = validar_email(e)
                    if valid:
                        if domain and domain in valid:
                            return valid
                        return valid
        except Exception:
            continue
    return ""


# === ESTRATEGIA 2: API ReceitaWS ===
def email_via_receitaws(cnpj):
    """Busca email via API gratuita da ReceitaWS. Retry ilimitado ate conseguir."""
    url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
    tentativa = 0
    while True:
        tentativa += 1
        try:
            resp = req_lib.get(url, timeout=10, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email", "")
                if email:
                    email = email.strip().lower()
                    emails = [e.strip() for e in email.split(";") if e.strip()]
                    for e in emails:
                        valid = validar_email(e)
                        if valid:
                            return valid
                return ""
            elif resp.status_code == 429:
                espera = min(30 + (tentativa * 10), 120)
                print(f"  [!] Rate limit ReceitaWS, aguardando {espera}s (tentativa {tentativa})...")
                time.sleep(espera)
                continue
            else:
                return ""
        except Exception:
            if tentativa >= 3:
                return ""
            time.sleep(5)


# === ESTRATEGIA 3: API publica.cnpj.ws ===
def email_via_cnpj_ws(cnpj):
    """Busca email via API publica.cnpj.ws."""
    try:
        url = f"https://publica.cnpj.ws/cnpj/{cnpj}"
        resp = req_lib.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Tenta varios campos possiveis
            email = (data.get("estabelecimento", {}).get("email")
                     or data.get("email", "")
                     or "")
            if email:
                valid = validar_email(email.strip().lower())
                if valid:
                    return valid
    except Exception:
        pass
    return ""


def main():
    print("=" * 60)
    print("BUSCA DE EMAILS - CNPJ + SITE + API")
    print("=" * 60)

    # Ler CSV
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    sem_email = [(i, r) for i, r in enumerate(rows) if not r.get("email")]
    print(f"Leads sem email: {len(sem_email)} de {len(rows)}")

    if not sem_email:
        print("Todos ja tem email!")
        return

    # Carregar progresso
    progress = {}
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            progress = json.load(f)
        ja_tem = sum(1 for v in progress.values() if v.get("email"))
        print(f"Progresso anterior: {ja_tem} emails ja encontrados")

    encontrados = 0
    sem_cnpj = 0
    sem_email_total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context = browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        )
        # Anti-detecção
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

        # Pagina para buscar CNPJ direto no site de consulta
        busca_page = context.new_page()

        for idx, (row_idx, lead) in enumerate(sem_email):
            nome = lead["nome"]
            cidade = lead["cidade"].replace(", RJ", "").replace(",RJ", "").strip()
            website = lead.get("website", "")
            domain = lead.get("domain", "") or ""
            chave = f"{nome}|{cidade}"

            # Ja processado?
            if chave in progress:
                email_salvo = progress[chave].get("email", "")
                if email_salvo:
                    rows[row_idx]["email"] = email_salvo
                    encontrados += 1
                continue

            nome_limpo = limpar_nome(nome)
            print(f"\n[{idx+1}/{len(sem_email)}] {nome_limpo} | {cidade}")

            email_final = ""

            # ESTRATEGIA 1: Scrape do site
            if website or domain:
                print(f"  [1] Scraping site...")
                email_final = scrape_site_email(website, domain)
                if email_final:
                    print(f"  [OK] Email do site: {email_final}")

            # ESTRATEGIA 2: Buscar CNPJ direto no site de consulta
            if not email_final:
                cnpj = ""
                print(f"  [2] Buscando CNPJ...")

                # Buscar no Google
                try:
                    query = f"{nome_limpo} {cidade} RJ CNPJ"
                    busca_page.goto(
                        f"https://www.google.com/search?q={query.replace(' ', '+')}",
                        wait_until="domcontentloaded",
                        timeout=20000,
                    )
                    time.sleep(3)

                    # Se aparecer consentimento de cookies do Google
                    try:
                        busca_page.click('button:has-text("Aceitar"), button:has-text("Accept all")', timeout=2000)
                        time.sleep(1)
                    except Exception:
                        pass

                    # Verificar se tem CAPTCHA
                    body = busca_page.inner_text("body").lower()
                    if "tráfego incomum" in body or "unusual traffic" in body or "não sou um robô" in body or "recaptcha" in body:
                        print(f"  [!] CAPTCHA detectado! Resolva no navegador aberto...")
                        input(f"  [PAUSA] Resolva o CAPTCHA no navegador e aperte ENTER aqui para continuar...")

                    body = busca_page.inner_text("body")
                    cnpj = extract_cnpj(body)
                    if cnpj:
                        print(f"  [OK] CNPJ no Google")
                except Exception as e:
                    print(f"  [!] Google erro: {str(e)[:60]}")

                # Fallback: DuckDuckGo via requests
                if not cnpj:
                    for query_text in [f'{nome_limpo} {cidade} RJ CNPJ', f'{nome_limpo} CNPJ']:
                        try:
                            ddg_url = f"https://html.duckduckgo.com/html/?q={query_text.replace(' ', '+')}"
                            resp = req_lib.get(ddg_url, timeout=15, headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0"
                            })
                            if resp.status_code == 200:
                                cnpj = extract_cnpj(resp.text)
                                if cnpj:
                                    print(f"  [OK] CNPJ via DuckDuckGo")
                                    break
                        except Exception:
                            pass
                        time.sleep(1)

                if cnpj:
                    cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
                    print(f"  [CNPJ] {cnpj_fmt}")

                    # API ReceitaWS
                    print(f"  [3a] ReceitaWS...")
                    email_final = email_via_receitaws(cnpj)
                    if email_final:
                        print(f"  [OK] Email: {email_final}")

                    # API cnpj.ws
                    if not email_final:
                        print(f"  [3b] CNPJ.ws...")
                        email_final = email_via_cnpj_ws(cnpj)
                        if email_final:
                            print(f"  [OK] Email: {email_final}")

                    # BrasilAPI
                    if not email_final:
                        print(f"  [3c] BrasilAPI...")
                        try:
                            resp = req_lib.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=10)
                            if resp.status_code == 200:
                                data = resp.json()
                                email = data.get("email", "")
                                if email:
                                    email_final = validar_email(email.strip().lower())
                                    if email_final:
                                        print(f"  [OK] BrasilAPI: {email_final}")
                        except Exception:
                            pass

                    # cnpj.biz via Playwright
                    if not email_final:
                        print(f"  [3d] cnpj.biz...")
                        try:
                            cnpj_page = context.new_page()
                            cnpj_page.goto(f"https://cnpj.biz/{cnpj}", wait_until="domcontentloaded", timeout=20000)
                            time.sleep(4)
                            cnpj_page.keyboard.press("Escape")
                            time.sleep(0.5)

                            # Remover overlays
                            try:
                                cnpj_page.evaluate("""() => {
                                    document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"]').forEach(el => el.remove());
                                }""")
                            except Exception:
                                pass

                            # Verificar email direto no HTML
                            html = cnpj_page.content()
                            emails = extract_emails(html)
                            for e in emails:
                                valid = validar_email(e)
                                if valid:
                                    email_final = valid
                                    break

                            # Se nao achou, procurar "(Ver E-mail)" e clicar
                            if not email_final:
                                try:
                                    # Interceptar requisicoes de rede
                                    email_capturado = []
                                    def capturar_response(response):
                                        try:
                                            body = response.text()
                                            encontrados = extract_emails(body)
                                            for e in encontrados:
                                                valid = validar_email(e)
                                                if valid:
                                                    email_capturado.append(valid)
                                        except Exception:
                                            pass

                                    cnpj_page.on("response", capturar_response)

                                    # Scroll ate a secao de contatos com JavaScript
                                    cnpj_page.evaluate("""() => {
                                        const all = document.querySelectorAll('*');
                                        for (const el of all) {
                                            if (el.textContent && el.textContent.includes('E-mail:') && el.children.length < 5) {
                                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                                return;
                                            }
                                        }
                                    }""")
                                    time.sleep(2)

                                    # Agora clicar com Playwright (clique real, nao JS)
                                    clicou = False
                                    try:
                                        # Tentar texto exato "(Ver E-mail)"
                                        el = cnpj_page.locator('text=(Ver E-mail)').first
                                        if el.is_visible(timeout=3000):
                                            el.click(timeout=5000)
                                            clicou = True
                                            print(f"    Clicou com Playwright em (Ver E-mail)")
                                    except Exception:
                                        pass

                                    if not clicou:
                                        try:
                                            el = cnpj_page.locator('text=Ver E-mail').first
                                            if el.is_visible(timeout=3000):
                                                el.click(timeout=5000)
                                                clicou = True
                                                print(f"    Clicou com Playwright em Ver E-mail")
                                        except Exception:
                                            pass

                                    if not clicou:
                                        # Ultima tentativa: clicar em qualquer lugar que tenha o email mascarado
                                        try:
                                            el = cnpj_page.locator('text=Ver').first
                                            if el.is_visible(timeout=2000):
                                                el.click(timeout=3000)
                                                clicou = True
                                                print(f"    Clicou em Ver")
                                        except Exception:
                                            pass

                                    if clicou:
                                        time.sleep(8)

                                        # Capturar via rede
                                        if email_capturado:
                                            email_final = email_capturado[0]
                                            print(f"    [OK] Capturado via rede: {email_final}")
                                        else:
                                            # Capturar do HTML
                                            html = cnpj_page.content()
                                            emails = extract_emails(html)
                                            for e in emails:
                                                valid = validar_email(e)
                                                if valid:
                                                    email_final = valid
                                                    break
                                            if not email_final:
                                                body_text = cnpj_page.inner_text("body")
                                                emails_text = extract_emails(body_text)
                                                for e in emails_text:
                                                    valid = validar_email(e)
                                                    if valid:
                                                        email_final = valid
                                                        break
                                            if email_final:
                                                print(f"    [OK] Capturado: {email_final}")
                                            else:
                                                print(f"    Email nao apareceu apos clique")
                                    else:
                                        print(f"    Botao Ver E-mail nao encontrado")

                                except Exception as e:
                                    print(f"    Erro: {str(e)[:60]}")

                            if email_final:
                                print(f"  [OK] cnpj.biz: {email_final}")
                            cnpj_page.close()
                        except Exception as e:
                            print(f"  [!] cnpj.biz erro: {str(e)[:50]}")

                    # Buscar email direto no Google
                    if not email_final:
                        print(f"  [3e] Buscando email no Google...")
                        try:
                            busca_page.goto(
                                f"https://www.google.com/search?q={nome_limpo}+{cidade}+RJ+email+contato",
                                wait_until="domcontentloaded",
                                timeout=15000,
                            )
                            time.sleep(3)
                            body = busca_page.inner_text("body")
                            emails = extract_emails(body)
                            for e in emails:
                                valid = validar_email(e)
                                if valid:
                                    email_final = valid
                                    print(f"  [OK] Google email: {email_final}")
                                    break
                        except Exception:
                            pass

                else:
                    print(f"  [-] CNPJ nao encontrado")

            # Resultado
            if email_final:
                rows[row_idx]["email"] = email_final
                encontrados += 1
                progress[chave] = {"email": email_final, "status": "ok"}
            else:
                sem_email_total += 1
                progress[chave] = {"email": "", "status": "nao_encontrado"}

            # Salvar progresso
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)

            time.sleep(random.uniform(1, 2))

        browser.close()

    # Salvar CSV atualizado
    fieldnames = list(rows[0].keys())
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL")
    print(f"{'='*60}")
    print(f"Emails encontrados: {encontrados}")
    print(f"Nao encontrados: {sem_email_total}")
    com_total = sum(1 for r in rows if r.get("email"))
    print(f"Total com email: {com_total}/{len(rows)}")


if __name__ == "__main__":
    main()
