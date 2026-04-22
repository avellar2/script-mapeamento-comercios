"""
Busca emails dos leads do Playwright via CNPJ APIs
=================================================
Playwright pra achar CNPJ no Google + APIs pra email.
"""

import csv
import json
import re
import sys
import time
import random
import requests as req_lib
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent / "output" / "playwright"
CSV_FILE = OUTPUT_DIR / "todos_comercios.csv"
PROGRESS_FILE = OUTPUT_DIR / "progresso_emails_api.json"

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
        ext = "." + email.rsplit(".", 1)[-1] if "." in email else ""
        if ext in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".css"}:
            continue
        if email not in seen:
            seen.add(email)
            valid.append(email)
    return valid


def validar_email(email):
    if not email:
        return ""
    email = str(email).strip().lower()
    if email in BLACKLIST:
        return ""
    if len(email) > 80 or len(email) < 6:
        return ""
    fakes = ["segmenter", "loader", "module", "webpack", "require", "exports"]
    if any(f in email for f in fakes):
        return ""
    if not re.match(r"^[\w.+-]+@[\w.-]+\.[\w]{2,}$", email):
        return ""
    return email


def extract_cnpj(text):
    if not text:
        return ""
    match = re.search(r"(\d{2}\.?\d{3}\.?\d{3}[\/\\]?\d{4}-?\d{2})", text)
    if match:
        cnpj = re.sub(r"[^\d]", "", match.group(1))
        if len(cnpj) == 14:
            return cnpj
    return ""


def limpar_nome(nome):
    n = nome.split("|")[0].split("(")[0].strip()
    n = re.sub(r"\b(amil|hapvida|metlife|primavida|sulamérica|unimed|bradesco)\b.*", "", n, flags=re.I)
    return n.strip()


# === APIs ===

def email_via_receitaws(cnpj):
    url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
    for tentativa in range(3):
        try:
            resp = req_lib.get(url, timeout=10, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email", "")
                if email:
                    for e in email.strip().lower().split(";"):
                        valid = validar_email(e.strip())
                        if valid:
                            return valid
                return ""
            elif resp.status_code == 429:
                time.sleep(30)
                continue
            else:
                return ""
        except Exception:
            time.sleep(5)
    return ""


def email_via_cnpj_ws(cnpj):
    try:
        url = f"https://publica.cnpj.ws/cnpj/{cnpj}"
        resp = req_lib.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            email = (data.get("estabelecimento", {}).get("email")
                     or data.get("email", ""))
            if email:
                return validar_email(email.strip().lower())
    except Exception:
        pass
    return ""


def email_via_brasilapi(cnpj):
    try:
        resp = req_lib.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=10)
        if resp.status_code == 200:
            email = resp.json().get("email", "")
            if email:
                return validar_email(email.strip().lower())
    except Exception:
        pass
    return ""


def email_via_minhareceita(cnpj):
    try:
        resp = req_lib.get(f"https://minhareceita.org/{cnpj}", timeout=10,
                           headers={"Accept": "application/json"})
        if resp.status_code == 200:
            email = resp.json().get("email", "")
            if email:
                return validar_email(email.strip().lower())
    except Exception:
        pass
    return ""


