# Dashboard de Emails Enviados

Sistema completo de tracking de emails com Supabase + Dashboard HTML.

## O que foi criado

1. **Banco de dados Supabase** (`emails_enviados`)
   - Registra todos os emails enviados
   - Tracking de abertura
   - Views de estatísticas

2. **Edge Function `track`**
   - Serve tracking pixel (1x1 PNG)
   - Registra abertura no banco
   - URL: `https://ivqaccppqcchqshaplao.supabase.co/functions/v1/track?id=TRACKING_ID`

3. **Script de envio modificado** (`envio_emails_zoho.py`)
   - Salva cada email enviado no Supabase
   - Gera tracking ID único
   - Adiciona tracking pixel no HTML

4. **Dashboard HTML** (`frontend/dashboard-emails.html`)
   - KPIs: total enviados, abertos, taxa, categorias
   - Gráficos por categoria
   - Filtros: busca, categoria, cidade, status, tipo
   - Tabela paginada
   - Conexão direta com Supabase

## Como usar

### 1. Enviar emails
```bash
python envio_emails_zoho.py
```

O script:
- Carrega leads do CSV
- Envia via Zoho SMTP
- Salva no Supabase
- Adiciona tracking pixel

### 2. Ver dashboard

**Opção A - Local:**
```bash
cd frontend
python -m http.server 8080
```
Abre: `http://localhost:8080/dashboard-emails.html`

**Opção B - Vercel (deploy):**
1. Arrasta `dashboard-emails.html` pro Vercel
2. Ou usa CLI: `vercel deploy`

### 3. Acompanhar em tempo real

- Dashboard atualiza sozinho (busca direto do Supabase)
- Quando alguém abre email, o tracking pixel registra
- Taxa de abertura atualiza automaticamente

## Estrutura do banco

### Tabela `emails_enviados`

| Campo | Tipo | Descrição |
|---|---|---|
| id | bigint | PK auto-increment |
| nome | text | Nome do negócio |
| email | text | Email enviado |
| categoria | text | Categoria |
| cidade | text | Cidade |
| telefone | text | Telefone |
| tipo_email | text | 'cnpj' ou 'comercial' |
| template | text | Template usado |
| data_envio | timestamptz | Quando enviou |
| email_aberto | boolean | Se foi aberto |
| data_abertura | timestamptz | Primeira abertura |
| qtd_aberturas | integer | Quantas vezes |
| tracking_id | text | ID único (UUID) |

### Views

**`vw_stats_gerais`** - Estatísticas gerais
**`vw_por_categoria`** - Emails por categoria
**`vw_reenvio_sugerido`** - Quem reenviar (não abertos em 7+ dias)

## Tracking pixel

O tracking pixel é adicionado automaticamente no final de cada email:

```html
<img src="https://ivqaccppqcchqshaplao.supabase.co/functions/v1/track?id={TRACKING_ID}" width="1" height="1" style="display:none" alt="">
```

Quando o cliente abre o email e carrega a imagem:
1. Edge Function recebe request
2. Atualiza `email_aberto = true`
3. Registra `data_abertura`
4. Incrementa `qtd_aberturas`
5. Retorna 1x1 PNG transparente

## Supabase credentials

- **URL:** `https://ivqaccppqcchqshaplao.supabase.co`
- **Anon Key:** Está no dashboard HTML
- **Service Role Key:** Usado pela Edge Function (não expor!)

## Próximos passos

1. ** Hospedar dashboard no Vercel**
2. ** Testar envio de email**
3. ** Verificar tracking pixel funcionando**
4. ** Monitorar taxa de abertura**

## Troubleshooting

**Dashboard não carrega dados:**
- Verifica se RLS está configurado corretamente
- Verifica se Anon Key está correta
- Abre o console do navegador

**Tracking não funciona:**
- Verifica se Edge Function está ativa
- Verifica se tracking_id está sendo substituído
- Testa a URL do tracking pixel direto no navegador

**Script não salva no Supabase:**
- Verifica se `pip install supabase` foi executado
- Verifica credenciais URL e KEY
- Abre o console do Supabase para ver erros
