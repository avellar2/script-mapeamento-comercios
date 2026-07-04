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
8. AVGESTÃO: sistema de gestão em C:\projetos\saas-gestão (Next.js + Prisma + PostgreSQL, VPS). Diferencial: link pro cliente aprovar orçamento e acompanhar OS.
9. Envio automático: `enviar_auto_avgestao.py` — Playwright, perfil .whatsapp_business_profile, 7min entre msgs, bloco 10 + 1h pausa
10. 23/06: 38 leads enviados (oficina 12, serralheria 10, eletricista 7, pintor 6, marcenaria 3)
11. OpenCode + glm-5.2 usado pra reescrever o script de envio automático
12. PRIMEIRO CLIENTE AVGESTÃO! Universo do Celular (Posse - Nova Iguaçu, conserto de celular) ativou conta em 27/06/2026 às 08:49. R$49/mês.
13. SEGUNDO CLIENTE potencial: Oficina automotiva C&B (tel 21 965004338) respondeu sim em 02/07 após envio em 24/06. Pedir email válido pra configurar conta e redefinir senha.

## Captação de Leads RJ (run ativo)
14. Run `run_20260629_014644_583c55`: 92 cidades, grupo assistencias, 5 subnichos. Ordem alfabética, teto 90/cidade.
15. Status: 420/552 tarefas concluídas, 127 pendentes, ~1.808 leads. Parado em São Fidélis.
16. Retomar: `python executar_campanha_avgestao.py --etapas mapear --resume --run-id run_20260629_014644_583c55`
17. Consultar: `python executar_campanha_avgestao.py --status --run-id run_20260629_014644_583c55`
18. Requisitos: Python 3.12, Playwright + Chromium, mesmo caminho C:\projetos\script-mapear-comércios\
19. Lock.py corrigido: os.write via fd no Windows com msvcrt.locking(). 346 testes.
20. NUNCA executar resume/captação/Chromium/alterar arquivos/locks/matar sem autorização.

## WhatsApp Matcher (branch feat/protecao-duplicidade-whatsapp)
21. Matcher otimizado: TIMEOUT_CURTO 5s→1s, encontrar_seletor_rapido com count(), espera composta asyncio.gather
22. variantes_busca_telefone: 8 variantes → 1 (DDD+numero, sem 55). Celular: 11 dígitos. Fixo: 10 dígitos.
23. Controle positivo TECM: MATCHED em 13.71s. Dry-run 10 leads: ~10s/lead (antes ~66s).
24. Commit 19555c2. Branch: feat/protecao-duplicidade-whatsapp.

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