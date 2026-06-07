# Progress Tracking — progresso.json do mapear_comercios.py

Arquivo: `C:/projetos/script-mapear-comercios/output/{regiao}/playwright/progresso.json`

**ATENÇÃO: arquivo grande (5-8 MB, ~90.000 linhas). `python -c` e `execute_code` dão TIMEOUT nele.**

## Método certo: read_file + search_files

### Estrutura (linhas reais)
| Linha | Conteúdo |
|-------|----------|
| 1-2 | `{"categorias_prontas": [` |
| 2-~280 | Lista de `"Bairro::categoria"` (uma por linha) |
| ~280-312 | `categorias_em_andamento` (dict de tarefas atuais) |
| ~319-324 | O dict de em_andamento com índice/total |
| ~325+ | Array `comercios` com todos os leads |
| Últimas ~20 | Último comércio coletado |

### Passo a passo para reportar progresso

**1. Categorias prontas:**
```
search_files output_mode=count, path=progresso.json, pattern="categorias_prontas": \+
```
O número de vírgulas + 1 = total de categorias concluídas.

**2. Rodando agora (em_andamento):**
```
read_file limit=10 offset=318
```
Mostra o dict com `"Bairro::categoria": {"indice": N, "total": M}`

**3. Total comercios coletados:**
```
search_files output_mode=count, path=progresso.json, pattern="\"nome\":"
```
~5600 no Rio Premium.

**4. Sem site:**
```
search_files output_mode=count, path=progresso.json, pattern="\"tem_site\": false"
```
~2063 no Rio Premium.

### Exemplo de leitura (Rio Premium — 07/06/2026)
- **Categorias prontas**: 295/700 (42%)
- **Em andamento**: `Laranjeiras::pilates` (20/60)
- **Comércios**: 5.600
- **Sem site**: 2.063