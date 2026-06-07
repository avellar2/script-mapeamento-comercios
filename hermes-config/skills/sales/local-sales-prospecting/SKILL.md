---
name: local-sales-prospecting
version: 2.0.0
description: Gerenciar ciclo completo de prospecção de comércios locais para venda de landing pages — papel de gerente comercial/SDR com Supabase como fonte oficial, extração de histórico WhatsApp, importação, campanha diária e follow-up.
tags: [sales, prospecting, whatsapp, landing-pages, local-business, sdr, crm]
triggers:
  - prospecção de comércios locais
  - geração de leads para vendas
  - lista diária de contatos
  - campanha de WhatsApp para negócios locais
  - pipeline de vendas para pequenos comércios
  - filtrar e priorizar leads
  - landing pages para comércios
  - atualizar histórico do WhatsApp
  - preparar campanha de hoje
  - marcar lead como enviado
  - importar leads para o Supabase
  - regras de comunicação em português
---

# Prospecção de Vendas Locais — Gerente Comercial/SDR

Atuar como gerente comercial/SDR do projeto de venda de landing pages na Baixada Fluminense. Supabase é a fonte oficial de dados. Nunca enviar WhatsApp automaticamente. Nunca alterar status sem confirmação.

## Acesso Remoto (Gateway)

Quando o usuário estiver no trabalho e quiser acessar o Hermes remotamente.

**Opção principal: Gateway (Telegram ou Discord)**
1. Configurar o Hermes Gateway no PC que fica ligado (casa ou trabalho)
2. Do outro local, conversar via Telegram/Discord Web ou app
3. O Hermes tem acesso a todos os scripts, WhatsApp Business e dados do PC onde está rodando

**Vantagens do gateway:**
- Conversa de qualquer lugar (celular, web, app)
- Não instala nada no PC de destino (só abre web.app)
- WhatsApp Business fica no PC que está rodando o Hermes

**Alternativas:**
- Instalar Hermes em ambos os PCs: skills + scripts vão por GitHub, mas WhatsApp Business precisa ser configurado separadamente em cada um
- AnyDesk/TeamViewer: funciona mas controla o PC inteiro (mais pesado)
- Preparar tudo antes + envio automático: não precisa de interação em tempo real

**Setup do gateway:** ver `references/gateway-setup.md`

## Fontes de Dados e Arquivos

- **Projeto**: `C:\projetos\script-mapear-comércios`
- **Python**: `/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe`
- **Fonte oficial**: **Supabase** — é o banco autoritativo. Todos os leads históricos vivem lá.
- **CSV local** (`output/playwright/todos_comercios.csv`, `leads_sem_site.csv`): **REGERADO a cada execução** do `mapear_comercios.py`. Não é acumulativo — sobrescreve. Não confiar como backup.
- **JSON de progresso** (`output/playwright/progresso.json`): estado bruto do Playwright, não confiável para contagem final.
- **Dashboard local**: `file:///C:/projetos/script-mapear-comércios/output/painel/index.html`
- **Banco local SQLite**: `output/painel/prospeccao.db` (legacy, está sendo substituído pelo Supabase)
- **Excel legado**: `campanha_diaria.xlsx` (~915 leads)

## Modelo de Negócio Atual (Junho 2026)

- **Venda única** de landing page por **R$149** (Baixada) / **R$247-297** (Rio Premium)
- **NÃO** é assinatura/mensalidade — o usuário quer modelo simples: vender, criar com Claude Code, colocar no ar
- **Meta**: R$3.000/mês mínimo = ~20 vendas Baixada ou ~12 Rio Premium
- Sem mensalidade, sem recorrência por enquanto. O foco é validar o modelo primeiro.

## Regras Críticas de Operação (NUNCA violar — tudo aprendido com erro)

### Chrome e Processos

1. **NUNCA mudar Playwright para headless=True sem perguntar o usuário.** O usuário quer VER o Chrome mapeando. Headless faz ele pensar que não está funcionando. Isso causou frustração direta.

2. **NUNCA abrir mais de 1 processo mapear_comercios.py por vez.** Se o browser do Playwright cair mas o Chrome ficar aberto (órfão), rodar de novo abre SEGUNDO Chromium — ambos escrevem no mesmo progresso.json e corrompem dados.

3. **Antes de reiniciar um mapeamento, VERIFICAR se o processo realmente morreu:**
   - `process(action='poll')` — checar `status` e `uptime_seconds`
   - `ps aux | grep mapear_comercios` — ver PIDs reais no sistema
   - `cat /proc/<pid>/cmdline | tr '\0' ' '` — confirmar qual script é qual
   O Hermes notifica `[IMPORTANT: Background process completed]` mesmo para processos ANTIGOS que já foram substituídos. Não confiar só nessa notificação.

4. **NUNCA matar todos os Python de uma vez.** Hermes também roda como Python/bash. Antes de matar PIDs: identificar qual é o Hermes (bash com `hermes` no cmdline) e matar APENAS `mapear_comercios.py`. Comando seguro:
   ```bash
   ps aux | grep python | grep -v grep  # listar PIDs
   cat /proc/<pid>/cmdline | tr '\0' ' '  # identificar cada um
   kill -9 <PID_do_mapeador>  # matar SÓ o mapeador
   ```

5. **Solução quando 2 Chromes estão abertos corrompendo progresso:**
   - Matar o processo `mapear_comercios.py` atual
   - Deletar `output/{regiao}/playwright/progresso.json`
   - Reiniciar do zero — o script retoma sem duplicatas

### Acompanhamento de Progresso

- **Cron jobs do Hermes podem não disparar** — não confiar em crons. Usuário pergunta manualmente "como tá o progresso?" e você verifica na hora com Python.
- **Formatar progresso assim para o usuário:**
  - Tarefas (ex: 54/700) — SEMPRE explicar que são bairros × categorias
  - Coletados totais
  - Sem site (leads úteis)
  - Bairro/categoria rodando agora
  - Por bairro: total + sem site

## Regras Obrigatórias (NUNCA violar)

