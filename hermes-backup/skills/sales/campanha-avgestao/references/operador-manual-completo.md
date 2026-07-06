# Manual do Operador do Captador AVGESTÃO

Regras permanentes para operação do captador de leads. Leia antes de qualquer execução.

## 1. Projeto correto

Diretório: `C:\projetos\script-mapear-comércios`

Não confundir com:
- SaaS AVGESTÃO em Next.js (`saas-gestão`)
- Scripts antigos de envio
- Captadores de landing pages

## 2. Situação atual

Versão 1 do captador geográfico concluída:
- 297 testes passando
- Migration Supabase aplicada (NÃO reaplicar)
- 9 colunas geográficas presentes
- 3 índices presentes
- Branch: `feat/captador-geografico-avgestao-v1`
- Tag: `captador-avgestao-v1`

## 3. Arquivos principais

- `mapear_comercios.py` — captador (pesquisa Google Maps, fila, dedup, checkpoint, resume, dry-run)
- `executar_campanha_avgestao.py` — orquestrador (encadeia mapear → prospectar → campanha). NUNCA envia WhatsApp
- `config/territorios.py` — municípios, UFs, regiões
- `config/fila.py` — fila de pesquisas
- `config/dedup.py` — deduplicação global
- `config/limites.py` — limites por leads únicos
- `config/runs.py` — run_id, checkpoint, arquivos
- `config/avgestao.py` — regras comerciais
- `import_leads_to_supabase.py` — importação

## 4. Regra principal

Sou OPERADOR, não desenvolvedor. Durante captação:
- Não modificar código
- Não criar funcionalidades
- Não ajustar testes
- Não reescrever templates
- Não alterar score/classificação/subnichos/banco
- Não aplicar migration
- Não fazer commit/push

Se encontrar BUG: parar e apresentar (comando + erro + run_id + checkpoint + hipótese + sugestão). Não corrigir sem autorização.

## 5. Foco comercial

Grupo: `assistencias`
6 subnichos: celular, computadores, impressoras, eletrodomésticos, eletrônicos, videogames

## 6. Dry-run

Valida cidades, tarefas, grupos, subnichos, limites, fila sem abrir navegador.

Exemplo:
```bash
python executar_campanha_avgestao.py --grupo assistencias --escopo uf --uf RJ --max-total 300 --dry-run
```

Resultado esperado: 92 cidades, 552 tarefas, navegador não aberto, pasta do run criada.

## 7. Primeiro teste real

```bash
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidades --cidades "Duque de Caxias, RJ" "Nova Iguaçu, RJ" --max-por-consulta 3 --max-total 10 --delay-min 4 --delay-max 8
```

Verificar: navegador abre, pesquisas corretas, 6 subnichos, leads com telefone, cidade+UF, place_id+maps_url, dedup, limite 10, navegador fecha.

Após o teste: entregar relatório e AGUARDAR autorização para próximo passo.

## 8. Escalonamento obrigatório

1. Teste real 10 leads → validar CSV/checkpoint/resume
2. Lote 30 leads → validar
3. Lote 50 leads → validar
4. Lote 100 leads → validar
5. Só depois ampliar para RJ

Cada etapa depende da validação da anterior E autorização do Vanderson. NÃO pular etapas.

## 9. Run ID

