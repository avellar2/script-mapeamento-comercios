# Plano: envio SEMIAUTOMÁTICO de mensagens AVGESTÃO pelo WhatsApp Web

> **Status:** a fazer (especificação pronta, implementação pendente).
> **Escopo:** criar um módulo NOVO separado. Não tocar no captador geográfico, nos templates atuais, na classificação, no score nem nos scripts de landing pages.
> **Princípio:** NÃO é disparo automático em massa. O script automatiza a preparação e abertura da conversa, mas a confirmação final do envio fica com o usuário.

---

## Modelo recomendado para implementar

⚠️ **Modelo recomendado: DeepSeek V4 Pro**
Motivo: nova feature com múltiplos módulos (CLI, Playwright, normalização de telefone, checkpoint, resume, lock, testes com mocks) — raciocínio profundo e cuidado com edge cases.
Comando: `ollama launch claude --model deepseek-v4-pro:cloud`

Secundário (se o Pro estiver lento/travando): `ollama launch claude --model minimax-m2.7:cloud`

Reserva: `ollama launch claude --model glm-5.1:cloud`

---

## ARQUIVO PRINCIPAL

Criar: **`enviar_whatsapp_assistido.py`** (módulo novo, isolado, não importa nem altera o captador).

---

## MODOS

### 1. `--modo revisar`
- lê a planilha ou CSV;
- seleciona os leads elegíveis;
- gera as mensagens;
- mostra uma tabela de revisão;
- **não abre navegador**.

### 2. `--modo preparar`
- cria uma fila de contatos;
- salva checkpoint;
- **não abre navegador**;
- permite informar `--quantidade`.

### 3. `--modo assistido`
- abre o Chrome ou Chromium com **contexto persistente**;
- permite leitura manual do QR Code na primeira execução;
- reutiliza a sessão nas execuções seguintes;
- abre o link `wa.me` com telefone e mensagem preenchida;
- **não clica automaticamente no botão Enviar**;
- aguarda confirmação do usuário pelo terminal;
- após o usuário confirmar, registra o lead como enviado;
- abre o próximo contato.

---

## TEMPLATE FIXO (não alterar)

```
Boa tarde, pessoal da {NOME_EMPRESA}! Tudo bem?

Aqui é o Vanderson, criador do AVGESTÃO, um sistema feito para organizar assistências técnicas.

Com ele vocês registram o aparelho, abrem a ordem de serviço, enviam o orçamento para aprovação e o cliente acompanha o reparo pelo próprio link.

Eu mesmo configuro a conta e deixo tudo pronto para vocês testarem com um atendimento real durante 15 dias.

Posso liberar e configurar o acesso de vocês?
```

- **Não resumir, expandir ou reescrever a mensagem.**
- Usar o **nome curto aprovado** do estabelecimento quando existir.
- Caso não exista, gerar um nome curto removendo apenas informações claramente desnecessárias (bairro, telefone, excesso de palavras repetidas). **Não inventar nomes.**

---

## ENTRADAS

Aceitar:
- CSV;
- XLSX;
- arquivo geográfico gerado pelo captador;
- `--arquivo`;
- `--quantidade`;
- `--run-id`;
- `--resume`;
- `--somente-confirmados`;
- `--score-minimo` (padrão **70**);
- `--delay-min`;
- `--delay-max`;
- `--perfil-chrome`.

---

## ELEGIBILIDADE

Enviar para revisão somente leads que tenham:
- telefone válido;
- grupo **assistencias**;
- `faz_assistencia` igual a **CONFIRMADO**;
- score igual ou superior ao mínimo;
- **não** estejam marcados como já abordados;
- **não** estejam duplicados;
- **não** sejam classificados como loja apenas de acessórios;
- **não** estejam em revisão manual.

Quando algum campo estiver ausente, **não assumir silenciosamente**. Marcar como `REVISAO_MANUAL`.

---

## TELEFONES