1. **NUNCA enviar WhatsApp automaticamente** — apenas gerar links `wa.me` e mensagens para envio manual
2. **NUNCA apagar dados** — sempre preservar, nunca remover
3. **NUNCA alterar status sem confirmação** — sempre perguntar antes de mudar status no Supabase
4. **NUNCA importar CSV sem aprovação** — sempre mostrar resumo antes de qualquer importação
5. **Sempre mostrar resumo antes de ação importante** — confirmar com o usuário
6. **Idioma**: mensagens em português, tom humano, curto e consultivo — SEM linguagem de spam
7. **Limite diário**: máximo 15 leads por dia para abordagem manual
8. **Respostas ao usuário**: sempre em PT-BR. SEM palavras em inglês, espanhol ou chinês, exceto termos técnicos inevitáveis (Supabase, WhatsApp, CRM, Playwright, Python, JSON, HTML, SQL)
9. **Navegador do Hermes é separado** do Chrome do usuário — não é possível acessar sessões/logins

## Preço e Modelo de Negócio

| Região | Preço LP | Motivo |
|--------|----------|--------|
| **Baixada** | **R$149** | Acessível, volume, tom direto |
| **Rio Premium** | **R$247-297** | Comércio premium aguenta mais; barato gera desconfiança |

**Meta mínima**: R$3.000/mês = ~20 vendas/mês (1 venda/dia e meio na Baixada) ou ~12 vendas/mês (Rio Premium)

**O que R$149 inclui**: Landing page feita com Claude Code, colocada no ar (hospedagem), 1 revisão, link direto pro WhatsApp deles.

**O R$149 não inclui** (opcional depois): manutenção mensal, alterações frequentes, SEO avançado.

**Faturamento projetado com duas frentes:**
| Frente | Preço | Meta/mês | Faturamento |
|--------|-------|----------|-------------|
| Baixada | R$149 | 10 vendas | R$1.490 |
| Rio Premium | R$247 | 15 vendas | R$3.705 |
| **Total** | - | **25** | **R$5.195** |

## Duas Frentes do Projeto

### baixada
- Tom direto e informal, foco volume
- Preço: R$149
- Scripts: `--regiao baixada`
- Nichos: salão, barbearia, restaurante, pizzaria, oficina, padaria, bar, supermercado etc.
- Mensagem mais simples e objetiva

### rio_premium
- Tom consultivo e profissional
- Preço: R$247-297
- Scripts: `--regiao rio_premium`
- Bairros: Barra da Tijuca, Recreio, Copacabana, Ipanema, Leblon, Botafogo, Flamengo, Tijuca, Jardim Botânico, Lagoa, Gávea, Laranjeiras, Humaitá, São Conrado, Urca, Méier, Vila Isabel, Grajaú, Freguesia, Pechincha, Centro
- Nichos: clínicas de estética, salões premium, barbearias premium, dentistas, psicólogos, nutricionistas, fisioterapeutas, pilates, academias boutique, studios de sobrancelha/cílios, spa, advogados, arquitetos, fotógrafos, harmonização facial, depilação a laser, micropigmentação, personal trainer, consultórios
- **NUNCA**: preço na 1ª mensagem, link na 1ª mensagem, tom de promoção
### Exemplo de mensagem de abertura — Rio Premium (COM dor):
> "Oi, tudo bem? Vi seu studio de cílios no Google e achei o trabalho lindo. Só que reparei que quando alguém pesquisa por 'studio de cílios na Barra', você não aparece com uma página profissional — acaba perdendo cliente que nem sabe que você existe. Trabalho criando páginas pra negócios como o seu, com fotos, localização e botão direto pro WhatsApp. Posso te mostrar um exemplo?"

### Regras
- **NUNCA misturar baixada e rio_premium na mesma campanha**
- Franquia: alta confiança = excluir, média = baixa prioridade, sem franquia = priorizar
- Scripts aceitam `--regiao` (baixada ou rio_premium)
- Antes de qualquer campanha, sempre confirmar: região, quantidade, só preparar ou enviar, WhatsApp Business, horário

## Funil de Status (Supabase)

```
novo → pronto_para_enviar → abordado → respondeu → follow_up → interessado → convertido
                                                                                     ↘ perdido
```

- Status protegidos: **NUNCA regredir** de `convertido` ou `perdido`
- Status que não devem ser abordados novamente: `abordado`, `respondeu`, `follow_up`, `interessado`, `convertido`, `perdido`
- Apenas abordar leads com status `novo` ou `pronto_para_enviar`
- Follow-up padrão: **7 dias**

## Papel do Gerente Comercial/SDR

### Quando disserem "atualizar histórico do WhatsApp":
1. Rodar `extrair_historico_whatsapp.py` com limite informado
2. Validar CSVs gerados em `output/whatsapp/`
3. Mostrar resumo dos contatos extraídos
4. **Esperar autorização** antes de importar no Supabase

### Quando disserem "preparar campanha de hoje":
1. Buscar leads com status `novo` ou `pronto_para_enviar` apenas
2. Ignorar: `abordado`, `respondeu`, `follow_up`, `interessado`, `convertido`, `perdido`
3. Máximo 15 leads, priorizando: score alto → nicho bom → cidade próxima
4. Gerar mensagem curta, humana e consultiva
5. Gerar link `wa.me` com mensagem pronta
6. **Nunca enviar mensagem automaticamente**

### Quando colarem uma resposta de cliente:
1. Analisar o contexto
2. Sugerir resposta curta, humana e vendedora
3. Ajudar a atualizar o status no Supabase

### Quando um cliente fechar:
1. Montar briefing completo para criar a landing page

### Quando autorizarem importação:
1. Rodar `importar_historico_whatsapp.py` usando `output/whatsapp/historico_whatsapp.csv`
2. Validar se os contatos foram marcados como `abordado`
3. Confirmar que não aparecem mais em `vw_leads_para_abordar`

## Uso da Memória (Regra do Usuário)

**A memória do Hermes funciona como PONTEIRO, não como armazenamento de conteúdo.**
- Na memória: só apontamentos curtos tipo `Skill: local-sales-prospecting`
- Conteúdo detalhado: sempre nas skills (.md) ou nos arquivos de referência
- Se a memória estiver cheia ou perto de encher, consolidar: remover entradas que duplicam skills
- Manter memória leve (~15-20% de uso) para sobrar espaço para coisas novas do momento

