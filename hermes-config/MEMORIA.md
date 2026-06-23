# Memória Hermes — para restaurar no trabalho

Copiar skills de hermes-config/skills/ para ~/AppData/Local/hermes/skills/

## Memória (apontamentos)
1. Discord: bot1512676735886426262, server 1512676518856364122, @menção, minimax-m2.7 minúsculo. Skill: local-sales-prospecting
2. Supabase ~13.361 leads (11.404 Baixada + 1.957 Rio Premium). Skill: local-sales-prospecting
3. Preços LP: Baixada R$197/297/496, Rio Premium R$297/397/596. Skill: local-sales-prospecting
4. Skill: llm-model-selection — qual modelo usar pra cada tarefa
5. Skill: local-sales-prospecting — fluxo vendas LP + tráfego
6. Skill: campanha-avgestao — campanha de vendas do AVGESTÃO (R$49/mês, 15 dias grátis)
7. **Foco atual (Junho 2026): AVGESTÃO** — LP estava difícil de vender, pivotou pro sistema de gestão
8. AVGESTÃO: sistema de gestão em C:\Users\Vanderson\Documents\saas-gestao (Next.js + Prisma + PostgreSQL, VPS)
9. Envio automático: `enviar_auto_avgestao.py` — Playwright, perfil .whatsapp_business_profile, 7min entre msgs, bloco 10 + 1h pausa
10. 23/06: 38 leads enviados (oficina 12, serralheria 10, eletricista 7, pintor 6, marcenaria 3)
11. OpenCode + glm-5.2 usado pra reescrever o script de envio automático

## Perfil de usuário
- Vanderson, TI do trabalho, PC ligado 24h. Prefere respostas PT-BR curtas.
- Prospecção de comércios sem site no RJ. 2 frentes: Baixada e Rio Premium.
- Meta R$3.000+/mês (~20 vendas). Equipe AI-powered (Hermes, Claude Code, OpenCode).
- Discord acesso remoto. Instagram manual.
- Não trocar modelo automático — só avisar qual usar.

## Config
- model.default: minimax-m2.7
- model.provider: ollama-cloud
- headless=False (NUNCA mudar sem perguntar)
- Cliente só paga LP depois de pronta no ar
