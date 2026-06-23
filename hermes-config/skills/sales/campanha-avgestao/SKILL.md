---
name: campanha-avgestao
description: Campanha de prospecção para vender o AVGESTÃO (sistema de gestão R$49/mês) para comércios locais da Baixada Fluminense. Envio automático via Playwright com perfil WhatsApp Business.
---

# Campanha AVGESTÃO

## Produto
- **AVGESTÃO** — sistema de gestão para pequenos negócios
- Funcionalidades: clientes, orçamentos, OS, financeiro, estoque, relatórios
- Diferencial: link pro cliente aprovar orçamento e acompanhar OS
- Preço: a partir de R$49/mês (NÃO mencionar na primeira mensagem)
- Oferta: 15 dias grátis
- Projeto: `C:\Users\Vanderson\Documents\saas-gestao` (Next.js + Prisma + PostgreSQL, VPS)

## Público-alvo
Negócios que usam OS e orçamentos:
- 🔧 Oficinas mecânicas, auto elétricas
- 🔩 Serralheria, marcenaria, vidraçaria
- ⚡ Prestadores de serviço (eletricista, pintor, encanador)
- 🦷 Dentistas, clínicas
- 💇 Salão de beleza, barbearia
- 🐾 Pet shop
- 🏋️ Academia, pilates
- 🚗 Auto escola
- 🏥 Clínica médica, veterinária, estética
- 📱 Loja de celulares (OS de reparo)
- 🚲 Loja de bicicleta (OS de manutenção)
- 🏪 Material de construção, loja de móveis (orçamentos)
- ❄️ Refrigeração e ar condicionado

## Dores por nicho
| Nicho | Dor |
|-------|-----|
| Oficina | serviços autorizados, peças usadas, valores e entrega do veículo |
| Assistência Técnica | aparelhos, diagnóstico, peças e andamento do serviço |
| Serralheria/Marcenaria | medidas, alterações, orçamento e retrabalho |
| Prestadores | quem aprovou, serviço pendente e pagamento em aberto |
| Refrigeração | chamados, equipamentos, histórico e garantia |
| Salão/Barbearia | agendamento, serviços, comissões |
| Pet shop | banho/tosa, agendamento, histórico |
| Academia/Pilates | matrículas, planos, renovação |

## Estrutura das mensagens (versão atual - junho 2026)
1. "Boa tarde, pessoal da [NOME]! Tudo bem?"
2. "Meu nome é Vanderson e desenvolvi o AVGESTÃO..."
3. Dor específica do nicho com consequência real
4. 2-3 funcionalidades contextualizadas (incluir portal do cliente)
5. "Estou liberando 15 dias gratuitos para teste."
6. CTA: "Posso criar um acesso para vocês entrarem e testarem?"

### Mensagens por nicho (APROVADAS - com acentuação OBRIGATÓRIA)

**Oficina mecânica:**
"Boa tarde, pessoal da {nome}! Tudo bem?\n\nMeu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços, veículos e orçamentos.\n\nUm dos maiores problemas de uma oficina é perder o controle de qual serviço foi autorizado, o que já foi feito e quanto o cliente ainda precisa pagar. Isso pode causar atraso, retrabalho e até discussão na hora da entrega.\n\nNo AVGESTÃO vocês conseguem abrir a ordem de serviço, registrar tudo que será feito, enviar o orçamento para aprovação do cliente e acompanhar cada etapa do veículo.\n\nEstou liberando 15 dias gratuitos para teste.\n\nPosso criar um acesso para vocês entrarem no sistema e testarem na própria oficina?"

**Serralheria/Marcenaria:**
"Boa tarde, pessoal da {nome}! Tudo bem?\n\nMeu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços personalizados e orçamentos.\n\nUm dos maiores riscos desse segmento é uma medida, alteração ou observação importante ficar perdida entre várias conversas no WhatsApp. Um detalhe esquecido pode gerar orçamento errado, retrabalho e prejuízo no material.\n\nNo AVGESTÃO vocês conseguem registrar o cliente, organizar as informações do serviço, montar o orçamento e enviar um link para o cliente aprovar antes da produção.\n\nO sistema está disponível para teste gratuito durante 15 dias.\n\nPosso criar um acesso para vocês entrarem e testarem no próprio negócio?"