**Alertas de modelo (regra do usuário):**
- NUNCA trocar o modelo automaticamente
- Só avisar: "Pra isso, melhor usar **kimi-k2.6** — troca lá e me chama."
- O usuário troca manualmente

## Regras de Comunicação com o Usuário (OBRIGATÓRIO)

1. **Idioma**: SEMPRE responder em português brasileiro. Nunca usar palavras em inglês, espanhol ou chinês, exceto termos técnicos inevitáveis (Supabase, WhatsApp, CRM, Playwright, Python, LP, CTA).
2. **Mensagens para clientes**: 100% em português brasileiro. Revisar e remover termos estrangeiros antes de entregar.
3. **Ser curto, claro e natural**. Não misturar idiomas.
4. **Antes de entregar mensagens de WhatsApp**: revisar e garantir que não têm termos estrangeiros desnecessários.

## Nichos Prioritários (ordem de conversão)

1. Estética / Salão de beleza
2. Barbearia
3. Restaurante / Pizzaria / Comida
4. Serviços locais (eletricista, encanador, etc.)
5. Dentista / Clínica médica
6. Advocacia

## Progresso do Mapeamento (mapear_comercios.py)

### Como funciona
O script `mapear_comercios.py` percorre **bairros/cidades × categorias** no Google Maps via Playwright.

**Total de tarefas por região:**
| Região | Cidades/Bairros | Categorias | Total de tarefas | Leads por tarefa |
|--------|---------------|-----------|-----------------|-----------------|
| baixada | 11 cidades | 40 | 440 | 20 |
| rio_premium | 25 bairros | 28 | 700 | 20 |

Cada tarefa = 1 busca no Google Maps no formato `{categoria} em {bairro/cidade}`. O script tenta coletar até `max_results` leads SEM site por tarefa.

### Como rastrear
O progresso é salvo em tempo real em `output/{regiao}/playwright/progresso.json`. O arquivo pode ter 5-8 MB — NUNCA use `python -c "import json..."` nem `execute_code` nele, vai dar timeout. Use `read_file` com `limit`/`offset` para ler só o necessário.

**Ler progresso (sem timeout):**
```python
# NÃO USE ASSIM (timeout em arquivos grandes):
# python -c "import json; d=json.load(open('progresso.json')); ..."

# USE read_file direto (limit=100, offset=1 já достаua):
# 1. Ler linhas 1-50: categorias_prontas (quantas já concluíram)
# 2. Ler linhas ~280-330: categorias_em_andamento (o que está rodando agora)
# 3. Ler últimas ~20 linhas: fim do array comercios (últimos coletados)
# 4. Grep: "categorias_prontas" count, '"tem_site": false' count, '"nome":' count
```

**Estrutura real do progresso.json:**
```json
{
  "categorias_prontas": ["Bairro::categoria", ...],   // array de strings
  "categorias_em_andamento": {                       // DICT, não lista!
    "Laranjeiras - Rio de Janeiro, RJ::pilates": {
      "indice": 20,
      "total": 60
    }
  },
  "comercios": [{...}, {...}]   // 5000-7000 objetos
}
```

**Métricas rápidas via grep (search_files):**
- Total categorias concluídas: grep `"categorias_prontas": \[` + contar vírgulas
- Em andamento: `grep "categorias_em_andamento"` → ler com `read_file` offset=318 limit=10
- Total comercios: grep `"nome":` count (~5600)
- Sem site: grep `"tem_site": false` count (~2000)

### Comunicação de progresso ao usuário
- **SEMPRE explicar o total**: não dar apenas "X/700" — explicar que são 25 bairros × 28 categorias
- **Mostrar**: tarefas concluídas vs total, leads coletados, qual bairro/categoria está rodando agora
- Se o usuário pedir "progresso detalhado", mostrar: bairros concluídos, categorias por bairro, com/site vs sem/site
- **Cron jobs do Hermes podem não disparar** — não confiar em crons para tracking. Alternativa: usuário pergunta "progresso?" e você verifica manualmente

### Retomada automática
O `progresso.json` salva progresso incremental. Se o browser fechar ou o processo morrer, basta rodar de novo — ele continua de onde parou. **Não perde dados.**

### Pitfalls
- **Chrome órfão**: se o processo Python morre mas o Chromium fica aberto, rodar de novo abre SEGUNDO browser — dois processos escrevem no mesmo `progresso.json`, corrompendo. Solução: matar Chromium orphans (`taskkill /F /IM chrome.exe`) antes de reiniciar, e apagar `progresso.json` para começar limpo.
- **Dedup**: script usa set `nome|cidade` e carrega CSV existente para evitar duplicatas. Não cria duplicados entre execuções.

## Scripts e Arquivos Principais

| Script | Função |
|--------|--------|
| `gerar_lista_diaria.py` | Filtra top 15 leads, gera mensagens WhatsApp e links wa.me |
| `preparar_campanha.py` | Prepara campanha diária com diversificação de nicho/cidade, mensagens humanas e horários recomendados |
| `gerar_painel_prospeccao.py` | Gera dashboard HTML |
| `mapear_comercios.py` | Coleta comércios no Google Maps via Playwright (cidades: Duque de Caxias, Nova Iguaçu, São João de Meriti, Belford Roxo, Nilópolis, Mesquita, Queimados, Itaguaí e outras). Output vai para `output/playwright/progresso.json` (não CSV). Roda em background — verificar progresso com `python -c "import json; d=json.load(open('C:/projetos/script-mapear-comércios/output/playwright/progresso.json')); print(len(d.get('comercios',[])))"` |
| `extrair_historico_whatsapp.py` | Extrai contatos do WhatsApp Web via Playwright |
| `importar_historico_whatsapp.py` | Importa CSV de histórico para o Supabase |
| `import_leads_to_supabase.py` | Importa planilha Excel para o Supabase com deduplicação |
| `importar_csv_playwright.py` | Importa `output/playwright/leads_sem_site.csv` para o Supabase. Deduplicação por telefone_normalizado. Modo seco (dry-run) por padrão, executar com `--confirmar` para importar. NÃO tem coluna `fonte` — usar só colunas existentes. Batch size 50. Criado para importar ~3.132 leads novos da Baixada (06/06), resultando em ~6.487 totais no Supabase. |
| `marcar_lead_enviado.py` | Marca lead como abordado no Supabase via telefone |
| `output/painel/db.py` | Módulo SQLite com funções CRUD e migração |
| `output/painel/server.py` | Backend do dashboard |
| `utils/phone_utils.py` | Normalização de telefone BR e geração de link wa.me |
| `docs/plano-operacional-diario.md` | Rotina diária completa |