Formato: `run_YYYYMMDD_HHMMSS_abc123`
Arquivos em: `output\avgestao\runs\<RUN_ID>\`
Guardar sempre o run_id.

Arquivos do run: config.json, fila.json, checkpoint.json, leads_parciais.csv, leads_parciais.xlsx, resumo.json, execucao.log, erros.jsonl, XLSX geográfico final.

Nunca apagar durante execução. Nunca enviar ao GitHub (contêm dados de empresas).

## 10. Status da fila

- `pendente`: não executada
- `em_andamento`: execução atual
- `concluida`: pesquisa finalizada
- `erro`: falhou após tentativas
- `interrompida`: execução parou antes de concluir
- `ignorada_limite`: não executada porque limite foi atingido (NÃO é erro)

## 11. Limites

Contam apenas leads ÚNICOS após dedup.

Argumentos: `--max-por-consulta`, `--max-por-cidade`, `--max-por-subnicho`, `--max-total`, `--limite-cidades`.

`--max-total 10` = captar no máximo 10 leads únicos, não executar apenas 10 tarefas.

## 12. CAPTCHA

NÃO tentar resolver, contornar, atualizar página, trocar IP ou usar evasão.

Procedimento correto:
1. Salvar screenshot
2. Salvar checkpoint
3. Registrar erro
4. Fechar navegador
5. Informar run_id
6. Aguardar antes de retomar

## 13. Supabase

Migration já aplicada. Campos: uf, estado, regiao, source_query, source_scope, run_id, captured_at, place_id, maps_url.
Índices: idx_leads_uf, idx_leads_run_id, idx_leads_place_id.

Não executar migration novamente. Não apagar leads. Não atualizar dados antigos em massa. Não expor .env.

## 14. Deduplicação

Compara: place_id, maps_url, telefone, nome+endereço, nome+cidade (último fallback).
Sem fuzzy match. Telefone igual em cidades diferentes não elimina filial automaticamente.
Comparar com leads do run E com leads já no Supabase.

## 15. Checkpoint e resume

Se execução parar (Ctrl+C, terminal fechado, erro, CAPTCHA, queda do navegador):
```bash
python executar_campanha_avgestao.py --etapas mapear --resume --run-id <RUN_ID>
```

Usar MESMO run_id. Resume preserva concluídas, não repete leads, não altera limites.

## 16. Prospecção e campanha

Após captura concluída:
```bash
python executar_campanha_avgestao.py --etapas prospectar,campanha --run-id <RUN_ID> --top 10
```

Processa leads, aplica score, seleciona melhores, gera campanha. NÃO envia WhatsApp.

## 17. Leads elegíveis

Para campanha de assistências:
- grupo `assistencias`
- `faz_assistencia = CONFIRMADO`
- score ≥ 70
- telefone válido
- empresa ativa
- não ser apenas loja de acessórios
- não ter sido abordada anteriormente
- não duplicada
- não em revisão manual

## 18. Mensagem comercial aprovada

NÃO resumir, reescrever, expandir ou mudar o encerramento:

```
Boa tarde, pessoal da {NOME_EMPRESA}! Tudo bem?

Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.

Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.

Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.

Posso liberar e configurar o acesso de vocês?
```

Apenas substituir `{NOME_EMPRESA}`. Não inventar nome. Não incluir preço. Não oferecer vídeo/demonstração. Não alterar 15 dias.

## 19. WhatsApp

O captador e o orquestrador NÃO enviam WhatsApp. Durante captação: não abrir WhatsApp Web, não abrir wa.me, não clicar em Enviar, não executar scripts de envio, não marcar lead como abordado sem confirmação.

## 20. Regra crítica: 1 Chrome por vez

NUNCA ter 2 Chrome abertos simultaneamente na captura. O script abre 1 navegador que reusa para todas as tarefas. Se outro Chrome do Playwright estiver aberto (de execução anterior), os dois podem sobrescrever o perfil um do outro, causando erros e perda de progresso.

Sempre verificar se há processo Chrome rodando antes de iniciar captura. Se houver 2, matar todos antes de começar.

## 21. Relatório obrigatório

Após cada operação, apresentar:

**Execução:** comando, run_id, horário início/término, status final.

**Fila:** cidades, subnichos, tarefas totais, concluídas, pendentes, interrompidas, erros, ignoradas por limite.

**Leads:** brutos, únicos, duplicatas removidas, com telefone, sem telefone, por cidade, por subnicho, já existentes no Supabase.

**Arquivos:** caminho da pasta do run, CSV, XLSX, checkpoint, resumo, erros.

**Problemas:** CAPTCHA, falhas, tarefas que precisam revisão, dados incompletos.

Não afirmar que algo funcionou sem evidência no terminal ou nos arquivos.

## 22. Comandos úteis

```bash
# Uma cidade
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidade --cidade "Duque de Caxias, RJ" --max-total 20

# Várias cidades
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo cidades --cidades "Duque de Caxias, RJ" "Nova Iguaçu, RJ" --max-total 30

# Estado do Rio
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo uf --uf RJ --max-por-consulta 3 --max-por-cidade 5 --ordem-cidades alfabetica --delay-min 6 --delay-max 12 --max-tentativas 3

# Vários estados
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo ufs --ufs RJ MG SP --max-total 300

# Região Sudeste
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo regiao --regiao sudeste --max-total 300

# Brasil (NUNCA sem limites)
python executar_campanha_avgestao.py --etapas mapear --grupo assistencias --escopo brasil --limite-cidades 100 --max-total 500
```
