# Controle de Leads no Supabase

Este documento explica como usar o Supabase como fonte da verdade para o controle de leads de prospecção.

## Visão Geral

O Supabase armazena:
- **Leads** — todos os comércios prospectados, com status e dados de contato
- **Interações** — histórico de todas as ações (abordagem, follow-up, resposta)
- **Campanhas** — registro de cada importação de planilha

O fluxo de dados é:

```
Planilha (.xlsx) → import_leads_to_supabase.py → Supabase (leads + interactions + campaigns)
```

Antes de abordar alguém, consulte o Supabase para saber se aquele número já foi abordado.

---

## Setup

### 1. Criar tabelas no Supabase

Acesse o [SQL Editor do Supabase](https://supabase.com/dashboard/project/ivqaccppqcchqshaplao/sql) e execute o conteúdo do arquivo `supabase/schema.sql`.

Isso criará as tabelas `leads`, `lead_interactions` e `campaigns`, com indexes, triggers e RLS policies.

### 2. Variáveis de ambiente

O arquivo `.env` já deve conter:

```
SUPABASE_URL=https://ivqaccppqcchqshaplao.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Instalar dependências

```bash
pip install supabase python-dotenv openpyxl
```

---

## Importar Leads

### Da planilha mais recente

```bash
python import_leads_to_supabase.py
```

O script procura automaticamente a planilha em:
1. `output/campanhas/campanha_diaria.xlsx`
2. `output/prospeccao/leads_prospeccao.xlsx`
3. Qualquer `.xlsx` nos diretórios acima

### De um arquivo específico

```bash
python import_leads_to_supabase.py --arquivo caminho/do/arquivo.xlsx
```

### O que acontece na importação

- Telefones são normalizados para o formato `5521999999999`
- `telefone_normalizado` é a **chave de deduplicação** (não nome+cidade)
- Novos leads são inseridos com status `novo`
- Leads existentes são atualizados (score, prioridade, oferta, etc.)
- **Status protegidos** (abordado, respondeu, follow_up, interessado, convertido, perdido) **NUNCA são resetados**
- `ultimo_contato_em` e `proximo_followup_em` **NUNCA são sobrescritos** em leads existentes
- Uma interação tipo `importacao` é criada para cada novo lead

### Saída do script

```
📊 RESUMO DA IMPORTAÇÃO
============================================================
  📄 Leads lidos da planilha:  150
  ✅ Leads válidos com tel:     142
  🆕 Novos inseridos:          45
  🔄 Atualizados:              90
  🔒 Preservados (status ok):  7
  ⚠️  Ignorados (sem tel):     8
  ❌ Erros:                    0
============================================================
```

---

## Importar Histórico do WhatsApp

Se você já abordou leads manualmente pelo WhatsApp, pode importar esse histórico:

```bash
python importar_historico_whatsapp.py
```

Ou especificar o caminho do CSV:

```bash
python importar_historico_whatsapp.py --arquivo meu_historico.csv
```

### Formato do CSV

O arquivo `historico_whatsapp.csv` deve ter as colunas:

```csv
telefone,status,observacao
21999999999,abordado,Mandei mensagem em maio
21333333333,abordado,
552188888888,abordado,Cliente respondeu mas desistiu
```

Colunas:
- **telefone** — telefone em qualquer formato (será normalizado)
- **status** — status atual (opcional, usado apenas para referência)
- **observacao** — observações livres (opcional)

### O que acontece

- Para cada telefone, busca o lead no Supabase
- Se encontra: atualiza status para `abordado` (exceto se já convertido/perdido), preenche datas se vazias
- Se não encontra: cria um lead mínimo com status `abordado` e origem `historico_whatsapp`
- Cria interação tipo `primeira_abordagem_manual_antiga`

---

## Marcar Lead como Enviado

Após enviar uma mensagem de WhatsApp para um lead:

```bash
python marcar_lead_enviado.py --telefone 21999999999
python marcar_lead_enviado.py --telefone 21999999999 --mensagem "Oi, vi seu salão no Google..."
```

### O que acontece

- Busca o lead pelo telefone normalizado
- Atualiza status para `abordado`
- Preenche `ultimo_contato_em` com a data/hora atual
- Define `proximo_followup_em` para daqui 7 dias
- Cria interação tipo `primeira_abordagem`, canal `whatsapp`
- Se o lead já está convertido ou perdido, não faz nada (protege contra regressão)

---

## Lógica de Deduplicação

A chave de deduplicação é **`telefone_normalizado`**, não `nome+cidade`.

Motivos:
- O mesmo negócio pode aparecer com nomes ligeiramente diferentes entre runs
- O telefone é o identificador real de contato via WhatsApp
- Um negócio com dois números será dois leads distintos (esperado)

Forma do telefone normalizado: `5521999999999` (código do país + DDD + número).

---

## Fluxo de Status

```
novo → pronto_para_enviar → abordado → respondeu → follow_up → interessado → convertido
  ↓        ↓                  ↓            ↓            ↓            ↓
  └──────────────────────────┴────────────┴────────────┴────────────┴──→ perdido
```

Qualquer status pode ir para `perdido`. Os status `convertido` e `perdido` são terminais — não são regredidos automaticamente.

---

## Interações (Audit Trail)

Cada ação cria um registro em `lead_interactions`:

| Tipo | Quando |
|------|--------|
| `importacao` | Lead importado pela primeira vez |
| `primeira_abordagem` | Mensagem enviada via `marcar_lead_enviado.py` |
| `primeira_abordagem_manual_antiga` | Histórico importado do WhatsApp |
| `follow_up` | Follow-up realizado |
| `resposta_cliente` | Cliente respondeu |
| `proposta_enviada` | Proposta comercial enviada |
| `convertido` | Venda fechada |
| `perdido` | Lead perdido |

---

## Consultas Úteis

### Ver todos os leads para abordar hoje

```sql
SELECT nome, telefone, categoria, cidade, score, oferta_sugerida
FROM vw_leads_para_abordar
ORDER BY score DESC;
```

### Ver follow-ups pendentes

```sql
SELECT nome, telefone, whatsapp, proximo_followup_em, status
FROM vw_followups_hoje
ORDER BY proximo_followup_em ASC;
```

### Ver resumo por status

```sql
SELECT * FROM vw_leads_resumo_status;
```

### Ver histórico de um lead

```sql
SELECT li.tipo, li.canal, li.mensagem, li.observacao, li.created_at
FROM lead_interactions li
WHERE li.lead_id = 'UUID-DO-LEAD'
ORDER BY li.created_at DESC;
```