## Formato de Mensagem WhatsApp (Abertura)

**REGRA FUNDAMENTAL**: NUNCA usar o nome do negócio como vocativo (ex: "Oi, Fortes!"). Sempre usar saudação genérica + tipo de comércio.

### Estrutura da mensagem de abertura:
`[Saudação] Vi [artigo] [tipo de comércio] no Google e [dor específica]. [proposta de valor curta]. [CTA leve]?`

### Saudações variadas (não repetir no mesmo lote):
- "Olá, tudo bem?"
- "Boa tarde, tudo bem?"
- "Olá! Tudo bem?"

### Artigos e referências por nicho:
- **Salão de beleza**: "seu salão" | **Estética**: "sua clínica de estética" | **Barbearia**: "sua barbearia" | **Pizzaria**: "sua pizzaria" | **Restaurante**: "seu restaurante" | **Dentista**: "sua clínica odontológica" | **Clínica médica**: "sua clínica" | **Pilates**: "seu estúdio de pilates" | **Confeitaria**: "sua confeitaria" | **Bar**: "seu bar" | **Advocacia**: "seu escritório" | **Oficina**: "sua oficina" | **Pet shop**: "seu pet shop"

### 3 variações por tipo de página (alternar no mesmo nicho):

**Tipo: Agendamento (estética, salão, barbearia, dentista, clínica, pilates)**

Dor central: cliente não consegue agendar fácil → perde o cliente que desiste de ligar

1. "Olá, tudo bem? Vi sua clínica de estética no Google e notei que quem procura você provavelmente não te encontra ou desiste antes de ligar. Uma página com agendamento direto pelo WhatsApp mudaria isso — o cliente agenda na hora e você já tem a consulta na agenda. Posso te mostrar como ficaria? É sem compromisso."
2. "Boa tarde, tudo bem? Vi seu salão no Google. Imagina o seguinte: um cliente novo te encontra, gostou do trabalho, mas aí precisa ligar pra marcar — ele provavelmente desiste e procura outro. Com uma página que agenda direto pelo WhatsApp, ele marca na hora. Quer ver como ficaria?"
3. "Olá! Tudo bem? Vi sua barbearia no Google. A maioria dos negócios assim perde cliente porque a pessoa vê o Instagram, quer agendar, mas não quer ligar. Uma página simples com botão de WhatsApp resolve isso. Posso te mandar uma prévia?"

**Tipo: Cardápio (pizzaria, restaurante, confeitaria, padaria, lanchonete)**

Dor central: cliente tem dúvida do que pedir → perde o pedido por falta de info

1. "Olá, tudo bem? Vi sua pizzaria no Google. Sabe o que mais faz o cliente não pedir? Ficar em dúvida do que escolher e não ter como ver os preços. Com um cardápio digital no WhatsApp, ele vê as fotos, escolhe e pede — sem precisar ligar ou mandar mensagem perguntando tudo. Posso te mostrar como ficaria?"
2. "Boa tarde, tudo bem? Vi seu restaurante no Google. O maior problema de não ter cardápio online é o cliente ter que ligar pra perguntar "quanto é oombo?". Muitos desistem. Um cardápio com foto e preço, onde ele pede direto pelo WhatsApp, muda isso. Quer ver como ficaria?"
3. "Olá! Tudo bem? Vi sua confeitaria no Google. O cliente olha, gosta, mas aí pensa "ai nem sei o preço, melhor não". E perde o pedido. Um cardápio digital com fotos e botão de pedido pelo WhatsApp evita isso. Posso te mandar uma prévia?"

**Tipo: Presença (advogado, bar, oficina, pet shop)**

Dor central: não aparece no Google → perde o cliente que está te procurando

1. "Olá, tudo bem? Vi seu escritório de advocacia no Google e pensei: quando alguém precisa de um advogado, a primeira coisa que faz é procurar no Google. Se você não aparece com uma página profissional, perde esse cliente pra quem aparece. Uma presença online simples muda isso. Posso te mostrar como ficaria?"
2. "Boa tarde, tudo bem? Vi seu bar no Google. Imagina o seguinte: um cliente potencial pede "qual o telefone do Bar do Zé?" no Google e aparece o concorrente, não você. Isso acontece todo dia. Uma página com seu endereço, horário e WhatsApp resolve. Quer dar uma olhada?"
3. "Olá! Tudo bem? Vi sua oficina no Google. O mecânico que aparece no Google com avaliações e fotos atrai mais clientes do que o que só existe no boca a boca. Uma página simples com o que você oferece muda isso. Posso te mandar uma prévia?"

---

## Fluxo Completo de Venda

### Etapa 1: Mensagem de abertura
Enviar mensagem com dor + CTA ("posso te mostrar como ficaria?"). Aguardar resposta do lead.

### Etapa 2: Quando lead aceita
Quando o lead responde "sim", "manda", "pode", "quero ver" → seguir este fluxo:

```
1. Acessar Instagram do comércio (MANUAL — usuário tira prints)
2. Baixar todas as fotos disponíveis do negócio
3. Criar LP com Claude Code usando as fotos deles
4. Gravar vídeo da LP (tela do navegador gravando a página)
5. Enviar vídeo pelo WhatsApp para o lead
```

### Etapa 2B: Quando lead pergunta "como seria? e o preço?"
Quando o lead responde com dúvidas sobre funcionamento ou preço, enviar esta mensagem de seguimiento:

**Baixada (R$149):**
> "Boa pergunta! Funciona assim: eu crio uma página personalizada pro seu negócio, com as fotos do seu Instagram, seu endereço, seus serviços e um botão de WhatsApp direto. O cliente entra, vê tudo e manda mensagem na hora. Por R$149, você tem sua página no ar. Mas antes de falar preço, quero te mostrar como ficaria na prática. Posso te mandar um vídeo de como ficaria? É de graça, sem compromisso."

