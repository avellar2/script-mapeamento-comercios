"""Gera versão standalone do painel de leads quentes com dados embutidos."""
import csv
import json
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"
CSV_FILE = OUTPUT_DIR / "leads_sem_site.csv"
HTML_OUT = Path(__file__).parent / "leads-quentes.html"

leads = []
with open(CSV_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            avaliacao = float(row["avaliacao"]) if row["avaliacao"] else 0
        except ValueError:
            avaliacao = 0
        try:
            num_avaliacoes = int(row["num_avaliacoes"]) if row["num_avaliacoes"] else 0
        except ValueError:
            num_avaliacoes = 0
        score = round(avaliacao * (1 + num_avaliacoes ** 0.5), 2)
        leads.append({
            "n": row["nome"],
            "t": row["telefone"],
            "c": row["categoria"],
            "a": avaliacao,
            "v": num_avaliacoes,
            "ci": row["cidade"].replace(", RJ", ""),
            "s": score,
        })

leads_json = json.dumps(leads, ensure_ascii=False, separators=(",", ":"))
print(f"  {len(leads)} leads embarcados ({len(leads_json) // 1024} KB)")

html = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Leads Quentes - Baixada Fluminense</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg-deep:#0a0a0b;--bg-card:#141416;--bg-elevated:#1a1a1d;
  --accent:#f97316;--accent-glow:rgba(249,115,22,.3);
  --cyan:#22d3ee;--green:#22c55e;--red:#ef4444;--yellow:#f59e0b;
  --text:#fafafa;--text2:#a1a1aa;--muted:#71717a;
  --border:rgba(255,255,255,.06);--border-active:rgba(249,115,22,.5);
  --grad:linear-gradient(135deg,#f97316 0%,#fb923c 50%,#22d3ee 100%);
}
body{font-family:'Outfit',sans-serif;background:var(--bg-deep);color:var(--text);min-height:100vh;line-height:1.6}
.bg-mesh{position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.4;
  background-image:
    radial-gradient(ellipse at 15% 15%,rgba(249,115,22,.1) 0%,transparent 50%),
    radial-gradient(ellipse at 85% 85%,rgba(239,68,68,.06) 0%,transparent 50%),
    radial-gradient(ellipse at 50% 50%,rgba(249,115,22,.04) 0%,transparent 70%)}
.container{position:relative;z-index:1;max-width:1600px;margin:0 auto;padding:0 24px}

/* Header */
header{padding:40px 0;border-bottom:1px solid var(--border);margin-bottom:32px}
.header-content{display:flex;justify-content:space-between;align-items:flex-start;gap:40px;flex-wrap:wrap}
.header-title h1{font-family:'Space Grotesk',sans-serif;font-size:clamp(2rem,5vw,3.2rem);font-weight:700;
  letter-spacing:-.02em;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;margin-bottom:4px}
.header-title p{color:var(--text2);font-size:1rem}
.stats-bar{display:flex;gap:32px;margin-top:20px;flex-wrap:wrap}
.stat-item{display:flex;flex-direction:column}
.stat-value{font-family:'Space Grotesk',sans-serif;font-size:1.8rem;font-weight:700;color:var(--accent);line-height:1}
.stat-label{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-top:4px}

/* Heat legend */
.heat-legend{display:flex;align-items:center;gap:8px;font-size:.75rem;color:var(--text2);
  background:var(--bg-card);padding:12px 20px;border-radius:10px;border:1px solid var(--border);margin-left:auto;align-self:flex-end}
.heat-bar{width:120px;height:8px;border-radius:4px;
  background:linear-gradient(90deg,#3b82f6,#22c55e,#f59e0b,#ef4444)}

/* Filters */
.filters{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:28px;padding:20px 24px;
  background:var(--bg-card);border-radius:14px;border:1px solid var(--border);align-items:flex-end}
.filter-group{display:flex;flex-direction:column;gap:6px}
.filter-group label{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:500}
.filter-select,.filter-input{background:var(--bg-elevated);border:1px solid var(--border);border-radius:8px;
  padding:9px 14px;color:var(--text);font-family:'Outfit',sans-serif;font-size:.85rem;cursor:pointer;
  transition:all .2s;min-width:150px}
.filter-select:hover,.filter-input:hover{border-color:var(--border-active)}
.filter-select:focus,.filter-input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow)}
.search-box{flex:1;min-width:240px}
.search-input{width:100%;background:var(--bg-elevated);border:1px solid var(--border);border-radius:8px;
  padding:9px 14px;color:var(--text);font-family:'Outfit',sans-serif;font-size:.85rem;transition:all .2s}
.search-input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow)}
.filter-checkbox{display:flex;align-items:center;gap:8px;font-size:.85rem;color:var(--text2);cursor:pointer;padding-bottom:2px}
.filter-checkbox input{accent-color:var(--accent);width:16px;height:16px}

