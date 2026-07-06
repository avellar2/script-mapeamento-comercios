# WhatsApp real
- Nunca enviar WhatsApp real sem confirmacao explicita do usuario. Confidence: 0.99
- Nunca usar modo auto com envio real sem --confirm-live-send e autorizacao clara. Confidence: 0.99
- Antes de campanha real, validar dry-run, limite de leads, checkpoint, reserva e duplicidade. Confidence: 0.95

# E-mail real
- Nunca enviar e-mail real pelo Zoho sem confirmacao explicita. Confidence: 0.99
- Sempre separar geracao/preview de envio real. Confidence: 0.95
- Nao vazar credenciais SMTP. Confidence: 0.99

# Scraping real
- Nunca executar scraping real em massa sem confirmacao. Confidence: 0.95
- Scraping deve ser controlado, resumivel e respeitar checkpoints. Confidence: 0.90
- Nao aumentar volume, cidades ou categorias sem explicar impacto. Confidence: 0.90

# Dados de leads
- Nunca alterar dados reais de leads sem explicar impacto. Confidence: 0.95
- Nunca usar dados reais de leads em testes automatizados. Confidence: 0.95
- Sempre mascarar telefone, lead_id, reservation_id e dados pessoais em relatorios. Confidence: 0.95

# Reservas e protecao contra duplicidade
- Nunca liberar, criar, deletar ou alterar reservas sem confirmacao quando houver risco. Confidence: 0.95
- Nunca remover protecao contra duplicidade. Confidence: 0.99
- Nunca contornar lead_outreach, reservation_token, reserve_outreach, settle_outreach, confirm_outreach_from_whatsapp, locks ou checkpoints. Confidence: 0.99
- Nunca finalizar reserva sem posse/token valido. Confidence: 0.99
- Nunca liberar reserva de outra campanha. Confidence: 0.95
- Sempre preservar atomicidade. Confidence: 0.95

# Tabelas sensiveis
- Tabelas sensiveis: leads, lead_outreach, lead_interactions, emails_enviados, campaigns. Confidence: 0.95
- Qualquer alteracao nessas tabelas deve ser tratada como sensivel. Confidence: 0.95

# RPCs criticas
- RPCs criticas: reserve_outreach, settle_outreach, confirm_outreach_from_whatsapp. Confidence: 0.95
- Nunca alterar uso dessas RPCs sem explicar impacto, riscos e testes. Confidence: 0.95
- Nao inventar RPC inexistente. Confidence: 0.95
- Se uma RPC nao existir, investigar schema e codigo antes de propor solucao. Confidence: 0.90

# Logs e dados
- Logs nao devem vazar telefone completo, e-mail completo, token, cookie ou dados sensiveis. Confidence: 0.95
- Para tarefas em Supabase, sempre informar se houve dry-run ou escrita real. Confidence: 0.95
- Para tarefas de WhatsApp, sempre informar se houve envio real ou zero envio. Confidence: 0.95
- Para tarefas de e-mail, sempre informar se houve envio real ou zero envio. Confidence: 0.95
