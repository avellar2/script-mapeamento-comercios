"""
Mapeador de Comércios - Duque de Caxias, RJ
=============================================
Busca comércios no Google Maps que NÃO possuem site,
gerando uma planilha de leads para prospecção.

Uso: python mapear_comercios.py
"""

import asyncio
import csv
import json
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CITY = "Duque de Caxias, RJ"
MAX_RESULTS_PER_CATEGORY = 20  # Reduzido para ser mais rápido
DELAY_MIN = 2.0
DELAY_MAX = 5.0

CATEGORIAS = [
    "restaurante",
    "salão de beleza",
    "barbearia",
    "clínica médica",
    "oficina mecânica",
    "pet shop",
    "loja de roupas",
    "padaria",
    "pizzaria",
    "bar",
    "farmácia",
    "dentista",
    "advogado",
    "contador",
    "imobiliária",
    "academia",
    "lanchonete",
    "supermercado",
    "material de construção",
    "auto escola",
    "lavanderia",
    "floricultura",
    "ótica",
    "joalheria",
    "clínica veterinária",
    "estética",
    "loja de celulares",
    "loja de móveis",
    "papelaria",
    "loja de bicicleta",
    "confeitaria",
    "serralheria",
    "vidraçaria",
    "pintor",
    "eletricista",
    "encanador",
    "marcenaria",
    "escola de idiomas",
    "curso pré-vestibular",
    "estúdio de pilates",
]

PROGRESS_FILE = OUTPUT_DIR / "progresso.json"


# ── Progress / Resume ──────────────────────────────────────────────

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categorias_prontas": [], "categorias_em_andamento": {}, "comercios": []}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ── Export ──────────────────────────────────────────────────────────

def export_csv(businesses, filename):
    filepath = OUTPUT_DIR / filename
    fieldnames = [
        "nome", "endereco", "telefone", "categoria",
        "tem_site", "url_site", "avaliacao", "num_avaliacoes",
    ]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(businesses)
    return filepath


