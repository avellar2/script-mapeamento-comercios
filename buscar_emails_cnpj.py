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
CSV_FILE = OUTPUT_DIR / "apify" / "leads_apify.csv"
PROGRESS_FILE = OUTPUT_DIR / "apify" / "progresso_emails_cnpj.json"

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
    # Validar formato basico de email (aceita .com.br, .co.uk, etc)
    if not re.match(r"^[\w.+-]+@[\w.-]+\.[\w]{2,}$", email):
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


# === ESTRATEGIA 4: MinhaReceita ===
def email_via_minhareceita(cnpj):
    """Busca email via API minhareceita.org."""
    try:
        url = f"https://minhareceita.org/{cnpj}"
        resp = req_lib.get(url, timeout=10, headers={"Accept": "application/json"})
        if resp.status_code == 200:
            data = resp.json()
            email = data.get("email", "")
            if email:
                valid = validar_email(email.strip().lower())
                if valid:
                    return valid
    except Exception:
        pass
    return ""


# === ESTRATEGIA 5: Bing busca de email ===
def email_via_bing(page, nome, cidade):
    """Busca email direto no Bing."""
    try:
        query = f'"{nome}" {cidade} email contato'
        page.goto(
            f"https://www.bing.com/search?q={query.replace(' ', '+')}",
            wait_until="domcontentloaded",
            timeout=15000,
        )
        time.sleep(2)
        body = page.inner_text("body")
        emails = extract_emails(body)
        for e in emails:
            valid = validar_email(e)
            if valid:
                return valid
    except Exception:
        pass
    return ""


# === ESTRATEGIA 6: Scrape do Google Maps do lead ===
def email_via_gmaps(page, nome, cidade):
    """Busca pagina do Google Maps e extrai email."""
    try:
        query = f"{nome} {cidade}"
        page.goto(
            f"https://www.google.com/search?q={query.replace(' ', '+')}",
            wait_until="domcontentloaded",
            timeout=15000,
        )
        time.sleep(2)

        # Clicar no primeiro resultado de maps
        try:
            link = page.locator('a[href*="maps.google"], a[href*="google.com/maps"]').first
            if link.is_visible(timeout=3000):
                link.click()
                time.sleep(3)
                body = page.inner_text("body")
                emails = extract_emails(body)
                for e in emails:
                    valid = validar_email(e)
                    if valid:
                        return valid
        except Exception:
            pass

        # Se nao clicou, pegar do resultado da busca
        body = page.inner_text("body")
        emails = extract_emails(body)
        for e in emails:
            valid = validar_email(e)
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

                    # ReceitaWS
                    print(f"  [3a] ReceitaWS...")
                    email_final = email_via_receitaws(cnpj)
                    if email_final:
                        print(f"  [OK] ReceitaWS: {email_final}")

                    # CNPJ.ws
                    if not email_final:
                        print(f"  [3b] CNPJ.ws...")
                        email_final = email_via_cnpj_ws(cnpj)
                        if email_final:
                            print(f"  [OK] CNPJ.ws: {email_final}")

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

                    # MinhaReceita
                    if not email_final:
                        print(f"  [3d] MinhaReceita...")
                        email_final = email_via_minhareceita(cnpj)
                        if email_final:
                            print(f"  [OK] MinhaReceita: {email_final}")

                    # cnpj.info
                    if not email_final:
                        print(f"  [3e] cnpj.info...")
                        try:
                            info_page = context.new_page()
                            info_page.goto(f"http://cnpj.info/{cnpj}", timeout=20000)
                            time.sleep(6)
                            if "code.html" in info_page.url:
                                print(f"  [!] cnpj.info bloqueou, pulando...")
                                info_page.close()
                            else:
                                body = info_page.inner_text("body")
                                emails_found = extract_emails(body)
                                for e in emails_found:
                                    valid = validar_email(e)
                                    if valid:
                                        email_final = valid
                                        print(f"  [OK] cnpj.info: {email_final}")
                                        break
                                if not email_final:
                                    print(f"  [-] cnpj.info: sem email")
                                info_page.close()
                                time.sleep(random.uniform(3, 6))
                        except Exception as e:
                            print(f"  [!] cnpj.info: {str(e)[:40]}")
                            try:
                                info_page.close()
                            except Exception:
                                pass

                    # cnpj.biz via Playwright
                    if not email_final:
                        print(f"  [3f] cnpj.biz...")
                        try:
                            biz_page = context.new_page()
                            biz_page.goto(f"https://cnpj.biz/{cnpj}", wait_until="domcontentloaded", timeout=15000)
                            time.sleep(4)
                            biz_page.keyboard.press("Escape")
                            time.sleep(1)

                            # Email direto no HTML
                            html = biz_page.content()
                            emails_found = extract_emails(html)
                            for e in emails_found:
                                valid = validar_email(e)
                                if valid:
                                    email_final = valid
                                    break

                            # Scroll ate email e clicar Ver E-mail
                            if not email_final:
                                try:
                                    biz_page.evaluate("""() => {
                                        const all = document.querySelectorAll('*');
                                        for (const el of all) {
                                            if (el.textContent && (el.textContent.includes('E-mail:') || el.textContent.includes('Ver E-mail')) && el.children.length < 5) {
                                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                                return;
                                            }
                                        }
                                    }""")
                                    time.sleep(2)
                                    el = biz_page.locator('text=Ver E-mail').first
                                    if el.is_visible(timeout=3000):
                                        el.click(timeout=3000)
                                        time.sleep(5)
                                        body2 = biz_page.inner_text("body")
                                        for e in extract_emails(body2):
                                            valid = validar_email(e)
                                            if valid:
                                                email_final = valid
                                                break
                                except Exception:
                                    pass

                            if email_final:
                                print(f"  [OK] cnpj.biz: {email_final}")
                            else:
                                print(f"  [-] cnpj.biz: sem email")
                            biz_page.close()
                        except Exception as e:
                            print(f"  [!] cnpj.biz: {str(e)[:40]}")
                            try:
                                biz_page.close()
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
