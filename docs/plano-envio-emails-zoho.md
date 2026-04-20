# Planejamento: Script de Envio Automático de Emails via Zoho

## Objetivo

Criar script Python que envia emails automaticamente para leads (`leads_sem_site.csv`) usando SMTP do Zoho Mail.

---

## Funcionalidades

### 1. Leitura dos Leads
- Ler `output/leads_sem_site.csv`
- Filtrar leads com telefone (prioridade)
- Filtrar leads com nota >= 4.0 (qualidade)
- Permitir retomar de onde parou (progresso/resume)

### 2. Configuração SMTP Zoho Mail
- **Host**: `smtppro.zoho.com`
- **Porta**: `465` (SSL)
- **Usuario**: `contato@vandersonavellar.com`
- **Senha**: App Password gerada no Zoho

### 3. Template de Email
- Assunto personalizado
- Corpo com HTML
- Variaveis: `{nome}`, `{categoria}`, `{cidade}`, `{telefone}`
- Assinatura profissional

### 4. Envio
- Delay aleatorio entre 2-5 minutos por email
- Limite diario (X emails/dia)
- Tratamento de erros (retry, fallback)

### 5. Tracking
- Log de emails enviados
- Log de erros
- CSV de resultado (quem recebeu, quando, status)

---

## Estrutura do Script

```python
envio_emails_zoho.py

# Config
SMTP_HOST = "smtppro.zoho.com"
SMTP_PORT = 465
SMTP_USER = "contato@vandersonavellar.com"
DELAY_MIN = 120  # 2 minutos
DELAY_MAX = 300  # 5 minutos
LIMITES_DIA = 50

# Funcoes
- load_progress() / save_progress()
- carregar_leads(filtro telefone, nota)
- montar_email_template(lead)
- enviar_email_smtp(lead, template)
- main() com loop e resume
```

---

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `envio_emails_zoho.py` | Script principal |
| `output/leads_sem_site.csv` | Leads pra enviar |
| `output/progresso_envio.json` | Progresso/resume |
| `output/envios_realizados.csv` | Log dos emails enviados |
| `templates/email_template.html` | Template HTML do email |

---

## Template de Email Exemplo

```
Assunto: Oportunidade de profissionalizar seu {categoria} em {cidade}

Olá {nome},

Vi que seu {categoria} em {cidade} está fazendo sucesso! 🎉

Tenho uma proposta que pode ajudar a profissionalizar ainda mais sua presença digital...

[continua email]

Atenciosamente,
Vanderson Avellar
contato@vandersonavellar.com
```

---

## Configuração App Password Zoho

1. Entrar em https://mail.zoho.com
2. Settings (engrenagem) → Email Configuration
3. POP/IMAP/SMTP Configuration
4. Gerar "App Password" ou "Senha de Aplicativo"
5. Usar essa senha no script (NÃO a senha da conta)

---

## Limites e Boas Práticas

- **Delay**: 2-5 minutos entre emails (evita bloqueio/spam)
- **Horario comercial**: 9h as 18h
- **Dia da semana**: Segunda a Sexta
- **Taxa de resposta**: Esperar 15-20%
- **Follow-up**: Segundo email 3 dias depois dos que não responderam

---

## Features Futuras

- [ ] A/B testing de assuntos
- [ ] Personalizacao por categoria
- [ ] Agendamento de envio
- [ ] Dashboard de resultado
- [ ] Integração com WhatsApp

---

## Status Planejamento

**Data**: 20/04/2026  
**Prioridade**: Alta  
**Estimativa**: 2-3 dias de desenvolvimento

---

## Proximos Passos

1. Gerar App Password no Zoho Mail
2. Criar arquivo `envio_emails_zoho.py`
3. Criar template HTML de email
4. Testar envio manual
5. Testar envio em massa (10 leads)
6. Monitorar taxa de resposta/spam
