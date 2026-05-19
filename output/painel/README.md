# Painel de Prospecção

Painel visual para controlar a prospecção diária de vendas de landing pages, mini sites e páginas profissionais.

## Como rodar

```bash
python gerar_painel_prospeccao.py
```

Para alterar o limite diário de leads:

```bash
python gerar_painel_prospeccao.py --limite 30
```

O limite padrão é 20 leads por dia. Para alterar permanentemente, edite `DAILY_LIMIT` no topo do script.

## Onde abrir

Abra no navegador:

```
output/painel/index.html
```

## O que o painel faz

1. Lê automaticamente a planilha mais atual (prioriza `campanha_diaria.xlsx`, depois `leads_prospeccao.xlsx`)
2. Filtra os melhores leads para vender landing page:
   - Prioridade Alta
   - Score >= 70
   - Sem site profissional
   - Com telefone ou WhatsApp
   - Nicho com boa chance de compra
3. Gera mensagens WhatsApp personalizadas por nicho
4. Salva o status de cada lead em `output/painel/status_leads.json`

## Funcionalidades do painel

- Cards de resumo (leads, enviadas, responderam, interessados, propostas, fechados, taxa)
- Filtros por nicho, status e atributos
- Busca por nome, nicho ou cidade
- Botão "Copiar mensagem" para cada lead
- Botão "Abrir WhatsApp" com mensagem preenchida
- Botões de status: mensagem enviada, respondeu, vídeo enviado, proposta, fechado, perdido, follow-up
- Campo de observações por lead
- Selo "Sem site" e "WhatsApp disponível"
- Score destacado em cores

## Rotina recomendada

1. Rode o script pela manhã
2. Abra o painel no navegador
3. Aborde no máximo 20 leads por dia
4. Não dispare mensagens em massa — envie uma por uma
5. Personalize a mensagem quando possível
6. Copie a mensagem, abra o WhatsApp e envie manualmente
7. Marque o status após cada contato
8. Faça follow-up depois de 2 dias
9. Volte ao painel para atualizar status

## Status disponíveis

| Status | Significado |
|---|---|
| novo | Lead ainda não abordado |
| abordar hoje | Prioridade para abordar hoje |
| mensagem enviada | Primeiro contato feito |
| respondeu | Lead respondeu |
| vídeo enviado | Prévia visual enviada |
| interessado | Lead demonstrou interesse |
| proposta enviada | Proposta comercial enviada |
| fechado | Venda concluída |
| perdido | Lead perdido |
| follow-up | Precisa de acompanhamento |
| não abordar | Não abordar |

## Arquivos

- `gerar_painel_prospeccao.py` — Script gerador
- `output/painel/index.html` — Painel HTML gerado
- `output/painel/status_leads.json` — Controle de status dos leads

## Observação

O painel NÃO envia mensagens automaticamente. Ele apenas gera o link WhatsApp e copia a mensagem. Você envia manualmente.