def export_excel(businesses, filename):
    """Exporta para .xlsx (requer openpyxl)."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = "Leads sem Site"

        headers = [
            "Nome", "Endereço", "Telefone", "Categoria",
            "Tem Site?", "URL do Site", "Avaliação", "Nº Avaliações",
        ]
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="2563EB")
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for row_idx, b in enumerate(businesses, 2):
            ws.cell(row=row_idx, column=1, value=b["nome"])
            ws.cell(row=row_idx, column=2, value=b["endereco"])
            ws.cell(row=row_idx, column=3, value=b["telefone"])
            ws.cell(row=row_idx, column=4, value=b["categoria"])
            ws.cell(row=row_idx, column=5, value="Sim" if b["tem_site"] else "NÃO")
            ws.cell(row=row_idx, column=6, value=b["url_site"])
            ws.cell(row=row_idx, column=7, value=b["avaliacao"])
            ws.cell(row=row_idx, column=8, value=b["num_avaliacoes"])

            # Destaca leads sem site em amarelo
            if not b["tem_site"]:
                highlight = PatternFill("solid", fgColor="FEF08A")
                for col in range(1, 9):
                    ws.cell(row=row_idx, column=col).fill = highlight

        # Ajusta largura das colunas
        widths = [35, 45, 18, 25, 10, 35, 10, 12]
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

        filepath = OUTPUT_DIR / filename
        wb.save(filepath)
        return filepath
    except ImportError:
        print("  [!] openpyxl não instalado — exportando CSV apenas")
        return None


# ── Google Maps Scraper ────────────────────────────────────────────

async def aceitar_cookies(page):
    """Clica no botão de aceitar cookies do Google, se aparecer."""
    for selector in [
        'button[aria-label*="Aceitar"]',
        'button[aria-label*="Accept"]',
        'button[aria-label*="accept all"]',
        'form:nth-of-type(2) button',
    ]:
        btn = page.locator(selector).first
        if await btn.count() > 0:
            try:
                await btn.click(timeout=2000)
                await asyncio.sleep(1)
                return True
            except Exception:
                pass
    return False


async def scroll_panel(page, max_scrolls=25):
    """Rola o painel de resultados para carregar mais comércios."""
    panel = page.locator('div[role="feed"]').first
    if await panel.count() == 0:
        return
    for _ in range(max_scrolls):
        await panel.evaluate("el => el.scrollBy(0, 800)")
        await asyncio.sleep(random.uniform(0.3, 0.8))
        fim = page.locator(
            'span:has-text("fim da lista"), span:has-text("end of the list")'
        )
        if await fim.count() > 0:
            break


async def extrair_detalhes(page, categoria):
    """Extrai dados de um comércio na página de detalhes aberta."""
    await page.wait_for_timeout(1500)

    dados = {
        "nome": "",
        "endereco": "",
        "telefone": "",
        "categoria": categoria,
        "tem_site": False,
        "url_site": "",
        "avaliacao": "",
        "num_avaliacoes": "",
    }

    # Nome
    for sel in ['h1.DUwDvf', 'h1[class*="fontHeadline"]', 'h1']:
        el = page.locator(sel).first
        if await el.count() > 0:
            txt = (await el.inner_text()).strip()
            if txt:
                dados["nome"] = txt
                break

    if not dados["nome"]:
        return None

    # Avaliação
    rating_el = page.locator('div[role="img"][aria-label*="estrela"], div[role="img"][aria-label*="star"]').first
    if await rating_el.count() > 0:
        label = await rating_el.get_attribute("aria-label") or ""
        m = re.search(r"([\d,.]+)", label)
        if m:
            dados["avaliacao"] = m.group(1).replace(",", ".")

    # Nº avaliações
    reviews_el = page.locator('button[aria-label*="avaliação"], button[aria-label*="review"]').first
    if await reviews_el.count() > 0:
        txt = await reviews_el.inner_text()
        dados["num_avaliacoes"] = re.sub(r"\D", "", txt)

    # Endereço
    addr_el = page.locator(
        'button[data-item-id*="address"], button[aria-label*="Endereço"], '
        'button[aria-label*="Address"]'
    ).first
    if await addr_el.count() > 0:
        dados["endereco"] = (await addr_el.inner_text()).strip()

    # Telefone
    phone_el = page.locator(
        'button[data-item-id*="phone:tel"], button[aria-label*="Telefone"], '
        'button[aria-label*="Phone"]'
    ).first
    if await phone_el.count() > 0:
        dados["telefone"] = (await phone_el.inner_text()).strip()

    # Website
    web_el = page.locator(
        'a[data-item-id*="authority"], a[aria-label*="Site"], '
        'a[aria-label*="Website"], a[aria-label*="site oficial"]'
    ).first
    if await web_el.count() > 0:
        dados["tem_site"] = True
        dados["url_site"] = (await web_el.get_attribute("href")) or ""

    return dados


async def buscar_categoria(page, categoria, start_index=0, progress=None):
    """Busca uma categoria no Google Maps e retorna lista de comércios."""
    query = f"{categoria} em {CITY}"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}/"

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"  [!] Erro ao carregar: {e}")
        try:
            await page.reload(wait_until="commit", timeout=30000)
        except Exception:
            pass

    await asyncio.sleep(random.uniform(2, 3))
    await aceitar_cookies(page)
    await asyncio.sleep(2)

    # Rola para carregar mais
    await scroll_panel(page)
    await asyncio.sleep(1)

    # Captura todos os resultados
    items = page.locator('div[role="feed"] > div > div[jsaction], div[role="feed"] > div > a[jsaction]')
    total = await items.count()
    print(f"  > {total} resultados encontrados")

    comercios = []
    limite = min(total, MAX_RESULTS_PER_CATEGORY)

    # Se está continuando de onde parou
    if start_index > 0:
        print(f"  > Continuando do indice {start_index}...")

    for i in range(start_index, limite):
        try:
            # Recarrega os itens a cada iteração (o DOM pode mudar)
            items = page.locator('div[role="feed"] > div > div[jsaction], div[role="feed"] > div > a[jsaction]')

            if await items.count() <= i:
                print(f"    [{i+1}] Itens reduzidos, recarregando pagina...")
                await scroll_panel(page)
                await asyncio.sleep(1)
                items = page.locator('div[role="feed"] > div > div[jsaction], div[role="feed"] > div > a[jsaction]')
                if await items.count() <= i:
                    break

            item = items.nth(i)
            await item.click(timeout=5000)
            await asyncio.sleep(random.uniform(1.8, 3.5))

            dados = await extrair_detalhes(page, categoria)
            if dados:
                comercios.append(dados)
                tag = "COM site" if dados["tem_site"] else "SEM site"
                print(f"    [{i+1}/{limite}] {tag} - {dados['nome'][:40]}")

                # Salva progresso incrementalmente
                if progress:
                    progress["categorias_em_andamento"][categoria] = {"indice": i + 1, "total": limite}
                    progress["comercios"].extend(comercios)
                    comercios.clear()  # Limpa a lista local já que salvou no progress
                    save_progress(progress)

            # Volta para resultados - TENTATIVA 1: botão voltar
            voltou = False
            for _ in range(2):
                try:
                    back = page.locator('button[aria-label*="Voltar"], button[aria-label*="Back"]').first
                    if await back.count() > 0:
                        await back.click(timeout=3000)
                        await asyncio.sleep(0.5)
                        voltou = True
                        break
                except Exception:
                    pass

                # TENTATIVA 2: go_back
                try:
                    await page.go_back(timeout=3000)
                    await asyncio.sleep(0.5)
                    voltou = True
                    break
                except Exception:
                    pass

            if not voltou:
                # TENTATIVA 3: recarrega a URL de busca
                print(f"    [{i+1}] Navegacao travada, recarregando...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                await scroll_panel(page, max_scrolls=5)
                await asyncio.sleep(1)

            await asyncio.sleep(random.uniform(0.8, 1.5))

        except Exception as e:
            print(f"    [{i+1}/{limite}] Erro: {str(e)[:50]}")
            # Salva onde parou mesmo com erro
            if progress:
                progress["categorias_em_andamento"][categoria] = {"indice": i + 1, "total": limite}
                save_progress(progress)
            # Tenta recuperar navegacao
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(2)
            except Exception:
                pass
            continue

    return comercios


# ── Main ────────────────────────────────────────────────────────────

async def main():
    # Força UTF-8 no Windows
    if sys.platform == "win32":
        import locale
        import codecs
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[!] Playwright não encontrado. Instalando...")
        os.system(f"{sys.executable} -m pip install playwright")
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.async_api import async_playwright

    print("=" * 60)
    print("  MAPEADOR DE COMÉRCIOS — DUQUE DE CAXIAS, RJ")
    print("  Buscando comércios SEM site para prospecção")
    print("=" * 60)

    progress = load_progress()
    feitas = set(progress.get("categorias_prontas", []))
    em_andamento = progress.get("categorias_em_andamento", {})
    todos = progress.get("comercios", [])

    # Adiciona categorias em andamento às restantes (para continuar)
    restantes = [c for c in CATEGORIAS if c not in feitas]
    print(f"\nCategorias restantes: {len(restantes)}/{len(CATEGORIAS)}")
    print(f"Comércios já mapeados: {len(todos)}")
    if em_andamento:
        print(f"Em andamento: {list(em_andamento.keys())}\n")

    if not restantes and not em_andamento:
        print("Todas as categorias já foram buscadas!")
        print("Delete output/progresso.json para recomeçar.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()

        # Abre o Google Maps e aceita cookies iniciais
        try:
            await page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"[!] Timeout ao carregar Maps. Tentando novamente... ({e})")
            await page.goto("https://www.google.com/maps", wait_until="commit", timeout=30000)
        await asyncio.sleep(3)
        await aceitar_cookies(page)
        await asyncio.sleep(1)

        for idx, cat in enumerate(restantes):
            print(f"\n[{idx+1}/{len(restantes)}] Buscando: {cat}")

            # Verifica se já estava em andamento
            start_idx = 0
            if cat in em_andamento:
                start_idx = em_andamento[cat].get("indice", 0)
                print(f"  > Continuando do índice {start_idx}")

            try:
                resultados = await buscar_categoria(page, cat, start_index=start_idx, progress=progress)

                # Marca categoria como completa
                if cat in em_andamento:
                    del em_andamento[cat]
                feitas.add(cat)
                progress["categorias_prontas"] = list(feitas)
                progress["categorias_em_andamento"] = em_andamento
                save_progress(progress)

                # Conta sem site (do progresso atualizado)
                sem = sum(1 for c in progress["comercios"] if c["categoria"] == cat and not c["tem_site"])
                todos_categoria = [c for c in progress["comercios"] if c["categoria"] == cat]
                print(f"  > {len(todos_categoria)} encontrados | {sem} sem site")

            except Exception as e:
                print(f"  X Erro geral: {e}")
                # Tenta navegar de volta ao Maps
                try:
                    await page.goto("https://www.google.com/maps", wait_until="commit", timeout=15000)
                except Exception:
                    pass
                continue

            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            print(f"  Aguardando {delay:.1f}s...")
            await asyncio.sleep(delay)

        await browser.close()

    # ── Exporta resultados ──────────────────────────────────────────
    # Recarrega o progresso para ter dados atualizados
    progress = load_progress()
    todos = progress.get("comercios", [])

    if not todos:
        print("\nNenhum comércio encontrado.")
        return

    # Todos os comércios
    export_csv(todos, "todos_comercios.csv")
    print(f"\n✓ CSV completo: output/todos_comercios.csv")

    # Leads sem site
    sem_site = [c for c in todos if not c["tem_site"]]
    if sem_site:
        export_csv(sem_site, "leads_sem_site.csv")
        print(f"✓ CSV leads:    output/leads_sem_site.csv")

        xlsx = export_excel(sem_site, "leads_sem_site.xlsx")
        if xlsx:
            print(f"✓ Excel leads:  {xlsx}")

    # Resumo
    com_site = len(todos) - len(sem_site)
    taxa = (len(sem_site) / len(todos) * 100) if todos else 0
    print(f"\n{'='*50}")
    print(f"  RESUMO FINAL")
    print(f"  Total mapeados:     {len(todos)}")
    print(f"  COM site:           {com_site}")
    print(f"  SEM site (leads):   {len(sem_site)}")
    print(f"  Taxa de prospecção: {taxa:.1f}%")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