Normalizar números brasileiros:
- remover espaços, parênteses, hífens e símbolos;
- adicionar código **55** quando ausente;
- validar DDD;
- aceitar celular e telefone fixo quando o WhatsApp estiver disponível;
- **não inventar dígitos**;
- **não alterar números internacionais**;
- gerar URL no formato:

```
https://wa.me/<telefone>?text=<mensagem_url_encoded>
```

Usar codificação URL correta em **UTF-8**, preservando acentos e quebras de linha.

---

## SESSÃO DO NAVEGADOR

Usar **Playwright com contexto persistente** e pasta própria, por exemplo:

```
output/avgestao/whatsapp_profile/
```

Regras:
- abrir **somente uma página**;
- **não** usar a sessão do Chrome pessoal diretamente;
- permitir leitura manual do QR Code;
- detectar quando o WhatsApp está desconectado;
- **não** tentar contornar verificações;
- **não** abrir dezenas de abas;
- fechar navegador corretamente ao finalizar;
- **não clicar automaticamente no botão Enviar**.

---

## FLUXO ASSISTIDO

Para cada lead:

1. mostrar nome, cidade, telefone, subnicho e mensagem no terminal;
2. permitir:
   - `A` → abrir;
   - `P` → pular;
   - `R` → revisão manual;
   - `S` → sair salvando o progresso;
3. ao escolher abrir, navegar para o `wa.me`;
4. aguardar a conversa carregar;
5. deixar a mensagem preenchida;
6. pedir ao usuário que **clique manualmente em Enviar**;
7. depois pedir confirmação no terminal:
   - `E` → enviado;
   - `N` → não enviado;
   - `I` → número inválido;
   - `B` → empresa pediu para não receber;
8. registrar o resultado;
9. aguardar o intervalo configurado;
10. seguir para o próximo.

---

## CHECKPOINT

Criar pasta:

```
output/avgestao/envios/<run_id>/
```

Salvar (escrita atômica — tmp + fsync + os.replace):
- `config.json`;
- `fila_envios.json`;
- `checkpoint.json`;
- `envios.csv`;
- `erros.jsonl`;
- `execucao.log`;
- `resumo.json`.

Status possíveis:
- `PENDENTE`
- `ABERTO`
- `ENVIADO`
- `PULADO`
- `REVISAO_MANUAL`
- `NUMERO_INVALIDO`
- `NAO_ENVIADO`
- `NAO_CONTATAR`
- `ERRO`
- `INTERROMPIDO`

---

## RESUME

Com `--resume --run-id`:
- **não repetir** `ENVIADO`;
- **não repetir** `NAO_CONTATAR`;
- **não repetir** `NUMERO_INVALIDO`;
- **continuar** `PENDENTE`, `ABERTO`, `NAO_ENVIADO` ou `INTERROMPIDO`;
- carregar a sessão persistente;
- salvar após cada lead.

---

## PROTEÇÕES

- **nunca** enviar automaticamente;
- **nunca** clicar no botão Enviar;
- **nunca** processar todos os leads sem limite explícito;
- **exigir** `--quantidade`;
- quantidade **máxima padrão por execução: 20**;
- não abrir dois contatos simultaneamente;
- impedir execução concorrente usando **lock file**;
- parar ao detectar logout, bloqueio ou comportamento inesperado;
- tratar **Ctrl+C** salvando o checkpoint;
- **não** registrar mensagem como enviada sem confirmação explícita do usuário;
- respeitar lista `NAO_CONTATAR` permanentemente.

---

## INTEGRAÇÃO COM O CAPTADOR

**Não modificar o captador.**

O script deve ler os campos existentes quando disponíveis:
- `nome`;
- `nome_curto`;
- `telefone`;
- `telefone_normalizado`;
- `cidade`;
- `uf`;
- `grupo`;
- `subnicho`;
- `faz_assistencia`;
- `score_avgestao`;
- `ja_abordado`;
- `run_id`;
- `source_query`.