def main():
    print("=" * 60)
    print("BUSCA DE EMAILS - LEADS PLAYWRIGHT (CNPJ APIs)")
    print("=" * 60)

    # Ler CSV
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Carregar progresso anterior do capturar_emails.py
    prog_antigo = {}
    prog_file = OUTPUT_DIR / "progresso_emails.json"
    if prog_file.exists():
        with open(prog_file, encoding="utf-8") as f:
            data = json.load(f)
            for r in data.get("resultados", []):
                key = f"{r['nome'].lower().strip()}|{r.get('cidade','').lower().strip()}"
                email = r.get("email_cnpj", "") or r.get("email_comercial", "")
                if email:
                    prog_antigo[key] = email

    # Atualizar CSV com emails do progresso antigo
    for row in rows:
        key = f"{row['nome'].lower().strip()}|{row.get('cidade','').lower().strip()}"
        if not row.get("email") and key in prog_antigo:
            row["email"] = prog_antigo[key]

    # Filtrar sem site e sem email
    pendentes = []
    for i, row in enumerate(rows):
        tem_site = row.get("tem_site", "False") == "True"
        tem_email = bool(row.get("email"))
        if not tem_site and not tem_email:
            pendentes.append((i, row))

    print(f"Total: {len(rows)} leads")
    print(f"Sem site e sem email: {len(pendentes)}")

    if not pendentes:
        print("Todos tem email!")
        return

    # Carregar progresso deste script
    progresso = {}
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            progresso = json.load(f)
        ja_tem = sum(1 for v in progresso.values() if v.get("email"))
        print(f"Progresso anterior: {ja_tem} emails encontrados")

    encontrados = 0
    sem_email = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)
        busca_page = context.new_page()

        for idx, (row_idx, lead) in enumerate(pendentes):
            nome = lead["nome"]
            cidade = lead.get("cidade", "")
            chave = f"{nome}|{cidade}"

            if chave in progresso:
                email_salvo = progresso[chave].get("email", "")
                if email_salvo:
                    rows[row_idx]["email"] = email_salvo
                    encontrados += 1
                continue

            nome_limpo = limpar_nome(nome)
            cidade_clean = cidade.replace(", RJ", "").replace(",RJ", "").strip()
            print(f"\n[{idx+1}/{len(pendentes)}] {nome_limpo} | {cidade_clean}")

            email_final = ""
            cnpj = ""

            # 1. Buscar CNPJ no Google
            print(f"  [1] Buscando CNPJ no Google...")
            try:
                query = f"{nome_limpo} {cidade_clean} RJ CNPJ"
                busca_page.goto(
                    f"https://www.google.com/search?q={query.replace(' ', '+')}",
                    wait_until="domcontentloaded",
                    timeout=20000,
                )
                time.sleep(3)

                # Cookies
                try:
                    busca_page.click('button:has-text("Aceitar"), button:has-text("Accept all")', timeout=2000)
                    time.sleep(1)
                except Exception:
                    pass

                # CAPTCHA
                body = busca_page.inner_text("body").lower()
                if any(x in body for x in ["tráfego incomum", "unusual traffic", "não sou um robô", "recaptcha"]):
                    print(f"  [!] CAPTCHA! Resolva no navegador...")
                    input(f"  [PAUSA] Resolva e aperte ENTER...")

                body = busca_page.inner_text("body")
                cnpj = extract_cnpj(body)
                if cnpj:
                    print(f"  [OK] CNPJ no Google")
                else:
                    print(f"  [-] CNPJ nao encontrado")
            except Exception as e:
                print(f"  [!] Google erro: {str(e)[:60]}")

            # Fallback DuckDuckGo
            if not cnpj:
                print(f"  [1b] DuckDuckGo...")
                for q in [f'{nome_limpo} {cidade_clean} CNPJ', f'{nome_limpo} CNPJ']:
                    try:
                        ddg_url = f"https://html.duckduckgo.com/html/?q={q.replace(' ', '+')}"
                        resp = req_lib.get(ddg_url, timeout=15, headers={
                            "User-Agent": "Mozilla/5.0 Chrome/136.0.0.0"
                        })
                        if resp.status_code == 200:
                            cnpj = extract_cnpj(resp.text)
                            if cnpj:
                                print(f"  [OK] CNPJ no DuckDuckGo")
                                break
                    except Exception:
                        pass
                    time.sleep(1)

            if cnpj:
                cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
                print(f"  [CNPJ] {cnpj_fmt}")

                # APIs
                print(f"  [2a] ReceitaWS...")
                email_final = email_via_receitaws(cnpj)
                if email_final:
                    print(f"  [OK] {email_final}")

                if not email_final:
                    print(f"  [2b] CNPJ.ws...")
                    email_final = email_via_cnpj_ws(cnpj)
                    if email_final:
                        print(f"  [OK] {email_final}")

                if not email_final:
                    print(f"  [2c] BrasilAPI...")
                    email_final = email_via_brasilapi(cnpj)
                    if email_final:
                        print(f"  [OK] {email_final}")

                if not email_final:
                    print(f"  [2d] MinhaReceita...")
                    email_final = email_via_minhareceita(cnpj)
                    if email_final:
                        print(f"  [OK] {email_final}")

            # Resultado
            if email_final:
                rows[row_idx]["email"] = email_final
                encontrados += 1
                progresso[chave] = {"email": email_final, "status": "ok"}
            else:
                sem_email += 1
                progresso[chave] = {"email": "", "status": "nao_encontrado"}

            # Salvar progresso
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(progresso, f, ensure_ascii=False, indent=2)

            # Salvar CSV atualizado
            fieldnames = list(rows[0].keys())
            with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(rows)

            time.sleep(random.uniform(2, 5))

        browser.close()

    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL")
    print(f"{'='*60}")
    print(f"Emails encontrados: {encontrados}")
    print(f"Nao encontrados: {sem_email}")
    com_total = sum(1 for r in rows if r.get("email"))
    print(f"Total com email: {com_total}/{len(rows)}")


if __name__ == "__main__":
    main()
