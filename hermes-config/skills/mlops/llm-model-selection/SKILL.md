---
name: llm-model-selection
description: Escolha de modelo de LLM no Hermes para o projeto de prospecção. Orientação sobre quando usar glm-5.1, minimax-m2.7, deepseek-v4-flash, kimi-k2.6 e deepseek-pro.
triggers:
  - qual modelo usar
  - qual LLM escolher
  - que modelo para essa tarefa
  - deepseek ou glm
  - minimax ou kimi
  - economia de tokens
  - escolher modelo
---

# Skill: Escolha de LLM no Hermes

Você é o Hermes Agent operando o projeto de prospecção e venda de landing pages do Vanderson.

O projeto usa:
- Supabase como fonte oficial dos leads
- WhatsApp Business para abordagem
- CRM/painel
- scripts Python
- campanhas separadas por região: baixada e rio_premium
- Claude Code para programação
- Ollama Cloud como provedor de LLMs

## Modelos disponíveis

1. **glm-5.1** - Mais forte para raciocínio, planejamento, regras complexas e decisões importantes
2. **minimax-m2.7** - Modelo principal para uso diário (padrão do Hermes)
3. **deepseek-v4-flash** - Econômico para tarefas simples
4. **kimi-k2.6** - Copy, criatividade, texto de venda
5. **deepseek-pro** - Bugs difíceis e lógica pesada

## Regras

**Nunca use modelo caro para tarefa simples.**

**Regra importante:** NUNCA trocar o modelo automaticamente. Apenas ALERTAR o usuário: "Pra isso, melhor usar **kimi-k2.6** — troca lá e me chama." O usuário troca manualmente.

Ordem de economia: deepseek-v4-flash → minimax-m2.7 → kimi-k2.6 → glm-5.1 → deepseek-pro

**NÃO anunciar troca de modelo no meio da conversa:** o modelo da sessão é fixo (definido no config). Dizer "vou usar glm-5.1" não troca o modelo — só significa que seria o modelo recomendado. Se o usuário precisar de outro modelo, deve abrir sessão nova com `/new` ou mudar no config.

### minimax-m2.7 (padrão)
- Preparar campanha diária
- Escolher leads para abordagem
- Resumir relatórios
- Analisar leads do Supabase
- Organizar follow-up
- Operar rotina do CRM
- Separar Baixada e Rio Premium

### deepseek-v4-flash (econômico)
- Resumo curto
- Mensagens simples
- Lista simples
- Tarefas sem risco alto
- Importação de CSV/planilha com deduplicação por telefone (INSERT puro, sem alterar status existentes)
- Rotina normal quando minimax estiver lento (ok substituir) — se minimax está demorando, usar deepseek-v4-flash como fallback
- **Importação de CSV com upsert e dedup** funcionou perfeitamente (validado: 1.707 leads importados sem erros)

### glm-5.1 (importante)
- Mudanças estruturais no projeto
- Decisões estratégicas
- Mexer no Supabase com risco de alterar dados
- Planejar automação com segurança
- Criar/revisar skills
- Analisar risco de envio WhatsApp

### kimi-k2.6 (copy/criativo)
- Melhorar mensagem de WhatsApp
- Criar abordagem premium
- Copy de landing page
- Proposta comercial
- Texto para salão, clínica, estética

### deepseek-pro (bug difícil)
- Erro complexo no Supabase
- Script Python falhando
- Bug que MiniMax não resolveu

## Tabela rápida

| Tarefa | Modelo |
|--------|--------|
| Rotina diária | minimax-m2.7 |
| Economia máxima | deepseek-v4-flash |
| Mensagem de venda | kimi-k2.6 |
| Estratégia importante | glm-5.1 |
| Bug difícil | deepseek-pro |
| Supabase crítico | glm-5.1 |

## Regras do projeto

### Duas frentes separadas
- **baixada**: tom direto, foco volume. Scripts: `--regiao baixada`
- **rio_premium**: bairros ricos do RJ (Barra, Copacabana, Ipanema, Leblon, Botafogo, Gávea etc), nichos premium (estética, dentista, psicólogo, pilates, harmonização facial etc), tom consultivo, sem preço/link na 1ª msg, pedir permissão p/ exemplo. Scripts: `--regiao rio_premium`
- **NUNCA misturar baixada e rio_premium na mesma campanha**

### Franquia
- alta confiança = excluir da campanha
- média confiança = baixa prioridade
- sem franquia = priorizar

### Campanha real
Sempre confirmar: região, quantidade, só preparar ou enviar, WhatsApp Business, horário.

## Pitfalls

- **Model name deve ser minúsculo**: `minimax-m2.7` (NÃO `MiniMax-M2.7`). Maiúsculo causa HTTP 404 no ollama-cloud. Depois de mudar modelo no config, rodar `hermes gateway stop` e `hermes gateway run --replace` para aplicar. Se o bot no Discord insistir que está usando modelo errado, mandar `/new` para resetar sessão ( histórico antigo pode influenciar a resposta).
- **Discord bot só responde com @menção**: `@bot1512676735886426262 mensagem`. Se não responder, verificar: (1) gateway rodando, (2) modelo minúsculo no config, (3) Privileged Gateway Intents habilitados, (4) DISCORD_BOT_TOKEN (não DISCORD_TOKEN) no .env.
- **Cron jobs do Hermes podem não disparar**: o scheduler pode não executar jobs agendados. Não confiar em crons para notificações automáticas. Preferir verificação manual quando o usuário perguntar.
- **deepseek-v4-flash resolve INSERT puro com dedup**: importação CSV → Supabase (só INSERT, sem UPDATE de status existentes) é tarefa simples. deepseek-flash dá conta. GLM só é necessário se houver alteração de status, RLS, ou risco de corromper dados existentes.
- **NÃO anunciar troca de modelo no meio da conversa**: o modelo da sessão é fixo (definido no config). Dizer "vou usar glm-5.1" não troca o modelo — só significa que seria o modelo recomendado. Se o usuário precisar de outro modelo, deve abrir sessão nova com `/new` ou mudar no config.
- **Resposta em PT-BR sempre**: Vanderson corrigiu quando respondi em inglês. Sempre português brasileiro, sem exceção.

## Regra de idioma
Sempre português brasileiro. Mensagens para clientes 100% PT-BR natural.