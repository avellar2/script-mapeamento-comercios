# Identidade
- Este projeto e a maquina de prospeccao B2B do AVGestao/Gestor Local. Nao e o SaaS em si. Confidence: 0.95
- Objetivo: mapear comercios no Google Maps, qualificar leads, importar para Supabase, abordar por WhatsApp com protecao contra duplicidade, enviar e-mails com tracking e acompanhar por dashboards. Confidence: 0.95

# Pipeline
- Pipeline principal: MAPEAR Google Maps, QUALIFICAR score, IMPORTAR Supabase, ABORDAR WhatsApp, ENVIAR EMAIL, TRACKAR dashboard. Confidence: 0.95
- Cada estagio e um script Python independente com argparse. Confidence: 0.90

# Produtos vendidos
- Landing pages. Confidence: 0.95
- Mini sites. Confidence: 0.95
- Cardapios digitais. Confidence: 0.95
- SaaS AVGESTAO para comercios locais. Confidence: 0.95

# Regiao de atuacao
- Baixada Fluminense/RJ (11 cidades, tom informal). Confidence: 0.95
- Regiao Premium do Rio (25 bairros, tom consultivo). Confidence: 0.95

# Modulos principais
- `mapear_comercios.py`: scraping Google Maps com Playwright (11 cidades, 40+ categorias). Confidence: 0.95
- `prospectar_leads.py`: qualificacao de leads com score 0-100, prioridade, oferta por nicho e mensagem WhatsApp personalizada. Confidence: 0.95
- `import_leads_to_supabase.py`: importacao para Supabase com deduplicacao por telefone_normalizado. Confidence: 0.95
- `campanha_whatsapp.py`: orquestrador WhatsApp com modos plan, semi e auto; recover e recover-reserved. Confidence: 0.95
- `envio_emails_zoho.py`: envio de e-mails via Zoho Mail SMTP com templates por categoria. Confidence: 0.95
- `sender_int.py`: integracao de reservas atomicas com lead_outreach (reserve/settle). Confidence: 0.95
- `whatsapp_match/matcher.py`: verificacao de duplicidade no WhatsApp Web (~30s/lead). Confidence: 0.95

# Config centralizada
- `config/regioes.py`: cidades, bairros, categorias, nichos, pesos, ofertas. Confidence: 0.90
- `config/avgestao.py`: modo AVGESTAO (grupos, subnichos, score 0-100, mensagens). Confidence: 0.90
- `config/mensagens.py`: templates WhatsApp por regiao (informal Baixada vs consultivo Rio). Confidence: 0.90
- `config/franquia.py`: deteccao de 80+ marcas franqueadas. Confidence: 0.90
- `config/dedup.py`: deduplicacao em 5 niveis. Confidence: 0.90
- `config/lock_whatsapp_sender.py`: lock do sender WhatsApp (perfil .whatsapp_business_profile). Confidence: 0.90
- `config/lock_whatsapp_match.py`: lock do matcher WhatsApp (perfil profiles/whatsapp_match). Confidence: 0.90
- `config/whatsapp_selectors.py`: seletores CSS/XPath para WhatsApp Web. Confidence: 0.90

# Arquitetura
- Scripts CLI independentes (nao framework), cada estagio e autonomo. Confidence: 0.90
- Supabase (PostgreSQL) como fonte unica da verdade para leads e status. Confidence: 0.95
- Dois perfis Chrome isolados: .whatsapp_business_profile (sender) e profiles/whatsapp_match (matcher). Confidence: 0.95
- Lock files com msvcrt/fcntl para exclusao mutua de processos no Windows. Confidence: 0.90
- Resumibilidade: checkpoints em JSON para retomar scraping e envios interrompidos. Confidence: 0.90
- Degradacao graciosa: fallbacks em cascata (Supabase, arquivo local, vazio). Confidence: 0.85