**Rio Premium (R$247-297):**
> "Ótima pergunta. Funciona assim: eu crio uma página profissional personalizada pro seu negócio, com as fotos do seu Instagram, endereço, serviços e um botão de WhatsApp direto. O cliente entra, vê tudo organizado e agenda na hora. O investimento é a partir de R$247. Mas antes de falar números, quero te mostrar como ficaria na prática. Posso te mandar uma prévia? Sem compromisso."

Se o lead aceitar (responder "sim", "quero ver", "pode"), seguir para Etapa 2 (Instagram → LP → vídeo).

### Etapa 3: Mensagem de seguimiento após vídeo
Após enviar o vídeo, enviar mensagem ÚNICA com:

**1. Vídeo + explicação do pixel (mesma mensagem — senão o cliente pensa "já tenho Instagram"):**
> "Aqui está o vídeo da prévia. Reparou que a página tem botão de WhatsApp direto e mostra todos os serviços?
>
> Outra vantagem: quando você fizer tráfego pago — anúncio no Google Ads ou Meta Ads — você consegue ver exatamente quem clicou, quem te chamou no WhatsApp e quanto gastou por cliente. O Instagram sozinho não te dá esse controle. A página sim.
>
> O que achou do visual?"

**2. Depois da resposta do cliente, falar preço + pagamento:**
**Baixada (R$149):**
> "O investimento é R$149, com a página completa no ar. E você só paga depois que a página estiver pronta e funcionando — primeiro eu entrego, você vê, e se gostar aí confirma. Sem risco."

**Rio Premium (R$247-297):**
> "O investimento é R$247, com a página completa no ar. E você só paga depois que a página estiver pronta e funcionando — primeiro eu entrego, você vê, e se gostar aí confirma. Sem risco."

**3. Fechamento — PERGUNTAR "QUER QUE EU CRIE?"**
> "Quer que eu crie a sua? Me manda as fotos que eu já começo."

**Regra de pagamento (OBRIGATÓRIO — sempre usar):**
Só cobrar DEPOIS que a página estiver no ar e funcionando. Isso elimina objeção de confiança.

**Passar credibilidade (nota fiscal):** Não falar "eu emito nota fiscal" diretamente. Deixar subentendido no fechamento:
> "Assim que confirmar, eu preparo a página e já te envio tudo certinho com a nota fiscal de serviço."

**Regra:** NUNCA falar de pixel/tráfego pago na primeira abordagem. Falar SEMPRE na mesma mensagem do vídeo, antes do cliente processar "já tenho Instagram". Usar "tráfego pago" pro Rio Premium, "anúncio pago" ou "impulsionar" pra Baixada.

### Etapa 4: Converter ou arquivar
- **Se converter**: criar briefing completo da LP, coletar pagamento, entregar LP oficial
- **Se não responder**: marcar como follow_up, tentar novamente em 7 dias
- **Se recusar**: marcar como perdido, não tentar novamente

### Etapas específicas:

**Acessar Instagram (MANUAL):**
- Você entra no Instagram manualmente e tira print das fotos do comércio
- Mínimo 5-10 fotos boas
- Salva no projeto pra eu usar na LP
- Se não tiver Instagram ou fotos, usar imagens genéricas do nicho como fallback

**Criar LP com Claude Code:**
- Carregar as fotos baixadas no projeto
- Criar prompt para Claude Code com as fotos e dados do comércio
- Gerar landing page profissional com as fotos reais

**Gravar vídeo:**
- Usar ferramenta de gravação de tela (Loom, OBS, ou similar)
- Gravar a LP completa em formato MP4
- Enviar pelo WhatsApp

**Enviar vídeo:**
- Via WhatsApp Business
- Formato: MP4 ou GIF (até 16MB)
- Mensagem acompanhante: "Aqui está a prévia da página da [nome do negócio]. Assisti e me conta o que acha!"

## Pitfalls

- **Primeiro teste de envio**: no primeiro teste real, enviar APENAS 3 leads (não 15). Mostrar lista antes de enviar. Aguardar confirmação do usuário. Enviar um por um. Após cada envio, marcar como abordado no Supabase com ultimo_contato_em e proximo_followup_em (7 dias). Criar interação em lead_interactions. Parar imediatamente se houver erro, tela estranha, número inválido ou bloqueio. Depois dos 3 envios, entregar relatório com sucessos, falhas, números inválidos e próximos follow-ups.

