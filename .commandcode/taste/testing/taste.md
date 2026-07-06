# Execucao de testes
- Rodar testes especificos do modulo alterado antes de commit. Confidence: 0.95
- Rodar testes de campanha, reservas, locks, WhatsApp matcher e dedup quando mexer nesses fluxos. Confidence: 0.95
- Comando padrao para testes especificos: python -m pytest tests/test_campanha_whatsapp.py -q. Confidence: 0.90
- Comando padrao para todos os testes: python -m pytest -q. Confidence: 0.90
- Zero falhas novas e obrigatoria. Confidence: 0.95

# Arquivos de teste principais
- `tests/test_campanha_whatsapp.py`: orquestrador de campanha WhatsApp (modos, locks, limites, recover). Confidence: 0.90
- `tests/test_browser_lifecycle.py`: ciclo de vida do Playwright, SessaoWhatsApp, locks. Confidence: 0.85
- `tests/test_whatsapp_match_selectors.py`: seletores do WhatsApp Web. Confidence: 0.85
- `tests/test_avgestao.py`: score AVGESTAO, classificacao faz_assistencia, dedup, mensagens. Confidence: 0.85
- `tests/test_phone_utils.py`: normalizacao de telefone BR. Confidence: 0.85
- `tests/test_outreach_safety.py`: controles de seguranca de envio. Confidence: 0.85
- `tests/test_reserva_atomicidade.py`: atomicidade de reservas. Confidence: 0.85
- `tests/test_dedup.py`: deduplicacao. Confidence: 0.85
- `tests/test_lock.py`: lock files. Confidence: 0.85

# Regras de teste
- Nao declarar sucesso sem evidencia. Confidence: 0.95
- Informar comandos executados e resultado. Confidence: 0.95
- Se teste falhar, corrigir ou explicar claramente. Confidence: 0.95
- Nao mascarar falha de teste. Confidence: 0.95
- Testes de integracao com Supabase podem precisar de service_role_key configurada. Confidence: 0.85
- Mocks devem ser usados para evitar WhatsApp real, envio real e escrita real em testes. Confidence: 0.90

# Fixtures
- `tests/fixtures/cidades.txt`: dados de teste para cidades. Confidence: 0.80
- `tests/outreach_safety.py`: helper de seguranca para testes de outreach. Confidence: 0.80
- `tests/outreach_pg_adapter.py`: adaptador PostgreSQL para testes. Confidence: 0.80
