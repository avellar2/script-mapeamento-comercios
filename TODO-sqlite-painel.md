# TODO - Painel de Prospecção: Persistir status no SQLite

## O que foi feito
- Criado `db.py` com SQLite (tabelas `leads`, `metricas_acumuladas`, `rodadas`)
- Atualizado `server.py` com endpoints `/api/leads`, `/api/metricas`, `/api/status-single`
- Atualizado `gerar_painel_prospeccao.py` para usar SQLite
- JavaScript do painel atualizado para chamar `/api/status-single` ao clicar nos botões de status

## O que NÃO está funcionando
O status clicado no painel NÃO está salvando no SQLite. Os contadores ficam em 0.

## O que falta fazer

### 1. Limpar localStorage do navegador
O painel ainda lê o localStorage primeiro. Quando abrir o painel, aperte F12 > Console e digite:
```
allow pasting
```
Enter, depois:
```js
localStorage.removeItem('prospeccao_status_v2'); location.reload();
```

### 2. Verificar se o servidor está rodando a versão nova do `server.py`
O `server.py` foi atualizado com SQLite mas pode estar rodando a versão antiga. Para garantir:
```bash
# Matar processo python antigo
taskkill /f /im python.exe

# Rodar o servidor novo
cd C:\Users\Vanderson\Documents\script-mapeamento-comercios\output\painel
python server.py
```

### 3. Verificar se o JavaScript do painel está chamando a API
Abrir F12 > Network no navegador. Clicar em "Mensagem enviada" num lead. Verificar se aparece:
- POST para `/api/status-single` com status 200
- Se der erro 404, o servidor antigo está rodando
- Se der erro de CORS, adicionar headers no server.py

### 4. Verificar se `render()` e `getFiltered()` são async
No `gerar_painel_prospeccao.py`, o JavaScript precisa ter:
- `async function render()` em vez de `function render()`
- `async function getFiltered()` em vez de `function getFiltered()`
- `const status = await loadStatus();` em vez de `const status = loadStatus();`
- `const filtered = await getFiltered();` em vez de `const filtered = getFiltered();`

Já foi trocado, mas confirmar que está no HTML gerado.

### 5. Verificar se `setStatus` está chamando a API
No HTML gerado, os botões chamam `setStatus(leadId, 'status', 'mensagem enviada')`. A função `setStatus` agora é async e faz POST para `/api/status-single`. Confirmar que o POST está sendo enviado.

### 6. Testar manualmente
```bash
# Verificar se o SQLite está recebendo dados
cd C:\Users\Vanderson\Documents\script-mapeamento-comercios\output\painel
python -c "import db; conn = db.get_conn(); rows = conn.execute('SELECT lead_id, nome, status FROM leads').fetchall(); [print(f'{r[1]:40s} | {r[2]}') for r in rows]; conn.close()"
```

Depois de clicar em "Mensagem enviada" num lead, rodar o comando acima e verificar se o status mudou de "novo" para "mensagem enviada".

### 7. Métricas acumuladas
Após cada mudança de status, o SQLite recalcula as métricas automaticamente via `recalcular_metricas()`. Verificar:
```bash
python -c "import db; conn = db.get_conn(); m = db.get_metricas(conn); print(m); conn.close()"
```

### Arquivos modificados
- `output/painel/db.py` — NOVO, módulo SQLite
- `output/painel/server.py` — Atualizado com endpoints SQLite
- `gerar_painel_prospeccao.py` — Atualizado para usar SQLite + async JS

### Arquivos que podem ser removidos depois
- `output/painel/status_leads.json` — Substituído pelo SQLite
- `output/painel/historico_leads.json` — Substituído pelo SQLite