- **Python no Windows**: `python` pode não estar no PATH. Use sempre `/c/Users/Vanderson/AppData/Local/Programs/Python/Python312/python.exe`
- **Rodar script em background**: scripts como `mapear_comercios.py` rodam em background (não interativo) — verificar output com `process(action='poll', session_id='...')` ou inspecionando o arquivo de progresso. Nunca use `input()` em scripts que rodam em background
- **Progresso do `mapear_comercios.py`**: output vai para `output/playwright/progresso.json` — ler com Python para contar leads coletados. Não há saída de console visível enquanto roda (Playwright Chromium abre janela)
- **WhatsApp Web inacessível**: o navegador do Hermes é separado do Chrome. Para extrair contatos do WhatsApp, use `extrair_historico_whatsapp.py` com Playwright — o usuário precisa escanear QR Code na janela do Chromium que abre
- **SEMPRE verificar se o processo REALMENTE caiu antes de reiniciar**: o Hermes notifica `[IMPORTANT: Background process completed]` mesmo para processos ANTIGOS que já foram substituídos. NUNCA reiniciar baseado só nessa notificação. Verificar com: (1) `process(action='poll')` — checar `status` e `uptime_seconds`, (2) `ps aux | grep mapear_comercios` — ver PIDs reais no sistema, (3) `cat /proc/<pid>/cmdline | tr '\0' ' '` — confirmar qual PID é qual processo. Só reiniciar se ambos mostrarem que o processo morreu. Se abrir um segundo Chromium sem matar o anterior, dois escrevem no mesmo `progresso.json` e corrompem dados.
- **NUNCA matar todos os processos Python sem verificar**: o Hermes Agent roda como processo Python/bash. Antes de matar processos, SEMPRE identificar qual é o Hermes (geralmente bash com `hermes` no cmdline) e quais são scripts do usuário (ex: `mapear_comercios.py`). Matar APENAS os scripts do usuário. Comando seguro: `ps aux | grep python | grep -v grep` → identificar PIDs → `cat /proc/<pid>/cmdline | tr '\0' ' '` → matar SÓ os que são `mapear_comercios.py`.
- **NÃO mudar Playwright para headless=True sem perguntar o usuário**: o usuário gosta de VER o Chrome mapeando. O modo headless esconde a janela e o usuário não consegue acompanhar visualmente. Sempre perguntar antes de alterar `headless=False` para `headless=True`.
- **Scripts com `input()`**: ao rodar scripts em background (não-interativo), qualquer `input()` causa `EOFError`. Comente ou remova confirmações interativas antes de rodar em background
- **Playwright timeout**: o primeiro acesso ao WhatsApp Web precisa de tempo para escanear QR Code. Use `timeout=180000` (3 min) no `wait_for_selector`
- **f-strings com chaves**: em Python, f-strings com expressões multi-linha dentro de chaves causam `SyntaxError`. Use concatenação de strings em vez de f-strings multi-linha com variáveis
- **WhatsApp Web DOM mudou (2025)**: o seletor `div[data-testid="chat-list-item"]` retorna 0 elementos. Use `span[title]` dentro de `div[data-testid="chat-list"]` para extrair nomes de conversas
- **Extração de telefone quebrada**: a função `ler_telefone_da_conversa()` pega o número do PRÓPRIO USUÁRIO ao clicar na conversa. NÃO clique nas conversas para extrair telefone — em vez disso, parse o `span[title]` que mostra `+55 21 9XXXX-XXXX` como número do contato
- **Two-phase WhatsApp extraction**: Phase 1 = Playwright extrai todos `span[title]` da chat-list; Phase 2 = Python processa: títulos com padrão `+55 21 ...` = telefone do contato, outros = nomes de negócio/pessoas sem telefone visível
- **Dados do WhatsApp são intercalados**: conversas aparecem em pares — telefone (+55 21 ...) seguido da última mensagem/nota. Mensagens de prospecção contêm "Vi a [nome] no Google"
- **Sessão do WhatsApp é persistente**: após escanear QR Code uma vez, o perfil `.whatsapp_profile` salva a sessão. Se a sessão expirar, o script volta a pedir QR Code
- **Contatos "sem telefone" do WhatsApp são leads reais**: quando um nome de negócio aparece no WhatsApp sem telefone visível, NÃO descarte como "dado incompleto". Faça match pelo nome contra `output/playwright/leads_sem_site.csv`, `output/playwright/todos_comercios.csv`, `output/consolidado/base_emails_consolidada.csv` e o banco SQLite local. A maioria dos leads abordados pelo painel tem telefone na base — só precisa cruzar os dados
- **Mensagens curtas no WhatsApp são previews de conversas**: entradas como "Sem compromisso, pode", "Obrigada. Ótimo final de semana", "Eu já tenho, obrigada" são **previews de mensagens de leads**, não nomes de contatos. Correspondem a números de telefone já extraídos — não trate como contatos sem telefone separados
- **Contatos excluídos (NÃO são leads)**: Lucia (Vandinho), Padre Paulo Ricardo, TIM Brasil, Carol Nora Cunhada — sempre remover da lista de importação
- **Usuário corrige dados do WhatsApp**: ao mostrar a lista de contatos extraídos, SEMPRE pergunte ao usuário para confirmar/excluir antes de importar. O usuário conhece os contatos melhor que o script
- **CSV encoding BOM bug**: ao salvar CSV com `encoding='utf-8-sig'` (que adiciona BOM), o script `importar_historico_whatsapp.py` deve ler com `encoding='utf-8-sig'` também. Se ler com `encoding='utf-8'` simples, a primeira coluna fica com prefixo `\ufeff` (ex: `\ufefftelefone` em vez de `telefone`), fazendo TODAS as buscas falharem silenciosamente (0 resultados, 0 erros). Sempre use `utf-8-sig` ao ler CSVs gerados com BOM
- **Telefone informado pelo usuário**: quando o usuário fornece telefones manualmente para leads "sem telefone", atualize o CSV imediatamente e reimporte — não deixe campos de telefone vazios na importação final
- **Campanha de prospecção — preparação**: ao preparar campanha, diversificar nichos (máx 2 por nicho) e cidades (máx 5 por cidade). Scores compostos combinam score base + prioridade de nicho × 5 + prioridade de cidade × 3
- **Saudação na mensagem — NUNCA usar nome do negócio como nome de pessoa**: ao gerar mensagens WhatsApp de abertura, NÃO chamar o negócio pelo nome como se fosse pessoa (ex: "Oi, Fortes!" ou "Oi, Casa!" ou "Oi, Estética!"). Em vez disso, usar saudação genérica e referir ao tipo de negócio: "Olá, tudo bem? Vi sua pizzaria no Google…", "Boa tarde, tudo bem? Vi sua clínica de estética no Google…". A abordagem correta é: saudação + tipo de comércio (pizzaria, barbearia, clínica, salão, etc.) — nunca o nome fantasia como vocativo. Cada nicho tem o artigo correto:-seu salão, sua barbearia, sua clínica de estética, seu estúdio de pilates, sua pizzaria, sua clínica odontológica, sua clínica, sua confeitaria, seu restaurante, seu bar, seu escritório de advocacia, sua oficina, seu pet shop
- Mensagens devem ser VARIADAS (3 variações por tipo) para não parecer template em massa ao enviar para múltiplos leads do mesmo nicho
- Saudações variadas: "Olá, tudo bem?", "Boa tarde, tudo bem?", "Olá! Tudo bem?"
- Tipo de página por nicho: agendamento (estética, salão, barbearia, dentista, clínica, pilates, academia, auto escola), cardápio (pizzaria, restaurante, confeitaria, padaria, lanchonete), presença (advogado, bar, oficina, pet shop)
- **Horários de envio por nicho**: estética/salão/barbearia/dentista/pilates/academia/auto escola → 09:00-10:00, pizzaria/restaurante/lanchonete/confeitaria/padaria → 10:30-11:30, bar → 14:00-16:00, advogado/oficina/pet shop → 09:00-11:00
- **Campanha sexta para segunda**: não enviar sexta à noite. Preparar na sexta para segunda de manhã, com mensagens e links wa.me prontos para revisão manual
- **CSV overwrite risk — CSV local NÃO é backup**: toda execução de `mapear_comercios.py` regera `todos_comercios.csv` e `leads_sem_site.csv` do zero. O fluxo real é: `progresso.json` (estado bruto do Playwright) → script gera CSV mesclando 0 existentes + novos do JSON. Se o script rodar 2x, o segundo execution sobrescreve o `progresso.json` primeiro, depois o CSV é gerado do JSON atualizado — todos os dados do primeiro execution são perdidos. Sempre importar para o Supabase IMEDIATAMENTE após cada mapeamento, antes de qualquer nova execução. Nunca confiar que o CSV ou JSON accumulate — ambos são regerados do zero.

