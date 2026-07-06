# Cross-PC Resume Workflow

**Contexto:** Vanderson trabalha em casa e no escritório. Precisa parar um run de captação em um PC, subir pro GitHub, e retomar exatamente de onde parou no outro PC.

## Workflow Completo

### 1. Parar a captação no PC de origem

```bash
# 1. Identificar o PID do captador
wmic process where "name='python.exe'" get processid,commandline | grep -i "mapear\|campanha\|avgestao"

# 2. Encerrar o processo (NÃO taskkill /F /IM chrome.exe)
wmic process where "processid=<PID>" delete

# 3. Verificar que parou
python executar_campanha_avgestao.py --status --run-id <RUN_ID>
# Confirmar: Captador ativo: NÃO, tarefas/leads preservados
```

### 2. Commit e push pro GitHub

```bash
cd C:\projetos\script-mapear-comércios
git add -A
git commit -m "feat: checkpoint <RUN_ID> - <N> tarefas, <M> leads"
git push origin <BRANCH>
```

### 3. No PC de destino

**Requisitos obrigatórios:**
- Python 3.12 (mesma versão)
- Playwright + Chromium instalado: `pip install playwright && playwright install chromium`
- **Mesmo caminho absoluto:** `C:\projetos\script-mapear-comércios\` (o checkpoint salva paths absolutos)
- Git instalado

```bash
# Clonar
git clone https://github.com/avellar2/script-mapeamento-comercios.git "C:\projetos\script-mapear-comércios"
cd C:\projetos\script-mapear-comércios
git checkout <BRANCH>

# Instalar dependências
pip install playwright
playwright install chromium

# Verificar estado do run
python executar_campanha_avgestao.py --status --run-id <RUN_ID>

# Retomar
python executar_campanha_avgestao.py --etapas mapear --resume --run-id <RUN_ID>
```

### 4. Se o caminho for diferente

Se o PC de destino não puder usar `C:\projetos\script-mapear-comércios\`, o checkpoint vai falhar porque os paths absolutos nos arquivos de run não batem.

**Solução:** editar `config.json` e `checkpoint.json` dentro de `output/avgestao/runs/<RUN_ID>/` para refletir o novo caminho. Ou melhor: criar um symlink:

```bash
# Se o projeto estiver em D:\projetos\script-mapear-comércios
mklink /D C:\projetos\script-mapear-comércios D:\projetos\script-mapear-comércios
```

## Pitfalls

- **Lock global:** O lock `captador_global.lock` é deletado na liberação. Se o PC de origem não liberou corretamente (crash, kill forçado), pode ficar um lock stale. Rodar `python scripts/diagnostico_lock.py` para verificar.
- **Chromium não instalado:** `playwright install chromium` é obrigatório. Sem ele, o script falha ao abrir navegador.
- **headless=False:** O run foi configurado com `headless=False` (navegador visível). Se o PC de destino não tiver monitor/display, pode falhar. Não mudar sem perguntar.
- **Processo residual:** Verificar se não há outro processo Python rodando o mapeador antes de retomar.
- **Git LFS / arquivos grandes:** O CSV de leads e os logs de captura podem ficar grandes. Verificar `.gitignore` — o diretório `output/` deve estar no `.gitignore` (dados de empresas, não devem ir pro GitHub público). O que sobe é o código, não os dados capturados.
