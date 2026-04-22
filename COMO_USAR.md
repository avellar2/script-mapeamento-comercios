# Sistema de Emails - Guia Completo

## Status: ✅ TUDO PRONTO

### Deploy
- Dashboard: https://frontend-j67aarixx-vandersonavellar1997-1683s-projects.vercel.app
- Supabase: conectado
- Edge Function: ativa
- Tracking pixel: funcionando

## Como usar

### 1. Enviar emails
```bash
python envio_emails_zoho.py
```

**O que acontece:**
- Carrega leads do CSV
- Envia via Zoho SMTP (senha do .env)
- Salva no Supabase
- Adiciona tracking pixel

### 2. Ver dashboard
Abre: https://frontend-j67aarixx-vandersonavellar1997-1683s-projects.vercel.app

**Mostra:**
- Total de emails enviados
- Taxa de abertura
- Por categoria
- Filtros (cidade, categoria, status)
- Tabela completa

### 3. Como o tracking funciona

Quando alguém abre o email:
1. Tracking pixel carrega (1x1 PNG invisível)
2. Edge Function registra abertura
3. Dashboard atualiza automaticamente

**Taxa de abertura esperada:** 60-80%
- Gmail web: ✓
- Gmail app: ✗ (bloqueia imagens)
- Outlook: ✓
- Apple Mail: ✓

## Arquivos principais

| Arquivo | O que faz |
|---|---|
| `envio_emails_zoho.py` | Envia emails + salva no Supabase |
| `frontend/dashboard-emails.html` | Dashboard (Vercel) |
| `.env` | Senhas (NÃO commitar) |
| `templates/*.html` | 9 templates + tracking pixel |
| `testar_sistema.py` | Testa se tudo está OK |

## Testar sistema

```bash
python testar_sistema.py
```

Verifica:
- Variáveis de ambiente (.env)
- Conexão Supabase
- Templates com tracking

## URLs importantes

- **Dashboard:** https://frontend-j67aarixx-vandersonavellar1997-1683s-projects.vercel.app
- **Supabase:** https://supabase.com/dashboard/project/ivqaccppqcchqshaplao
- **Tracking:** https://ivqaccppqcchqshaplao.supabase.co/functions/v1/track?id=XXX

## Troubleshooting

**Dashboard não carrega:**
- F5 (atualiza página)
- Verifica console (F12)
- Verifica se Supabase URL está correta

**Tracking não registra:**
- Normal: Gmail app bloqueia
- Testa abrindo email no navegador
- 60-80% é taxa esperada

**Script não envia:**
- Verifica se `.env` existe
- Verifica App Password Zoho
- Verifica horário (9h-18h seg-sex)

## Próximos passos

1. Testa enviando 1 email
2. Abre o email (clica em "Ver imagens")
3. Verifica se aparece no dashboard

Boas vendas! 🚀