- **SEMPRE comparar CSV novo com Supabase antes de assumir "são todos novos"**: em 2025-06-06, um CSV de 7.142 leads tinha ~1.348 duplicados (mesmo telefone) já existentes no Supabase. O usuário pensou que eram todos novos. Sempre fazer a deduplicação por telefone antes de qualquer afirmação sobre quantidade de leads novos. Código de comparação em `references/supabase-leads-schema.md`.
- **Protocolo "quantos são novos?": nunca responder de memória — sempre rodar dedup**: (1) baixar telefones do Supabase paginando com `.range(0, 1000)`, (2) normalizar CSV e Supabase (remover não-dígitos, lstrip('55')), (3) set intersection. Só então dar o número real ao usuário. Esse número muda a cada importação.
- **Phone normalization para comparação CSV vs Supabase**: ao cruzar telefones entre CSV e Supabase, normalizar assim: (1) remover todos os caracteres não-dígitos, (2) no Supabase, telefones são armazenados sem o prefixo 55 (ex: `552127564153` → `2127564153`); no CSV, telefones vêm como `21) 97554-7868` → normalizar para `21975547868`. Comparar去除 o `55` do Supabase. Exemplo de código: `def normalize_phone(digits): return ''.join(c for c in str(digits) if c.isalnum()).lstrip('55') if .startswith('55') else ''.join(c for c in str(digits) if c.isalnum())` — usar isso antes de fazer set intersection.
- **Quando o usuário diz que já tinha X leads antes**: o fluxo típico é ~7.000 leads brutos → filtrados para ~3.355 leads "bons sem site" → importados para o Supabase. O `progresso.json` só guarda o último mapeamento (7.142), não os anteriores. Se o usuário mencionar que tinha uma base anterior, ela pode estar no Supabase (se foi importada) ou perdida (se não foi). Sempre verificar Supabase primeiro antes de assumir perda.
- **Supabase como backup autoritativo**: o Supabase tem ~6.487 leads (2025-06-06). Sempre que `mapear_comercios.py` rodar e entregar novos leads, importar para o Supabase logo em seguida via `import_leads_to_supabase.py`. Nunca confiar que o CSV local accumulating — ele não acumula.

- **Resultado mapeamento Baixada 06/06/2026**: 7.142 total, 4.429 sem site. Comparando com Supabase (~6.487 leads): ~1.348 duplicados → ~5.794 leads NOVOS para importar. Verificar sempre com dedup por telefone antes de afirmar "são todos novos".
- **Distribuição atual do Supabase (2025-06-06)**:\\n  - Total: ~6.487 leads (NÃO 1.000 — o cliente Python retorna max 1.000 por padrão; use `.range()` para paginação ou `count='exact'`)\\n  - Importados de 2 fontes: 3.355 (base original 05/06) + 3.132 (playwright Baixada 06/06)\\n  - 802 leads sem contato do CSV foram descartados\\n  - Ver `references/supabase-leads-schema.md` para distribuição completa por cidade e nicho\\n- **Novo mapeamento 06/06 (playwright)**: 7.142 leads totais, 4.429 sem site em `output/playwright/leads_sem_site.csv`. Apenas ~1.348 duplicados com Supabase → ~5.794 leads novos. Importar via `import_leads_to_supabase.py --arquivo output/playwright/leads_sem_site.csv` após confirmar com o usuário.\\n
- **Script `import_leads_to_supabase.py`**: importa CSV para o Supabase com deduplicação por telefone.Rodar com `.env` carregado (`source .env` ou carregar manualmente no Python). Tabela destino: `leads`.
- **Supabase pagination pitfall**: o cliente Python do Supabase retorna NO MÁXIMO 1.000 linhas por query por padrão. Se a tabela tem mais de 1.000 registros, precisa usar `.range(offset, offset+batch_size)` para paginar manualmente, ou usar `count='exact'` via `.select('*', count='exact')` para obter o total real. Nunca assumir que `len(data.data)` é o total — é apenas a primeira página.
- **SQLite local será eliminado**: Supabase é a fonte oficial (3.355 leads em 2025-06-06). O SQLite local (56 leads em `output/painel/prospeccao.db`) está sendo substituído — Claude Code está migrando o painel pra ler direto do Supabase. NÃO sincronizar o SQLite local, vai ser removido em breve
- **WhatsApp Web envio automático FUNCIONA**: após escanear QR Code no perfil `.whatsapp_business_profile`, o envio via Playwright funciona. O fluxo é: (1) verificar se está logado, (2) se não, aguardar escaneamento, (3) navegar para `web.whatsapp.com/send?phone={tel}&text={msg_encoded}`, (4) clicar no botão `aria-Enviar` (não `data-testid="send"` — mudou). Botão enviar tem `aria-label="Enviar"`, não `data-testid="send"`
- **Discord gateway conectado**: bot1512676735886426262, server Hermes (ID: 1512676518856364122), canal #geral. Usar `@bot1512676735886426262` para mencionar. Modelo: `minimax-m2.7` via `ollama-cloud` (minúsculo obrigatório). Variável: `DISCORD_BOT_TOKEN` (não `DISCORD_TOKEN`). Message Content Intent obrigatório no Developer Portal. Para mudar modelo: `hermes config set model.default minimax-m2.7 && hermes config set model.provider ollama-cloud`. Resetar sessão: mandar `/new` no Discord.
- **Telegram bloqueado pelo Spambot**: Não é possível criar bots em contas novas. Usar Discord como canal de acesso remoto.
- **PC do trabalho = principal**: Vanderson é o TI, pode deixar ligado 24h. Scripts vão por GitHub. WhatsApp Business separado em cada PC.
- **Sessão do WhatsApp Business foi estabelecida**: durante a sessão de 2025-06-05, o perfil `.whatsapp_business_profile` foi conectado com sucesso via QR Code. A partir de agora, o envio automático deve funcionar sem precisar escanear novamente (até expirar)
- **Selector do botão enviar**: o WhatsApp Web atual usa `button[aria-label="Enviar"]` em vez de `button[data-testid="send"]`. Sempre verificar ambos — `data-testid` foi deprecado
- **WhatsApp potencial vs campo explícito**: o CSV do Playwright mostra campo `whatsapp` apenas quando há link direto visível no Google Maps (~22%). MAS no Brasil celular = WhatsApp. Dos 7.142 leads, 86.7% têm telefone → praticamente TODOS têm WhatsApp potencial. Nunca usar o baixo valor do campo `whatsapp` como justificativa para não contatar.
- **wa.me vs web.whatsapp.com/send para envio**: ao usar Playwright para envio automático, NÃO use `wa.me/{tel}?text={msg}` — essa URL redireciona para uma página intermediária "Compartilhe no WhatsApp" que NÃO tem a caixa de texto e NÃO permite envio programático. Em vez disso, use `https://web.whatsapp.com/send?phone={tel}&text={quote(msg)}` diretamente, que abre a conversa no WhatsApp Web com a mensagem pré-preenchida
- **Playwright Chromium crash com perfil lock**: se o Playwright Chromium crashar ao iniciar com `launch_persistent_context`, pode ser porque o diretório de perfil tem um lock file (`SingletonLock`, `SingletonCookie`, `SingletonSocket`) de uma sessão anterior que não fechou corretamente. Solução: deletar esses arquivos de lock antes de iniciar, ou fechar todos os processos Chrome/Chromium com `taskkill /F /IM chrome.exe`
- **Perfil `.whatsapp_business_profile` é o correto para envio**: o perfil `.whatsapp_profile` é para extração (WhatsApp pessoal). O perfil `.whatsapp_business_profile` é para envio automatizado de mensagens de prospecção
- **Supabase coluna 'fonte' não existe** — ao inserir leads no Supabase, a tabela `leads` NÃO tem coluna `fonte`. Erro: `Could not find the 'fonte' column of 'leads' in the schema cache`. Usar apenas colunas existentes: `nome, telefone, whatsapp, telefone_normalizado, instagram, email, categoria, cidade, bairro, endereco, tem_site, url_site, avaliacao, num_avaliacoes, score, prioridade, oferta_sugerida, mensagem_whatsapp, link_whatsapp, status, origem, observacoes`. Verificar schema no Supabase antes de inserir com colunas novas.
- **Batch insert size 50 funciona, 100 pode falhar** — inserções em lote no Supabase com 50 registros por batch funcionam confiavelmente. Evitar lotes maiores (100+) — podem causar timeout ou limite de payload.
- **Sempre verificar respostas do lead**: quando o usuário perguntar "o lead respondeu?" ou "chegou resposta?", NÃO perguntar o que o lead respondeu — em vez disso, abrir o WhatsApp Web e ler a conversa diretamente via `inner_text()` do DOM. O usuário espera que você saiba a resposta, não que ele te conte
- **inner_text() do conversation-panel-messages funciona - o seletor [data-testid=conversation-panel-messages] com inner_text() retorna o texto completo da conversa incluindo horas e mensagens. Usar para capturar resposta do lead sem perguntar ao usuario

