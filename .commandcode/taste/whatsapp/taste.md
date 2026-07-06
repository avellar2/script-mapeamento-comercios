# Modos de operacao
- `campanha_whatsapp.py` possui modos plan, semi, auto, recover e recover-reserved. Confidence: 0.95
- `plan` deve ser usado para consulta/dry-run. Nao abre browser, nao envia. Confidence: 0.95
- `semi` pode abrir wa.me, mas precisa de confirmacao humana antes de enviar. Confidence: 0.95
- `auto` e sensivel e so pode enviar com confirmacao explicita via --confirm-live-send. Confidence: 0.99
- --confirm-live-send e uma trava critica e nao deve ser banalizada. Confidence: 0.99

# Verificacao de duplicidade
- `whatsapp_match/matcher.py` e parte da protecao contra duplicidade. Confidence: 0.95
- O matcher pesquisa telefone no WhatsApp Web, abre conversa, confirma numero e detecta mensagens de saida existentes. Confidence: 0.90
- 12 status possiveis de match: MATCHED, AMBIGUOUS, NO_CHAT, GROUP, etc. Confidence: 0.85
- Tempo medio de verificacao: ~30s por lead. Confidence: 0.85

# Perfis e locks
- Dois perfis Chrome isolados: .whatsapp_business_profile (sender) e profiles/whatsapp_match (matcher). Confidence: 0.95
- Locks de perfis Chrome devem ser preservados. Confidence: 0.95
- Lock files usam msvcrt.locking() no Windows com stale recovery por PID. Confidence: 0.90

# Fluxo de campanha
- Fluxo: reserva atomica, verificacao de duplicidade, envio. Confidence: 0.95
- Reserva usa RPC reserve_outreach com TTL de 30 minutos. Confidence: 0.90
- Verificacao usa perfil matcher separado do sender. Confidence: 0.90
- Envio abre wa.me/{tel}?text={msg} com perfil sender. Confidence: 0.90

# Seletores
- Seletores do WhatsApp Web definidos em config/whatsapp_selectors.py. Confidence: 0.90
- Seletores incluem campo de busca, chat, header, mensagens, QR code. Confidence: 0.85
- Fallbacks para campo de busca: PT, EN, role alternativos. Confidence: 0.85

# Recuperacao
- Modo recover: recupera de checkpoint local de run anterior. Confidence: 0.90
- Modo recover-reserved: recupera reservas pendentes direto do Supabase, sem depender de checkpoint. Confidence: 0.90
- recover-reserved usa settle_outreach com reservation_token da propria tabela. Confidence: 0.90
