"""Diagnostico do campo de pesquisa WhatsApp Web. Abre WhatsApp, aguarda auth, inspeciona DOM, salva JSON."""
import asyncio, json, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
PROFILE_DIR = Path("profiles/whatsapp_match")
OUTPUT_DIR = Path("output/avgestao")
OUTPUT_FILE = OUTPUT_DIR / "diagnostico_search_box_dom.json"


async def main():
    from playwright.async_api import async_playwright
    print("=" * 60)
    print("  DIAGNOSTICO - Campo de pesquisa WhatsApp Web")
    print("=" * 60)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    p = await async_playwright().start()
    ctx = await p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR.resolve()), headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1200, "height": 800}, locale="pt-BR",
    )
    page = await ctx.new_page()
    print("Navegando para web.whatsapp.com...")
    await page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    print("Aguardando autenticacao (ate 3 min)...")
    authenticated = False
    for i in range(36):
        await page.wait_for_timeout(5000)
        body = await page.inner_text("body", timeout=3000)
        body_lower = body.lower()[:500]
        qr_kw = ["escaneie", "conectar", "use o whatsapp", "scan the qr"]
        if not any(kw in body_lower for kw in qr_kw):
            authenticated = True
            print("WhatsApp autenticado!")
            break
        if i % 6 == 0:
            print(f"  Aguardando... ({i * 5}s)")

    if not authenticated:
        print("NAO autenticado (QR visivel)")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(json.dumps({"authenticated": False, "error": "qr_code_visible"}, indent=2), encoding="utf-8")
        await ctx.close(); await p.stop(); return

    print("Aguardando interface carregar (10s)...")
    await page.wait_for_timeout(10000)
    print("Inspecionando DOM...")

    js_code = """() => {
        const results = [];
        const side = document.querySelector('#side');
        const sideInfo = side ? {tag: side.tagName, id: side.id} : null;

        // contenteditable=true
        const ce = document.querySelectorAll('[contenteditable="true"]');
        for (const el of ce) {
            const rect = el.getBoundingClientRect();
            const insideSide = !!side && side.contains(el);
            results.push({
                tag: el.tagName, id: el.id || '',
                role: el.getAttribute('role') || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                title: el.getAttribute('title') || '',
                placeholder: el.getAttribute('placeholder') || '',
                contentEditable: el.getAttribute('contenteditable'),
                dataTestId: el.getAttribute('data-testid') || '',
                dataTab: el.getAttribute('data-tab') || '',
                className: (el.className || '').substring(0, 100),
                insideSide: insideSide,
                visible: rect.width > 0 && rect.height > 0,
                bbox: {x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)},
                ancestors: (() => { let p=el.parentElement, a=[]; for(let i=0;i<5&&p;i++){a.push({tag:p.tagName,id:p.id||'',role:p.getAttribute('role')||''});p=p.parentElement;} return a; })(),
            });
        }

        // role=textbox
        const tb = document.querySelectorAll('[role="textbox"]');
        for (const el of tb) {
            if (!results.some(r => r.tag===el.tagName && r.ariaLabel===(el.getAttribute('aria-label')||''))) {
                const rect = el.getBoundingClientRect();
                const insideSide = !!side && side.contains(el);
                results.push({
                    tag: el.tagName, id: el.id || '', role: el.getAttribute('role') || '',
                    ariaLabel: el.getAttribute('aria-label') || '', title: el.getAttribute('title') || '',
                    contentEditable: el.getAttribute('contenteditable') || '',
                    dataTestId: el.getAttribute('data-testid') || '',
                    insideSide: insideSide, visible: rect.width > 0 && rect.height > 0,
                    bbox: {x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)},
                    source: 'role_textbox',
                });
            }
        }

        // aria-label search
        const sl = document.querySelectorAll('[aria-label*="pesquisar" i], [aria-label*="search" i], [title*="pesquisar" i], [title*="search" i]');
        for (const el of sl) {
            if (!results.some(r => r.tag===el.tagName && r.ariaLabel===(el.getAttribute('aria-label')||''))) {
                const rect = el.getBoundingClientRect();
                const insideSide = !!side && side.contains(el);
                results.push({
                    tag: el.tagName, id: el.id || '', role: el.getAttribute('role') || '',
                    ariaLabel: el.getAttribute('aria-label') || '', title: el.getAttribute('title') || '',
                    contentEditable: el.getAttribute('contenteditable') || '',
                    dataTestId: el.getAttribute('data-testid') || '',
                    insideSide: insideSide, visible: rect.width > 0 && rect.height > 0,
                    bbox: {x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)},
                    source: 'search_label',
                });
            }
        }
        return {side: sideInfo, elements: results, totalCE: ce.length, totalTB: tb.length};
    }"""

    diagnostics = await page.evaluate(js_code)
    diagnostics["timestamp"] = datetime.now(timezone.utc).isoformat()
    diagnostics["authenticated"] = True

    candidates = []
    for el in diagnostics.get("elements", []):
        is_search = el.get("insideSide") and el.get("visible") and (
            el.get("contentEditable") == "true" or el.get("role") == "textbox"
        )
        has_label = any(
            kw in (el.get("ariaLabel", "") + el.get("title", "")).lower()
            for kw in ["pesquisar", "search", "buscar"]
        )
        el["is_search_candidate"] = is_search or has_label
        if el.get("is_search_candidate"):
            candidates.append(el)

    diagnostics["search_candidates"] = candidates
    diagnostics["search_candidate_count"] = len(candidates)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Diagnostico salvo: {OUTPUT_FILE}")
    print(f"Total contenteditable: {diagnostics['totalCE']}")
    print(f"Total role=textbox: {diagnostics['totalTB']}")
    print(f"Candidatos a search: {diagnostics['search_candidate_count']}")

    for i, c in enumerate(candidates):
        print(f"\n  Candidato {i+1}:")
        print(f"    tag={c.get('tag')} role={c.get('role')}")
        print(f"    aria-label={c.get('ariaLabel')} title={c.get('title')}")
        print(f"    data-testid={c.get('dataTestId')} data-tab={c.get('dataTab')}")
        print(f"    ce={c.get('contentEditable')} inside_side={c.get('insideSide')}")
        print(f"    visible={c.get('visible')} bbox={c.get('bbox')}")

    print("\nFechando...")
    await page.wait_for_timeout(3000)
    await ctx.close()
    await p.stop()
    print("Concluido.")


if __name__ == "__main__":
    asyncio.run(main())