- **Model name case-sensitivity**: `minimax-m2.7` (minúsculo OBRIGATÓRIO). `MiniMax-M2.7` com maiúsculas causa HTTP 404 no ollama-cloud. Depois de mudar modelo no config: `hermes config set model.default minimax-m2.7 && hermes config set model.provider ollama-cloud`, depois reiniciar gateway: `hermes gateway stop && hermes gateway run --replace`. Se o bot Discord insistir que está usando modelo errado, mandar `/new` para resetar sessão (histórico antigo influencia).

- **Discord bot só responde com @menção**: `@bot1512676735886426262 mensagem`. Se não responder, verificar: (1) gateway rodando, (2) modelo minúsculo no config, (3) Privileged Gateway Intents habilitados no Developer Portal, (4) `DISCORD_BOT_TOKEN` (não `DISCORD_TOKEN`) no `.env`.
- **Skill de escolha de LLM**: `skill:llm-model-selection` — usar minimax-m2.7 (rotina), glm-5.1 (estratégia/importante), kimi-k2.6 (copy), deepseek-v4-flash (simples/econômico), deepseek-pro (bugs).
- **Usuário prefere respostas diretas e curtas em PT-BR**: sem rodeios, sem explicações longas. Ir direto ao ponto.

Preco e duvidas - quando lead pergunta como seria e o preco enviar mensagem de seguimiento explicando funcionamento (R$ 97 a R$ 197) e oferecendo video gratuito. Se aceitar seguir fluxo normal Instagram LP video**: o seletor `[data-testid="conversation-panel-messages"]` com `inner_text()` retorna o texto completo da conversa, incluindo horas e mensagens. É assim que se captura a resposta do lead sem perguntar ao usuário

## Arquivos de Referência

- `references/message-templates-pain-focus.md` — Templates de mensagens com foco em dor (9 variações, 3 tipos de página, mensagens de acompanhamento)
- `references/message-templates-and-db-schema.md` — Templates de mensagem, schema Supabase + SQLite e instruções de importação
- `references/whatsapp-extraction-playbook.md` — Playbook de extração WhatsApp (two-phase approach, bugs corrigidos, DOM atualizado)
- `references/whatsapp-sending-playbook.md` — Playbook de envio WhatsApp via Playwright (enviar_teste_whatsapp_business.py, sessão expira, wa.me vs web.whatsapp.com, Chromium crash fix)
- `references/gateway-setup.md` — Configuração de acesso remoto (Telegram e Discord), criação de bots, pitfalls
- `references/playwright-csv-import.md` — Importação de `leads_sem_site.csv` do Playwright para o Supabase, colunas, pitfalls (fonte não existe, batch 50)
- `references/rio-premium-mapeamento-20260606.md` — Sessão de mapeamento Rio Premium: config, importação Supabase, preços, lições sobre processo/browser/cron