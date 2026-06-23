---
name: campanha-avgestao
description: Campanha de prospecção para vender o AVGESTÃO (sistema de gestão) para comércios locais da Baixada Fluminense. Abordagem manual com 3 contatos (Dia 1, 3 e 7).
---

# Campanha AVGESTÃO

## Produto
- **AVGESTÃO** — sistema de gestão para pequenos negócios
- Funcionalidades: clientes, orçamentos, OS, financeiro, estoque, relatórios
- Diferencial: link pro cliente aprovar orçamento e acompanhar OS
- Preço: a partir de R$49/mês
- Oferta: 15 dias grátis
- Projeto: `C:\projetos\saas-gestão` (Next.js + Prisma + PostgreSQL, rodando em VPS)

## Público-alvo
Negócios que usam OS e orçamentos:
- 🔧 Oficinas mecânicas, auto elétricas
- 📱 Assistência técnica (celular, informática)
- 🪚 Serralheria, marcenaria, vidraçaria
- ⚡ Prestadores de serviço (eletricista, pintor, encanador)
- ❄️ Refrigeração e ar condicionado

## Dores por nicho
| Nicho | Dor |
|-------|-----|
| Oficina | serviços autorizados, peças usadas, valores e entrega do veículo |
| Assistência Técnica | aparelhos, diagnóstico, peças e andamento do serviço |
| Serralheria/Marcenaria | medidas, alterações, orçamento e retrabalho |
| Prestadores | quem aprovou, serviço pendente e pagamento em aberto |
| Refrigeração | chamados, equipamentos, histórico e garantia |

## Cronograma de abordagem
```
Dia 1 → Abordagem inicial
Dia 3 → Follow-up 1 (mostrar valor)
Dia 7 → Follow-up 2 (último)
Depois → Marcar como "sem retorno" e encerrar
```

## Estrutura das mensagens
1. "Boa tarde, pessoal da [NOME]! Tudo bem?"
2. "Meu nome é Vanderson e desenvolvi o AVGESTÃO..."
3. Dor específica do nicho com consequência real
4. 2-3 funcionalidades contextualizadas
5. "Estou liberando 15 dias gratuitos para teste."
6. CTA: "Posso criar um acesso para vocês entrarem e testarem?"

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

## Regras
- Não enviar mensagens idênticas em massa
- Não inventar informações do comércio
- Não pressionar
- Respeitar quem pedir pra parar
- Após 2 follow-ups sem resposta → encerrar
- Horário ideal: 9h-11h ou 14h-16h

## Fluxo de envio (manual)
1. Abrir WhatsApp Business (perfil salvo em `.whatsapp_business_profile/`)
2. Clicar no link wa.me com mensagem personalizada
3. Mostrar pro Vanderson → ele aprova → enviar
4. Marcar como "abordado" no Supabase
5. Agendar follow-up conforme cronograma

## Scripts
- `campanha_avgestao.py` — gera roteiro completo com mensagens e links
- `mostrar_msg.py` — mostra exemplos reais por nicho
- Base de leads: Supabase (origem=baixada, status=novo)