/* Results */
.results-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.results-count{font-size:.95rem;color:var(--text2)}
.results-count strong{color:var(--accent);font-weight:600}
.sort-btn{background:var(--bg-elevated);border:1px solid var(--border);border-radius:8px;padding:8px 14px;
  color:var(--text2);font-family:'Outfit',sans-serif;font-size:.8rem;cursor:pointer;transition:all .2s}
.sort-btn:hover{border-color:var(--accent);color:var(--text)}
.sort-btn.active{border-color:var(--accent);color:var(--accent)}

/* Grid */
.leads-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px;margin-bottom:60px}

/* Card */
.card{background:var(--bg-card);border-radius:14px;border:1px solid var(--border);overflow:hidden;
  transition:all .3s cubic-bezier(.4,0,.2,1);position:relative;opacity:0;animation:fadeUp .45s ease forwards}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;opacity:0;transition:opacity .3s}
.card:hover{transform:translateY(-4px);border-color:var(--border-active);
  box-shadow:0 16px 40px rgba(0,0,0,.3),0 0 50px var(--accent-glow)}
.card:hover::before{opacity:1}
.card.heat-fire::before{background:linear-gradient(90deg,#f97316,#ef4444)}
.card.heat-warm::before{background:linear-gradient(90deg,#f59e0b,#f97316)}
.card.heat-cool::before{background:linear-gradient(90deg,#22c55e,#22d3ee)}

.card-top{padding:16px 18px 0;display:flex;justify-content:space-between;align-items:center;gap:8px}
.card-tags{display:flex;gap:6px;flex-wrap:wrap}
.tag{font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;padding:3px 9px;border-radius:100px;font-weight:600}
.tag-cat{background:var(--bg-elevated);color:var(--accent)}
.tag-city{background:rgba(34,211,238,.1);color:var(--cyan)}
.heat-badge{font-size:.65rem;padding:3px 9px;border-radius:100px;font-weight:700;letter-spacing:.05em}
.heat-badge.fire{background:rgba(239,68,68,.15);color:#ef4444}
.heat-badge.warm{background:rgba(249,115,22,.15);color:#f97316}
.heat-badge.cool{background:rgba(34,197,94,.15);color:#22c55e}

.card-body{padding:10px 18px 18px}
.card-name{font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;line-height:1.3;margin-bottom:10px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-meta{display:flex;flex-direction:column;gap:8px}
.meta-row{display:flex;align-items:center;gap:8px;font-size:.85rem;color:var(--text2)}
.meta-icon{width:16px;height:16px;flex-shrink:0;opacity:.5}
.meta-icon svg{width:100%;height:100%}
.phone-link{color:var(--cyan);text-decoration:none;transition:color .2s}
.phone-link:hover{color:#fff;text-decoration:underline}

/* Rating stars */
.stars{display:flex;align-items:center;gap:3px}
.star{font-size:.85rem}
.star.filled{color:var(--yellow)}
.star.empty{color:var(--muted);opacity:.3}
.rating-num{font-weight:600;color:var(--text);margin-left:4px;font-size:.85rem}
.review-count{color:var(--muted);font-size:.75rem;margin-left:2px}

/* Score bar */
.score-bar{height:4px;background:var(--bg-elevated);border-radius:2px;margin-top:10px;overflow:hidden}
.score-fill{height:100%;border-radius:2px;transition:width .5s ease}

/* Pagination */
.pagination{display:flex;justify-content:center;gap:8px;margin:20px 0 40px;flex-wrap:wrap}
.page-btn{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:8px 16px;
  color:var(--text2);font-family:'Outfit',sans-serif;font-size:.85rem;cursor:pointer;transition:all .2s}
.page-btn:hover{border-color:var(--accent);color:var(--text)}
.page-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.page-info{display:flex;align-items:center;color:var(--muted);font-size:.85rem;padding:0 8px}

/* Empty */
.empty-state{text-align:center;padding:80px 20px;color:var(--muted);grid-column:1/-1}
.empty-state h3{font-family:'Space Grotesk',sans-serif;font-size:1.4rem;color:var(--text2);margin-bottom:6px}

/* Animations */
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}

/* Footer */
footer{padding:32px 0;border-top:1px solid var(--border);text-align:center;color:var(--muted);font-size:.85rem}

/* Responsive */
@media(max-width:768px){
  .header-content{flex-direction:column}
  .heat-legend{margin-left:0}
  .stats-bar{gap:20px}
  .filters{padding:14px}
  .filter-select,.search-box{min-width:100%}
  .leads-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="bg-mesh"></div>
<div class="container">
  <header>
    <div class="header-content">
      <div class="header-title">
        <h1>Leads Quentes</h1>
        <p>Comercios sem site com maior potencial de conversao - Baixada Fluminense</p>
        <div class="stats-bar" id="statsBar">
          <div class="stat-item"><span class="stat-value" id="statTotal">-</span><span class="stat-label">Leads</span></div>
          <div class="stat-item"><span class="stat-value" id="statPhone">-</span><span class="stat-label">Com Telefone</span></div>
          <div class="stat-item"><span class="stat-value" id="statHot">-</span><span class="stat-label">Quentes</span></div>
          <div class="stat-item"><span class="stat-value" id="statCities">-</span><span class="stat-label">Cidades</span></div>
          <div class="stat-item"><span class="stat-value" id="statCats">-</span><span class="stat-label">Categorias</span></div>
        </div>
      </div>
      <div class="heat-legend">
        <span>Frio</span><div class="heat-bar"></div><span>Quente</span>
      </div>
    </div>
  </header>

  <section class="filters">
    <div class="filter-group search-box">
      <label>Buscar</label>
      <input type="text" class="search-input" id="searchInput" placeholder="Nome do comercio...">
    </div>
    <div class="filter-group">
      <label>Cidade</label>
      <select class="filter-select" id="cityFilter"><option value="">Todas</option></select>
    </div>
    <div class="filter-group">
      <label>Categoria</label>
      <select class="filter-select" id="catFilter"><option value="">Todas</option></select>
    </div>
    <div class="filter-group">
      <label>Nota minima</label>
      <select class="filter-select" id="ratingFilter">
        <option value="">Qualquer</option>
        <option value="4.5">4.5+</option>
        <option value="4">4.0+</option>
        <option value="3">3.0+</option>
      </select>
    </div>
    <div class="filter-group">
      <label>&nbsp;</label>
      <label class="filter-checkbox"><input type="checkbox" id="phoneOnly"> Somente com telefone</label>
    </div>
    <div class="filter-group">
      <label>Ordenar por</label>
      <select class="filter-select" id="sortSelect">
        <option value="score">Score (mais quente)</option>
        <option value="rating">Nota</option>
        <option value="reviews">Avaliacoes</option>
        <option value="name">Nome A-Z</option>
      </select>
    </div>
  </section>

  <section class="results-header">
    <p class="results-count">Mostrando <strong id="visibleCount">0</strong> de <strong id="totalFiltered">0</strong> leads</p>
  </section>

  <main class="leads-grid" id="leadsGrid"></main>

  <div class="pagination" id="pagination"></div>

  <footer>
    <p>Dados coletados via Google Maps | Baixada Fluminense, RJ</p>
  </footer>
</div>

<script>
const DATA = __LEADS_DATA__;
const PER_PAGE = 48;
let currentPage = 1;
let filtered = [];

const icons = {
  phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg>',
  pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>',
};

function init() {
  populateFilters();
  updateStats();
  applyFilters();
  bindEvents();
}

function populateFilters() {
  const cities = [...new Set(DATA.map(l => l.ci))].sort();
  const cats = [...new Set(DATA.map(l => l.c))].sort();
  const cf = document.getElementById('cityFilter');
  const caf = document.getElementById('catFilter');
  cities.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; cf.appendChild(o); });
  cats.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; caf.appendChild(o); });
}

function updateStats() {
  anim('statTotal', DATA.length);
  anim('statPhone', DATA.filter(l => l.t).length);
  anim('statHot', DATA.filter(l => l.a >= 4.5 && l.t).length);
  anim('statCities', new Set(DATA.map(l => l.ci)).size);
  anim('statCats', new Set(DATA.map(l => l.c)).size);
}

function anim(id, target) {
  const el = document.getElementById(id);
  const start = performance.now();
  (function tick(now) {
    const p = Math.min((now - start) / 800, 1);
    el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3))).toLocaleString('pt-BR');
    if (p < 1) requestAnimationFrame(tick);
  })(start);
}

function applyFilters() {
  const q = document.getElementById('searchInput').value.toLowerCase();
  const city = document.getElementById('cityFilter').value;
  const cat = document.getElementById('catFilter').value;
  const minR = parseFloat(document.getElementById('ratingFilter').value) || 0;
  const phoneOnly = document.getElementById('phoneOnly').checked;
  const sort = document.getElementById('sortSelect').value;

  filtered = DATA.filter(l => {
    if (q && !l.n.toLowerCase().includes(q)) return false;
    if (city && l.ci !== city) return false;
    if (cat && l.c !== cat) return false;
    if (minR && l.a < minR) return false;
    if (phoneOnly && !l.t) return false;
    return true;
  });

  filtered.sort((a, b) => {
    if (sort === 'score') return b.s - a.s;
    if (sort === 'rating') return b.a - a.a;
    if (sort === 'reviews') return b.v - a.v;
    return a.n.localeCompare(b.n);
  });

  currentPage = 1;
  render();
}

function heat(a) { return a >= 4.8 ? 'fire' : a >= 4.3 ? 'warm' : 'cool'; }
function heatLabel(a) { return a >= 4.8 ? 'FOGO' : a >= 4.3 ? 'MORNO' : 'FRIO'; }
function scoreColor(s) {
  const max = 25;
  const pct = Math.min(s / max, 1);
  if (pct > .7) return 'linear-gradient(90deg,#f97316,#ef4444)';
  if (pct > .4) return 'linear-gradient(90deg,#f59e0b,#f97316)';
  return 'linear-gradient(90deg,#22c55e,#22d3ee)';
}

function stars(r) {
  let h = '';
  for (let i = 1; i <= 5; i++) h += `<span class="star ${i <= Math.round(r) ? 'filled' : 'empty'}">&#9733;</span>`;
  return h;
}

function render() {
  const grid = document.getElementById('leadsGrid');
  const total = filtered.length;
  const pages = Math.ceil(total / PER_PAGE);
  const start = (currentPage - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);

  document.getElementById('totalFiltered').textContent = total.toLocaleString('pt-BR');
  document.getElementById('visibleCount').textContent = page.length.toLocaleString('pt-BR');

  if (!total) {
    grid.innerHTML = '<div class="empty-state"><h3>Nenhum lead encontrado</h3><p>Ajuste os filtros para ver resultados.</p></div>';
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  const maxScore = Math.max(...filtered.slice(0, 50).map(l => l.s), 1);

  grid.innerHTML = page.map((l, i) => {
    const h = heat(l.a);
    const scPct = Math.min((l.s / maxScore) * 100, 100);
    return `<article class="card heat-${h}" style="animation-delay:${i * 25}ms">
      <div class="card-top">
        <div class="card-tags">
          <span class="tag tag-cat">${esc(l.c)}</span>
          <span class="tag tag-city">${esc(l.ci)}</span>
        </div>
        <span class="heat-badge ${h}">${heatLabel(l.a)}</span>
      </div>
      <div class="card-body">
        <div class="card-name">${esc(l.n)}</div>
        <div class="card-meta">
          <div class="meta-row">
            <span class="meta-icon">${icons.phone}</span>
            ${l.t ? `<a href="tel:${l.t.replace(/\D/g,'')}" class="phone-link">${esc(l.t)}</a>` : '<span style="color:var(--muted)">Sem telefone</span>'}
          </div>
          <div class="meta-row">
            <span class="meta-icon">${icons.pin}</span>
            <span>${esc(l.ci)}</span>
          </div>
          <div class="meta-row">
            <div class="stars">${stars(l.a)}</div>
            <span class="rating-num">${l.a.toFixed(1)}</span>
            ${l.v ? `<span class="review-count">(${l.v})</span>` : ''}
          </div>
        </div>
        <div class="score-bar"><div class="score-fill" style="width:${scPct}%;background:${scoreColor(l.s)}"></div></div>
      </div>
    </article>`;
  }).join('');

  // Pagination
  const pag = document.getElementById('pagination');
  if (pages <= 1) { pag.innerHTML = ''; return; }
  let ph = '';
  if (currentPage > 1) ph += `<button class="page-btn" onclick="goPage(${currentPage - 1})">&laquo; Anterior</button>`;
  const range = getPageRange(currentPage, pages);
  range.forEach(p => {
    if (p === '...') ph += `<span class="page-info">...</span>`;
    else ph += `<button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="goPage(${p})">${p}</button>`;
  });
  if (currentPage < pages) ph += `<button class="page-btn" onclick="goPage(${currentPage + 1})">Proximo &raquo;</button>`;
  pag.innerHTML = ph;
}

function getPageRange(cur, total) {
  if (total <= 7) return Array.from({length: total}, (_, i) => i + 1);
  const r = [];
  r.push(1);
  if (cur > 3) r.push('...');
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) r.push(i);
  if (cur < total - 2) r.push('...');
  r.push(total);
  return r;
}

function goPage(p) { currentPage = p; render(); window.scrollTo({top: 260, behavior: 'smooth'}); }

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

function bindEvents() {
  document.getElementById('searchInput').addEventListener('input', debounce(applyFilters, 250));
  ['cityFilter','catFilter','ratingFilter','sortSelect'].forEach(id =>
    document.getElementById(id).addEventListener('change', applyFilters));
  document.getElementById('phoneOnly').addEventListener('change', applyFilters);
}

init();
</script>
</body>
</html>"""

html = html.replace("__LEADS_DATA__", leads_json, 1)
HTML_OUT.write_text(html, encoding="utf-8")
print(f"\n  Salvo em: {HTML_OUT}")
print(f"  Tamanho: {len(html) // 1024} KB")
print("  Abra no navegador para usar!")
