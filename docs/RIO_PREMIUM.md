# Rio Premium — Regiao de Prospecção

## O que é

**rio_premium** é a região de prospecção que foca em bairros de alto poder aquisitivo do Rio de Janeiro. O objetivo é mapear negócios premium com maior chance de entender e pagar por landing pages de qualidade superior.

A região opera **completamente separada** da Baixada Fluminense. Leads, campanhas, saídas e mensagens não se misturam.

---

## Bairros

| # | Bairro |
|---|--------|
| 1 | Barra da Tijuca |
| 2 | Recreio dos Bandeirantes |
| 3 | Copacabana |
| 4 | Ipanema |
| 5 | Leblon |
| 6 | Botafogo |
| 7 | Flamengo |
| 8 | Tijuca |
| 9 | Jardim Botânico |
| 10 | Lagoa |
| 11 | Gávea |
| 12 | Laranjeiras |
| 13 | Humaitá |
| 14 | São Conrado |
| 15 | Urca |
| 16 | Méier |
| 17 | Vila Isabel |
| 18 | Grajaú |
| 19 | Jardim Guanabara |
| 20 | Freguesia |
| 21 | Pechincha |
| 22 | Vila Valqueire |
| 23 | Recreio |
| 24 | Taquara |
| 25 | Centro |

---

## Nichos Prioritários

| Tipo | Nichos |
|------|--------|
| **Saúde/Estética** | clínica de estética, harmonização facial, dentista, psicólogo, nutricionista, fisioterapeuta, clínica médica, consultório |
| **Beleza Premium** | salão premium, barbearia premium, studio de sobrancelha, studio de cílios, lash designer, spa, depilação a laser, micropigmentação |
| **Fitness** | pilates, academia boutique, personal trainer |
| **Profissional Liberal** | advogado, arquiteto, fotógrafo, designer de interiores |
| **Hospitalidade** | restaurante, hotel boutique, pousada |
| **Educação** | escola, curso livre |

---

## Como Usar

### Mapear comércios

```bash
# Mapear bairros premium
python mapear_comercios.py --regiao rio_premium

# Mapear baixada (comportamento padrão)
python mapear_comercios.py --regiao baixada
```

### Prospectar leads

```bash
# Qualificar leads rio_premium
python prospectar_leads.py --regiao rio_premium

# Qualificar leads baixada
python prospectar_leads.py --regiao baixada
```

### Importar para Supabase

```bash
# Importar leads rio_premium
python import_leads_to_supabase.py --regiao rio_premium

# Importar leads baixada
python import_leads_to_supabase.py --regiao baixada
```

### Gerar campanha diária

```bash
# Campanha rio_premium
python campanha_diaria.py --regiao rio_premium --top 30

# Campanha baixada
python campanha_diaria.py --regiao baixada --top 30

# Preparar campanha do Supabase
python preparar_campanha.py --regiao rio_premium
```

### Relatório regional

```bash
python gerar_relatorio_regional.py
python gerar_relatorio_regional.py --regiao rio_premium
```

---

## Score Premium

O score para rio_premium tem bônus adicionais:

| Critério | Baixada | Rio Premium |
|----------|---------|-------------|
| Sem site | +30 | +30 |
| Telefone/WhatsApp | +20 | +20 |
| Avaliação >= 4.0 | +15 | +15 |
| 20+ avaliações | +15 | +15 |
| Instagram | +10 | +10 |
| Nicho bom para landing | +10 | +10 |
| **Bônus região** | +0 | **+10** |
| **Bônus high-ticket** | — | **+10** |
| Franquia (alta) | -30 | -30 |
| Franquia (média) | -15 | -15 |
| Site profissional | -25 | -25 |
| **Máximo** | 100 | 100 |

**Prioridade:**
- Alta: score >= 75
- Média: 50 a 74
- Baixa: abaixo de 50

**Nichos high-ticket** (bônus +10): estética, harmonização facial, dentista, psicólogo, nutricionista, fisioterapeuta, pilates, academia boutique, advogado, arquiteto, spa, salão premium, barbearia premium, fotógrafo, curso livre.

---

## Mensagens WhatsApp

### Baixada (informal)
> "Oi, tudo bem? Vi sua barbearia no Google e notei que não tem uma página de agendamento. Quando o cliente quer marcar horário e não consegue, acaba indo pro próximo que aparece. Posso te mostrar como ficaria uma página?"

### Rio Premium (consultivo)
> "Boa tarde. Encontrei sua clínica de estética no Google e percebi que não há uma página com informações de agendamento. Considerando o padrão do seu negócio, uma página profissional poderia facilitar bastante o acesso dos clientes. Posso enviar uma proposta visual de como ficaria?"

**Diferenças:**
- Saudação: "Oi" → "Boa tarde"
- Verbo: "Vi" → "Encontrei"
- Tom: casual → profissional
- CTA: "Quer ver?" → "Posso enviar uma proposta visual?"
- Sem preço, sem link, sem spam

---

## Detecção de Franquia

O sistema detecta possíveis franquias com 3 níveis de confiança:

| Confiança | Critério | Penalidade |
|-----------|----------|------------|
| **Alta** | Nome na lista de ~80 marcas conhecidas | -30 score |
| **Média** | Padrão de endereço (Unidade, Filial, Shopping) | -15 score |
| **Baixa** | Indício leve, sem confirmação | 0 (sem penalidade) |

**Marcas detectadas:** McDonald's, Burger King, Subway, Starbucks, Smart Fit, Espaçolaser, O Boticário, Cacau Show, Drogasil, Petz, Cobasi, Renner, CVC, Ibis, Novotel, etc.

**Shoppings detectados:** Barra Shopping, NorteShopping, VillageMall, RioSul, Rio Design, etc.

**Limitações:**
- Detecção por nome/endereço é heurística, não 100% precisa
- Franquias locais pequenas podem não ser detectadas
- Falsos positivos são possíveis em nomes genéricos
- Confiança "baixa" não aplica penalidade para evitar falso positivo

---

## Supabase — Campo `origem`

A região do lead é identificada pelo campo `origem` na tabela `leads`:

| Valor | Região |
|-------|--------|
| `"baixada"` | Baixada Fluminense |
| `"rio_premium"` | Bairros premium do RJ |
| `""` (vazio) | Tratar como baixada (legado) |

---

## Estrutura de Saídas

```
output/
  baixada/
    playwright/        CSV/XLSX do mapear
    apify/             Resultados Apify
    prospeccao/        Excel qualificado
    campanhas/         Excel de campanha
  rio_premium/
    playwright/
    apify/
    prospeccao/
    campanhas/
  painel/             Compartilhado — CRM unificado
```

---

## CRM — Filtros

O painel CRM agora tem 3 filtros novos:

1. **Região**: Todas / Baixada / Rio Premium
2. **Franquia**: Todos / Possível franquia / Não franquia
3. **Tipo cliente**: Todos / pequeno_negocio / profissional_liberal / clinica_local / etc.

Badge de região no card do lead:
- Azul "Premium" = rio_premium
- Cinza "Baixada" = baixada

---

## Config Centralizado

Todas as configurações de região estão em `config/regioes.py`:

- Cidades/bairros por região
- Categorias de busca
- Nichos prioritários
- Pesos de score
- Tipos de oferta
- Mensagens (tom informal vs consultivo)
- Detecção de franquia (`config/franquia.py`)
- Geração de mensagens (`config/mensagens.py`)

Para adicionar uma nova região, basta criar um novo `RegiaoConfig` em `config/regioes.py`.