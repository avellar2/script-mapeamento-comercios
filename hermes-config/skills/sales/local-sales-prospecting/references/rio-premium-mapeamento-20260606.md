# Mapeamento Rio Premium — 2026-06-06 (em andamento)

## Status (07/06/2026 — 09:00)
- **Tarefas**: 296/700 completas (~42%)
- **Em andamento**: `Laranjeiras::pilates` (20/60)
- **Comércios coletados**: 5.600
- **Sem site (leads bons)**: 2.063 (~37%)
- **Rodando há**: vários dias no PC do trabalho

## Bairros por status de conclusão
| Bairro | Status |
|--------|--------|
| Flamengo | ~93% |
| Copacabana | ~86% |
| Lagoa | ~79% |
| Ipanema | ~75% |
| Botafogo | ~75% |
| Jardim Botânico | ~75% |
| Leblon | ~71% |
| Recreio | ~68% |
| Barra da Tijuca | ~57% |
| Tijuca | ~57% |
| Gávea | iniciando |
| Laranjeiras | rodando agora |

## Observação importante sobre taxa sem site
No Rio Premium, ~1/3 dos comércios não tem site (vs Baixada onde a taxa é maior). Isso é esperado — bairros nobres têm mais estrutura digital. Mas os 562 leads sem site são de ALTA QUALIDADE: clínicas de estética, dentistas, personal trainers que PRECISAM de presença digital e têm maior poder aquisitivo para pagar R$247-297.

## Config da região
- `max_results_per_category`: 20 (aumentado de 10 para 20 em 06/06)
- `headless=False` (**NÃO mudar para True sem perguntar**)
- Bairros: 25 | Categorias: 28 | Total buscas: 700
- Output: `output/rio_premium/playwright/progresso.json`

## Processo de importação
- Script `importar_csv_playwright.py` importou 3.132 leads da Baixada para o Supabase
- Supabase total: ~6.487 leads (3.355 original + 3.132 importados)
- 802 leads sem contato descartados
- 491 duplicados ignorados
- Coluna `fonte` NÃO existe na tabela leads — usar `origem='baixada'`

## Preços definidos
- Baixada: R$149 (tom direto, volume)
- Rio Premium: R$247-297 (tom consultivo, premium)

## Cron jobs
- Cron de progresso não disparou (tentado 2x com `every 15m` e `*/15 * * * *`). Não confiar em crons para tracking — usar verificação manual quando o usuário perguntar "progresso?"

## Lições aprendidas
1. Quando o processo de mapeamento morre (browser fecha), verificar SE REALMENTE morreu antes de reiniciar. Notificações `[IMPORTANT: Background process completed]` podem ser de processos antigos.
2. Se abrir 2+ Chrome sem matar o anterior, os dois escrevem no mesmo progresso.json e corrompem dados. Matá-los todos e reiniciar limpo (deletar progresso.json se necessário).
3. headless=True remove a janela do Chrome — o usuário QUER ver o browser mapeando. Não mudar sem perguntar.
4. Ao matar PIDs Python, verificar qual é o Hermes (bash com 'hermes' no cmdline) e matar APENAS os scripts do usuário.
5. `mapear_comercios.py` alterado para headless=False (visível) — o default era headless=False, foi mudado para True por engano e revertido.
6. **NUNCA reiniciar mapeamento baseado só na notificação de processo completado** — sempre verificar com `process(action='poll')` + `ps aux` antes. O Hermes notifica processos ANTIGOS que já foram substituídos.