Gerar um **novo arquivo atualizado, sem sobrescrever o original**.

---

## TESTES

Adicionar testes para:
- normalização de telefone;
- telefone com e sem 55;
- URL `wa.me`;
- codificação de acentos e quebras de linha;
- template exato;
- substituição do nome;
- filtro `CONFIRMADO`;
- score mínimo;
- exclusão de já abordados;
- exclusão de `NAO_CONTATAR`;
- fila;
- checkpoint;
- resume;
- escrita atômica;
- limite obrigatório;
- lock de execução;
- Ctrl+C;
- navegador **não** aberto no modo revisar;
- **nenhuma função de clique automático em Enviar**.

**Não abrir o WhatsApp Web nos testes.** Usar mocks para Playwright e navegador.

Sugestão de arquivo: `tests/test_enviar_whatsapp_assistido.py` (rodar via `py -3.12 tests/test_enviar_whatsapp_assistido.py` ou pytest, no mesmo padrimento dos outros testes do projeto — runner `_run_all`).

---

## ENTREGÁVEL FINAL

Ao terminar, informe:
- arquivos criados e alterados;
- total de testes (com resultado);
- comandos de uso;
- exemplo de fila (`fila_envios.json`);
- exemplo de checkpoint (`checkpoint.json`);
- **confirmação de que não existe clique automático no botão Enviar**.

---

## Contexto do projeto (para a sessão que for implementar)

- Projeto: `C:\projetos\script-mapear-comércios` (Python 3.12, Playwright, Supabase). **Não é o saas-gestão.**
- Python: `py -3.12`.
- Bash no Windows: usar **Git Bash** (POSIX); `cd /d` falha, usar `cd "C:/projetos/script-mapear-comércios"`.
- Prints com emojis (❌/✓/⏸) quebram em cp1252: nos testes, usar `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
- Padrão de testes: runner `_run_all()` no fim de cada `tests/test_*.py`, executáveis via `py -3.12 tests/test_X.py` OU pytest.
- Escrita atômica já existe em `config/runs.py` (`salvar_json_atomico`) — reusar o padrão (tmp + flush + fsync + os.replace).
- O captador gera XLSX geográfico com `COLUNAS_XLSX_AVGESTAO_GEO` (29 colunas, em `config/avgestao.py`) e CSV `leads_parciais.csv` (`config/runs.py:COLUNAS_CSV_GEO`). Os campos geográficos incluem `uf`, `estado`, `regiao`, `source_query`, `run_id`, `captured_at`, `place_id`, `maps_url`.
- `normalizar_texto` e helpers de normalização estão em `config/avgestao.py` — **não duplicar**, importar.
- **Não alterar** `config/avgestao.py` nas funções comerciais nem `COLUNAS_XLSX_AVGESTAO` (20 colunas).
- Convenções de dedup em `config/dedup.py` (`normalizar_telefone_br`, `normalizar_maps_url`).
- Regras de segurança do usuário: nunca enviar WhatsApp automaticamente, nunca clicar em Enviar automaticamente, exigir `--quantidade`, lock file, Ctrl+C salva checkpoint.

---

## Ordem segura sugerida de implementação

1. Helpers puros (sem Playwright): normalização de telefone, geração de URL wa.me, template fixo, substituição de nome, filtro de elegibilidade. + testes desses (sem rede/navegador).
2. Leitura de entrada (CSV/XLSX/geo) e escrita de arquivo atualizado (sem sobrescrever original). + testes.
3. Checkpoint/lock/resume/escrita atômica (reusar padrão de `config/runs.py`). + testes.
4. Modos `revisar` e `preparar` (sem navegador). + testes (incl. "navegador não aberto no modo revisar").
5. Modo `assistido` com Playwright persistente + mock para testes. + testes (incl. "nenhuma função de clique em Enviar", Ctrl+C, logout).
6. Validação final: rodar todos os testes novos + regressão dos 279 existentes; não abrir WhatsApp Web.