**Prestador (eletricista, pintor, encanador):**
"Boa tarde, pessoal da {nome}! Tudo bem?\n\nMeu nome é Vanderson e desenvolvi o AVGESTÃO para empresas e profissionais que trabalham com atendimentos e serviços externos.\n\nUm dos maiores problemas nessa rotina é perder o controle de quem pediu orçamento, quem aprovou, qual serviço ainda está pendente e qual cliente ainda não pagou.\n\nNo AVGESTÃO vocês conseguem organizar os clientes, criar orçamentos, abrir ordens de serviço e acompanhar os valores recebidos e pendentes em um só lugar.\n\nEstou liberando 15 dias gratuitos para teste.\n\nPosso criar um login para vocês entrarem no sistema e testarem com os próprios serviços?"

## Cronograma de abordagem
```
Dia 1 → Abordagem inicial (envio automático)
Dia 3 → Follow-up 1 (mostrar valor)
Dia 7 → Follow-up 2 (último)
Depois → Marcar como "sem retorno" e encerrar
```

## Follow-up 1 (Dia 3)
- "Passando para saber se conseguiram ver minha mensagem..."
- Reforçar: reúne clientes, orçamentos, OS, andamento, valores, histórico
- Link pro cliente aprovar e acompanhar
- "Posso criar o login de teste para vocês?"

## Follow-up 2 (Dia 7 — último)
- "Esse será meu último contato para não incomodar."
- Reforçar benefícios
- "Quer que eu deixe um acesso preparado para vocês?"
- Após isso: marcar como "sem retorno"

## Envio Automático (Playwright)
- Script: `enviar_auto_avgestao.py`
- Perfil: `.whatsapp_business_profile/` (já logado)
- headless=False (usuário quer ver o navegador)
- 30 leads/dia, 7 min entre cada, bloco de 10 + 1h pausa
- Marca como "abordado" no Supabase automaticamente
- Marca como "perdido" se for fixo ou número inválido
- Lock de instância única (.enviar_auto.pid)
- Usa channel="chrome" (Chrome instalado, não Chromium bundled)

## Regras
- Não enviar mensagens idênticas em massa
- Não inventar informações do comércio
- Não pressionar
- Respeitar quem pedir pra parar
- Após 2 follow-ups sem resposta → encerrar
- Horário ideal: 9h-11h ou 14h-16h
- **Acentuação OBRIGATÓRIA** em todas as mensagens
- Não mencionar preço (R$49/mês) na primeira mensagem

## Fluxo de envio (automático)
1. Script busca leads do Supabase (status novo/pronto_para_enviar)
2. Filtra só celular (DDD 21 com 9 = celular, 21 sem 9 = fixo)
3. Abre Chrome com perfil WhatsApp Business
4. Navega pra URL de envio com mensagem personalizada
5. Clica em enviar
6. Marca como "abordado" no Supabase
7. Aguarda 7 min, repete
8. Bloco de 10, pausa de 1h entre blocos

## Scripts
- `enviar_auto_avgestao.py` — envio automático via Playwright
- `campanha_avgestao.py` — gera roteiro completo com mensagens e links
- `mostrar_msg.py` — mostra exemplos reais por nicho
- `gerar_campanha_avgestao.py` — gera HTML com links manuais
- `marcar_enviados.py` — marca leads como abordados no Supabase
- Base de leads: Supabase (origem=baixada, status=novo)

## Resultados
- 23/06/2026: 38 leads enviados (oficina 12, serralheria 10, eletricista 7, pintor 6, marcenaria 3)
- 1 lead respondeu com 👍🏼 (interessado em testar)
