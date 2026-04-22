"""Gerar todos os templates de email por categoria"""
import os

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

TEMPLATE_DATA = {
    "bar": {"color": "#f59e0b", "stat": "72%", "stat_text": "escolhem o bar pelo Instagram/site antes de ir", "hero_h1": "{nome}, quando o cliente quer uma noite boa em {cidade}, encontra seu bar?", "problem": "Seu bar aparece no Google Maps, mas quando o cliente quer ver cardápio, eventos, horário — não encontra um site.", "stat_detail": "72% dos clientes escolhem o bar pelo Instagram ou site antes de sair de casa. Sem presença digital, perde essa galera pro concorrente.", "checks": ["Cardápio digital com <strong>preços e promoções</strong>", "Cliente vê eventos e <strong>agenda direto</strong>", "Integração com <strong>Instagram</strong> pra atrair mais gente", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Cardápio Digital", "#f59e0b", "QR Code na mesa &bull; Atualização fácil &bull; Sem comissão"), ("Chatbot WhatsApp", "#22c55e", "Auto-respostas &bull; 24h disponível &bull; Reservas"), ("Gestão Instagram", "#ec4899", "Postagens agendadas &bull; Stories de eventos &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "clinica_medica": {"color": "#0ea5e9", "stat": "82%", "stat_text": "pesquisam clínica médica online antes de agendar", "hero_h1": "{nome}, quando o paciente procura sua clínica em {cidade}, encontra um site profissional?", "problem": "Sua clínica em {cidade} aparece no Google Maps, mas quando o paciente quer saber mais — ver especialidades, convênios, horários — não encontra um site.", "stat_detail": "82% dos pacientes pesquisam a clínica online antes de agendar. Sem site profissional, perde esses pacientes.", "checks": ["Mostra suas <strong>especialidades e convênios</strong>", "Paciente <strong>agenda direto pelo site</strong>", "Transmite <strong>credibilidade e confiança</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Agendamento Online", "#0ea5e9", "Agenda integrada &bull; Confirmação automática &bull; Lembrete"), ("Chatbot WhatsApp", "#22c55e", "Triagem automática &bull; 24h disponível &bull; Coleta de dados"), ("Gestão Instagram", "#ec4899", "Dicas de saúde &bull; Posts agendados &bull; Authority"), ("Portal do Paciente", "#8b5cf6", "Resultados online &bull; Histórico &bull; Seguro e prático")]},
    "clinica_veterinaria": {"color": "#8b5cf6", "stat": "76%", "stat_text": "dos donos de pet pesquisam veterinário online", "hero_h1": "{nome}, quando o dono de pet procura uma clínica em {cidade}, encontra a sua?", "problem": "Sua clínica veterinária em {cidade} aparece no Google Maps, mas quando o dono de pet quer saber mais — ver serviços, preços, estrutura — não encontra um site.", "stat_detail": "76% dos donos de pet pesquisam veterinário online antes de levar o animal. Sem site, esses tutores vão pro concorrente.", "checks": ["Mostra seus <strong>serviços e especialidades</strong>", "Dono de pet <strong>agenda pelo site ou WhatsApp</strong>", "Galeria de fotos da <strong>estrutura e equipe</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Agendamento Online", "#0ea5e9", "Consulta e vacina &bull; Lembrete &bull; Prático"), ("Chatbot WhatsApp", "#22c55e", "Dúvidas 24h &bull; Emergência &bull; Banco de perguntas"), ("Gestão Instagram", "#ec4899", "Fotos de pets &bull; Dicas veterinárias &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "confeitaria": {"color": "#ec4899", "stat": "68%", "stat_text": "encomendam doces de confeitarias que aparecem online", "hero_h1": "{nome}, quando o cliente quer encomendar doces em {cidade}, encontra sua confeitaria?", "problem": "Sua confeitaria em {cidade} faz doces incríveis, mas quando o cliente quer ver o catálogo e preços — não encontra online.", "stat_detail": "68% encomendam doces de confeitarias que aparecem online. Sem catálogo digital, perde encomendas toda semana.", "checks": ["Catálogo de doces com <strong>fotos e preços</strong>", "Cliente <strong>encomenda direto pelo site</strong>", "Mostra seus <strong>diferenciais e Ingredientes</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Digital", "#ec4899", "Fotos profissionais &bull; Preços &bull; Atualização fácil"), ("Encomendas Online", "#f59e0b", "Formulário &bull; WhatsApp &bull; Confirmação"), ("Gestão Instagram", "#22c55e", "Stories de produção &bull; Posts agendados &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "curso_pre_vestibular": {"color": "#8b5cf6", "stat": "88%", "stat_text": "dos alunos pesquisam cursinho online antes de matricular", "hero_h1": "{nome}, quando o aluno procura cursinho em {cidade}, encontra o seu?", "problem": "Seu cursinho em {cidade} prepara alunos pra aprovação, mas quando o aluno pesquisa — não encontra turmas, preços, nem resultados.", "stat_detail": "88% dos alunos pesquisam cursinho online antes de matricular. Sem site, perde matrículas todo mês.", "checks": ["Mostra <strong>turmas, horários e preços</strong>", "Aluno se <strong>matricula direto pelo site</strong>", "Resultados de <strong>aprovações anteriores</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Matrícula Online", "#8b5cf6", "Formulário &bull; Pagamento &bull; Confirmação automática"), ("Chatbot WhatsApp", "#22c55e", "Dúvidas 24h &bull; Simulado &bull; Informações"), ("Gestão Instagram", "#ec4899", "Dicas de estudo &bull; Aprovados &bull; Reports"), ("Portal do Aluno", "#0ea5e9", "Notas &bull; Material &bull; Simulados online")]},
    "eletricista": {"color": "#f59e0b", "stat": "79%", "stat_text": "procuram eletricista no Google antes de ligar", "hero_h1": "{nome}, quando precisam de um eletricista em {cidade}, encontram você?", "problem": "Você é um profissional excelente, mas quando o cliente busca eletricista em {cidade} — não encontra seus serviços nem depoimentos online.", "stat_detail": "79% procuram eletricista no Google antes de ligar. Sem site, esses clientes chamam o concorrente.", "checks": ["Mostra seus <strong>serviços e especialidades</strong>", "Cliente solicita <strong>orçamento pelo site</strong>", "Depoimentos de <strong>clientes satisfeitos</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Orçamento Online", "#f59e0b", "Formulário &bull; WhatsApp &bull; Resposta rápida"), ("Chatbot WhatsApp", "#22c55e", "Orçamento automático &bull; 24h &bull; Emergência"), ("Gestão Instagram", "#ec4899", "Antes/depois &bull; Dicas elétricas &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "encanador": {"color": "#0ea5e9", "stat": "81%", "stat_text": "pesquisam encanador online em emergências", "hero_h1": "{nome}, quando o cano estoura em {cidade}, encontram você rápido?", "problem": "Em emergência, o cliente corre pro Google. Seu nome aparece, mas sem site com telefone claro e serviços — ele liga pro concorrente.", "stat_detail": "81% pesquisam encanador online em emergências. Sem site, perde essas ligações urgentes.", "checks": ["Telefone e WhatsApp <strong>sempre visíveis</strong>", "Lista de <strong>serviços e urgências</strong>", "Depoimentos de <strong>clientes anteriores</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Botão Emergência", "#ef4444", "Destaque vermelho &bull; Clique e liga &bull; WhatsApp"), ("Orçamento Online", "#0ea5e9", "Formulário &bull; Fotos do problema &bull; Resposta"), ("Gestão Instagram", "#ec4899", "Antes/depois &bull; Dicas &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "escola_de_idiomas": {"color": "#0ea5e9", "stat": "85%", "stat_text": "pesquisam escola de idiomas online antes de matricular", "hero_h1": "{nome}, quando o aluno quer aprender idiomas em {cidade}, encontra sua escola?", "problem": "Sua escola de idiomas em {cidade} tem ótimos professores, mas quando o aluno pesquisa — não encontra metodologia, turmas, nem preços.", "stat_detail": "85% pesquisam escola de idiomas online antes de matricular. Sem site, perde alunos pra escola que tem.", "checks": ["Mostra <strong>idiomas, turmas e horários</strong>", "Aluno faz <strong>teste de nível online</strong>", "Depoimentos de <strong>alunos que fluenciaram</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Teste de Nível", "#0ea5e9", "Online &bull; Automático &bull; Indica turma certa"), ("Matrícula Online", "#8b5cf6", "Formulário &bull; Pagamento &bull; Confirmação"), ("Chatbot WhatsApp", "#22c55e", "Dúvidas 24h &bull; Informações &bull; Agendamento"), ("Gestão Instagram", "#ec4899", "Dicas diárias &bull; Stories &bull; Reports")]},
    "estetica": {"color": "#ec4899", "stat": "83%", "stat_text": "pesquisam clínica estética online antes de agendar", "hero_h1": "{nome}, quando a cliente quer tratamento estético em {cidade}, encontra sua clínica?", "problem": "Sua clínica estética em {cidade} tem ótimos tratamentos, mas quando a cliente pesquisa — não encontra procedimentos, preços, nem resultados.", "stat_detail": "83% pesquisam clínica estética online antes de agendar. Sem site com antes/depois, perde clientes.", "checks": ["Catálogo de <strong>tratamentos e preços</strong>", "Galeria de <strong>antes e depois</strong>", "Cliente <strong>agenda direto pelo site</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Tratamentos", "#ec4899", "Procedimentos &bull; Preços &bull; Resultados"), ("Agendamento Online", "#0ea5e9", "Agenda integrada &bull; Confirmação &bull; Lembrete"), ("Gestão Instagram", "#22c55e", "Antes/depois &bull; Stories &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "estudio_de_pilates": {"color": "#8b5cf6", "stat": "78%", "stat_text": "procuram estúdio de pilates online", "hero_h1": "{nome}, quando o aluno procura pilates em {cidade}, encontra seu estúdio?", "problem": "Seu estúdio em {cidade} tem estrutura excelente, mas quando o aluno pesquisa — não encontra horários, planos, nem fotos do espaço.", "stat_detail": "78% procuram estúdio de pilates online. Sem site, perde alunos pro concorrente.", "checks": ["Mostra <strong>modalidades e horários</strong>", "Aluno <strong>agenda aula experimental</strong> pelo site", "Fotos da <strong>estrutura e equipamentos</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Agendamento Online", "#0ea5e9", "Aula experimental &bull; Recorrente &bull; Confirmação"), ("Chatbot WhatsApp", "#22c55e", "Dúvidas 24h &bull; Horários &bull; Agendamento"), ("Gestão Instagram", "#ec4899", "Exercícios &bull; Dicas de saúde &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "farmacia": {"color": "#22c55e", "stat": "71%", "stat_text": "pesquisam farmácia no Google antes de ir", "hero_h1": "{nome}, quando o cliente precisa de remédio em {cidade}, encontra sua farmácia?", "problem": "Sua farmácia em {cidade} tem o que o cliente precisa, mas quando ele pesquisa — não encontra se tem o remédio nem promoções.", "stat_detail": "71% pesquisam farmácia no Google antes de sair de casa. Sem site, o cliente vai na concorrente.", "checks": ["Mostra <strong>promoções e ofertas da semana</strong>", "Cliente vê se tem o <strong>remédio disponível</strong>", "Integração com <strong>delivery</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Ofertas da Semana", "#f59e0b", "Promoções &bull; Atualização fácil &bull; Destaques"), ("Delivery Online", "#22c55e", "Pedido pelo site &bull; WhatsApp &bull; Rápido"), ("Chatbot WhatsApp", "#0ea5e9", "Verificar preço &bull; 24h &bull; Disponibilidade"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "floricultura": {"color": "#ec4899", "stat": "70%", "stat_text": "encomendam flores online", "hero_h1": "{nome}, quando o cliente quer flores em {cidade}, encontra sua floricultura?", "problem": "Suas flores são lindas, mas quando o cliente quer ver arranjos e preços — não encontra online.", "stat_detail": "70% encomendam flores pela internet. Sem catálogo digital, perde vendas todos os dias.", "checks": ["Catálogo de <strong>arranjos com fotos e preços</strong>", "Cliente <strong>encomenda direto pelo site</strong>", "Mostra <strong>ocasiões especiais</strong> (aniversário, casamento)", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Online", "#ec4899", "Fotos &bull; Preços &bull; Atualização fácil"), ("Encomendas Online", "#f59e0b", "Formulário &bull; WhatsApp &bull; Entrega"), ("Gestão Instagram", "#22c55e", "Stories &bull; Arranjos do dia &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "imobiliaria": {"color": "#2563eb", "stat": "90%", "stat_text": "buscam imóvel online antes de visitar", "hero_h1": "{nome}, quando o cliente procura imóvel em {cidade}, encontra sua imobiliária?", "problem": "Sua imobiliária em {cidade} tem ótimos imóveis, mas quando o cliente pesquisa — não encontra um site com portfólio.", "stat_detail": "90% buscam imóvel online antes de visitar. Sem site com fotos e detalhes, perde clientes.", "checks": ["Portfólio de <strong>imóveis com fotos e detalhes</strong>", "Busca por <strong>tipo, bairro e preço</strong>", "Cliente entra em <strong>contato direto</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Portfólio Imóveis", "#2563eb", "Fotos &bull; Detalhes &bull; Busca avançada"), ("Busca Online", "#0ea5e9", "Filtros &bull; Mapa &bull; Favoritos"), ("Chatbot WhatsApp", "#22c55e", "Agendamento visita &bull; Dúvidas &bull; 24h"), ("Gestão Instagram", "#ec4899", "Imóveis &bull; Dicas &bull; Reports")]},
    "joalheria": {"color": "#f59e0b", "stat": "76%", "stat_text": "pesquisam joalheria online antes de comprar", "hero_h1": "{nome}, quando o cliente quer joias em {cidade}, encontra sua loja?", "problem": "Suas joias são bonitas, mas quando o cliente pesquisa — não encontra catálogo com peças e preços.", "stat_detail": "76% pesquisam joalheria online antes de comprar. Sem vitrine digital, perde vendas.", "checks": ["Catálogo de <strong>peças com fotos e preços</strong>", "Cliente solicita <strong>orçamento personalizado</strong>", "Destaque para <strong>ocasiões especiais</strong> (casamento, noivado)", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Online", "#f59e0b", "Fotos &bull; Preços &bull; Atualização"), ("Encomendas", "#ec4899", "Sob medida &bull; WhatsApp &bull; Orçamento"), ("Gestão Instagram", "#22c55e", "Peças em destaque &bull; Stories &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "lanchonete": {"color": "#f97316", "stat": "75%", "stat_text": "pedem lanche pelo celular", "hero_h1": "{nome}, seu lanche é o melhor de {cidade}, mas o cliente te encontra online?", "problem": "Sua lanchonete faz o melhor lanche de {cidade}, mas depende de apps de delivery que cobram 20% de comissão em cada pedido.", "stat_detail": "75% pedem lanche pelo celular. Sem site próprio, você trabalha pro iFood.", "checks": ["Cardápio digital com <strong>pedidos diretos</strong> — sem comissão", "Cliente pede pelo <strong>WhatsApp ou site</strong>", "Recebe <strong>pagamentos online</strong> via Mercado Pago", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Cardápio QR Code", "#f97316", "QR Code na mesa &bull; Atualização fácil &bull; Sem taxa"), ("Pedidos Online", "#22c55e", "Pelo site &bull; WhatsApp &bull; Direto pra cozinha"), ("Chatbot WhatsApp", "#0ea5e9", "Auto-respostas &bull; Cardápio &bull; Pedidos"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "lavanderia": {"color": "#0ea5e9", "stat": "68%", "stat_text": "procuram lavanderia no celular", "hero_h1": "{nome}, quando o cliente precisa de lavanderia em {cidade}, encontra a sua?", "problem": "Sua lavanderia em {cidade} presta ótimo serviço, mas quando o cliente pesquisa — não encontra serviços, preços, nem como pedir coleta.", "stat_detail": "68% procuram lavanderia no celular. Sem site, o cliente liga pra concorrente.", "checks": ["Tabela de <strong>preços e serviços</strong>", "Cliente solicita <strong>coleta e entrega</strong>", "Mostra seus <strong>diferenciais</strong> (produtos, cuidado)", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Preços Online", "#0ea5e9", "Tabela clara &bull; Atualização fácil &bull; Detalhes"), ("Coleta Delivery", "#22c55e", "Solicitação &bull; WhatsApp &bull; Agendamento"), ("Chatbot WhatsApp", "#f59e0b", "Orçamento &bull; Status &bull; 24h"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "loja_de_bicicleta": {"color": "#10b981", "stat": "74%", "stat_text": "pesquisam loja de bicicleta online", "hero_h1": "{nome}, quando o ciclista procura peças e bicicletas em {cidade}, encontra sua loja?", "problem": "Sua loja em {cidade} tem tudo pra ciclista, mas quando ele pesquisa — não encontra produtos, marcas, nem oficina.", "stat_detail": "74% pesquisam loja de bicicleta online. Sem vitrine digital, perde vendas.", "checks": ["Catálogo de <strong>produtos e marcas</strong>", "Cliente pede <strong>orçamento pelo site</strong>", "Mostra <strong>serviço de oficina</strong> e acessórios", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Online", "#10b981", "Produtos &bull; Marcas &bull; Fotos"), ("Orçamento", "#0ea5e9", "Formulário &bull; WhatsApp &bull; Resposta"), ("Chatbot WhatsApp", "#22c55e", "Dúvidas &bull; Estoque &bull; Preço"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "loja_de_celulares": {"color": "#6366f1", "stat": "88%", "stat_text": "pesquisam celular online antes de comprar", "hero_h1": "{nome}, quando o cliente quer comprar celular em {cidade}, encontra sua loja?", "problem": "Sua loja em {cidade} tem os melhores preços, mas quando o cliente pesquisa — não encontra modelos, preços, nem assistência técnica.", "stat_detail": "88% pesquisam celular online antes de comprar. Sem vitrine digital, perde vendas todo dia.", "checks": ["Vitrine de <strong>modelos e preços</strong>", "Destaque para <strong>ofertas e promoções</strong>", "Mostra <strong>assistência técnica</strong> e acessórios", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Vitrine Online", "#6366f1", "Modelos &bull; Preços &bull; Atualização"), ("Orçamento", "#0ea5e9", "Formulário &bull; WhatsApp &bull; Resposta"), ("Chatbot WhatsApp", "#22c55e", "Estoque &bull; Preço &bull; 24h"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "loja_de_moveis": {"color": "#d97706", "stat": "82%", "stat_text": "pesquisam móveis online antes de comprar", "hero_h1": "{nome}, quando o cliente quer mobiliar a casa em {cidade}, encontra sua loja?", "problem": "Sua loja em {cidade} tem móveis bonitos e preços bons, mas quando o cliente pesquisa — não encontra catálogo.", "stat_detail": "82% pesquisam móveis online. Sem catálogo digital, perde vendas.", "checks": ["Catálogo de <strong>móveis com fotos e preços</strong>", "Cliente solicita <strong>orçamento personalizado</strong>", "Mostra <strong>ambientes montados</strong> pra inspirar", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Online", "#d97706", "Fotos &bull; Preços &bull; Ambientes"), ("Orçamento", "#0ea5e9", "Formulário &bull; WhatsApp &bull; Medidas"), ("Gestão Instagram", "#ec4899", "Ambientes &bull; Promoções &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "loja_de_roupas": {"color": "#ec4899", "stat": "85%", "stat_text": "veem a loja online antes de visitar", "hero_h1": "{nome}, quando a cliente quer roupas novas em {cidade}, encontra sua loja?", "problem": "Suas roupas são lindas, mas quando a cliente pesquisa — não encontra vitrine, novidades, nem promoções.", "stat_detail": "85% veem a loja online antes de visitar. Sem vitrine digital, perde clientes.", "checks": ["Vitrine de <strong>coleções e novidades</strong>", "Destaque para <strong>promoções e liquidações</strong>", "Cliente pede pelo <strong>WhatsApp</strong> com foto", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Vitrine Online", "#ec4899", "Fotos &bull; Coleções &bull; Novidades"), ("Encomendas WhatsApp", "#f59e0b", "Foto &bull; Tamanho &bull; Reserva"), ("Gestão Instagram", "#22c55e", "Looks do dia &bull; Stories &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "marcenaria": {"color": "#92400e", "stat": "72%", "stat_text": "procuram marceneiro no Google", "hero_h1": "{nome}, quando precisam de móveis sob medida em {cidade}, encontram sua marcenaria?", "problem": "Sua marcenaria em {cidade} faz trabalhos incríveis, mas quando o cliente pesquisa — não encontra portfólio de projetos.", "stat_detail": "72% procuram marceneiro no Google. Sem portfólio online, o cliente chama o concorrente.", "checks": ["Portfólio de <strong>projetos com fotos antes/depois</strong>", "Cliente solicita <strong>orçamento pelo site</strong>", "Mostra <strong>materiais e acabamentos</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Portfólio Online", "#92400e", "Fotos &bull; Projetos &bull; Antes/depois"), ("Orçamento", "#0ea5e9", "Formulário &bull; Medidas &bull; WhatsApp"), ("Gestão Instagram", "#ec4899", "Projetos &bull; Processo &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "material_de_construcao": {"color": "#f97316", "stat": "75%", "stat_text": "pesquisam materiais de construção online", "hero_h1": "{nome}, quando o pedreiro ou cliente precisa de material em {cidade}, encontra sua loja?", "problem": "Sua loja em {cidade} tem tudo pra construção, mas quando o cliente pesquisa — não encontra se tem o que precisa.", "stat_detail": "75% pesquisam materiais online. Sem site, o cliente vai no concorrente que aparece.", "checks": ["Catálogo de <strong>produtos e marcas</strong>", "Destaque para <strong>ofertas da semana</strong>", "Cliente pede <strong>orçamento e entrega</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Online", "#f97316", "Produtos &bull; Preços &bull; Estoque"), ("Orçamento", "#0ea5e9", "Formulário &bull; Lista &bull; WhatsApp"), ("Chatbot WhatsApp", "#22c55e", "Preço &bull; Estoque &bull; Entrega"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "otica": {"color": "#6366f1", "stat": "74%", "stat_text": "procuram ótica online antes de comprar óculos", "hero_h1": "{nome}, quando o cliente precisa de óculos em {cidade}, encontra sua ótica?", "problem": "Sua ótica em {cidade} tem ótimos modelos, mas quando o cliente pesquisa — não encontra catálogo, preços, nem exame de vista.", "stat_detail": "74% procuram ótica online. Sem vitrine digital, perde clientes.", "checks": ["Catálogo de <strong>óculos com fotos e preços</strong>", "Mostra <strong>exame de vista e convênios</strong>", "Cliente <strong>agenda pelo site</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Online", "#6366f1", "Modelos &bull; Preços &bull; Marcas"), ("Agendamento", "#0ea5e9", "Exame de vista &bull; Confirmação &bull; Lembrete"), ("Gestão Instagram", "#ec4899", "Modelos &bull; Depoimentos &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "padaria": {"color": "#d97706", "stat": "70%", "stat_text": "dos clientes procuram padaria no celular antes de sair", "hero_h1": "{nome}, quando o cliente quer pão fresquinho em {cidade}, encontra sua padaria?", "problem": "Sua padaria em {cidade} faz os melhores pães, mas quando o cliente pesquisa — não encontra cardápio, promoções, nem horário.", "stat_detail": "70% dos clientes procuram padaria no celular antes de sair. Sem site, perde clientes.", "checks": ["Cardápio com <strong>produtos e preços</strong>", "Destaque para <strong>promoções do dia</strong>", "Cliente pode <strong>encomendar online</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Cardápio Digital", "#d97706", "Produtos &bull; Preços &bull; Atualização"), ("Encomendas Online", "#f59e0b", "WhatsApp &bull; Formulário &bull; Entrega"), ("Gestão Instagram", "#ec4899", "Stories &bull; Produtos do dia &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "papelaria": {"color": "#8b5cf6", "stat": "65%", "stat_text": "procuram papelaria online", "hero_h1": "{nome}, quando o cliente precisa de material escolar em {cidade}, encontra sua papelaria?", "problem": "Sua papelaria em {cidade} tem de tudo, mas quando o cliente pesquisa — não encontra produtos, marcas, nem preços.", "stat_detail": "65% procuram papelaria online. Sem catálogo digital, perde vendas.", "checks": ["Catálogo de <strong>produtos e marcas</strong>", "Destaque para <strong;volta às aulas e promoções</strong>", "Cliente pede <strong>orçamento pelo site</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Catálogo Online", "#8b5cf6", "Produtos &bull; Marcas &bull; Fotos"), ("Orçamento", "#0ea5e9", "Lista escolar &bull; WhatsApp &bull; Resposta"), ("Gestão Instagram", "#ec4899", "Novidades &bull; Promoções &bull; Reports"), ("Site Simples", "#22c55e", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "pintor": {"color": "#ec4899", "stat": "73%", "stat_text": "veem portfólio do pintor antes de contratar", "hero_h1": "{nome}, quando precisam de pintor em {cidade}, encontram seus trabalhos?", "problem": "Você pinta muito bem, mas quando o cliente quer ver seus trabalhos — não encontra portfólio online.", "stat_detail": "73% veem portfólio do pintor antes de contratar. Sem portfólio, perde orçamentos.", "checks": ["Portfólio de <strong>trabalhos com fotos antes/depois</strong>", "Cliente solicita <strong>orçamento pelo site</strong>", "Depoimentos de <strong>clientes satisfeitos</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Portfólio Online", "#ec4899", "Fotos &bull; Antes/depois &bull; Projetos"), ("Orçamento", "#0ea5e9", "Formulário &bull; Fotos do local &bull; WhatsApp"), ("Gestão Instagram", "#22c55e", "Trabalhos &bull; Processo &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "pizzaria": {"color": "#ef4444", "stat": "80%", "stat_text": "pedem pizza online", "hero_h1": "{nome}, sua pizza é a melhor de {cidade}, mas o iFood fica com 20% de cada pedido?", "problem": "Sua pizzaria em {cidade} faz a melhor pizza, mas o iFood tira 20% de comissão em cada pedido. E o pior: o cliente é do app, não seu.", "stat_detail": "80% pedem pizza online. Num pedido de R$80, são R$16 que saem do seu bolso. Todo dia. Todo mês.", "checks": ["Cardápio digital com <strong>pedidos diretos</strong> — sem comissão", "Cliente pede pelo <strong>site ou WhatsApp</strong>", "Recebe <strong>pagamentos online</strong> via Mercado Pago", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Cardápio Online", "#ef4444", "Sabores &bull; Preços &bull; Fotos profissionais"), ("Pedidos pelo Site", "#22c55e", "Direto &bull; Sem comissão &bull; Entrega ou retirada"), ("Chatbot WhatsApp", "#0ea5e9", "Cardápio &bull; Pedidos &bull; Promoções"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "serralheria": {"color": "#6b7280", "stat": "70%", "stat_text": "procuram serralheiro online", "hero_h1": "{nome}, quando precisam de serviço de serralheria em {cidade}, encontram você?", "problem": "Seu trabalho em metal é excelente, mas quando o cliente pesquisa — não encontra portfólio de projetos anteriores.", "stat_detail": "70% procuram serralheiro online. Sem portfólio, perde orçamentos.", "checks": ["Portfólio de <strong>projetos com fotos</strong>", "Mostra <strong>materiais e tipos de serviço</strong>", "Cliente solicita <strong>orçamento pelo site</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Portfólio Online", "#6b7280", "Fotos &bull; Projetos &bull; Detalhes"), ("Orçamento", "#0ea5e9", "Formulário &bull; Medidas &bull; WhatsApp"), ("Gestão Instagram", "#ec4899", "Projetos &bull; Processo &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "supermercado": {"color": "#10b981", "stat": "80%", "stat_text": "pesquisam supermercado no celular", "hero_h1": "{nome}, quando o cliente vai fazer compras em {cidade}, encontra promoções do seu supermercado?", "problem": "Seu supermercado em {cidade} tem preços ótimos, mas quando o cliente pesquisa — não encontra ofertas, nem folheto da semana.", "stat_detail": "80% pesquisam supermercado no celular. Sem site com ofertas, perde clientes.", "checks": ["Encarte de <strong>ofertas da semana</strong>", "Cliente vê <strong>promções e preços</strong>", "Destaque para <strong>produtos em oferta</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Ofertas da Semana", "#f59e0b", "Encarte &bull; Preços &bull; Destaques"), ("Delivery Online", "#10b981", "Lista &bull; WhatsApp &bull; Entrega"), ("Chatbot WhatsApp", "#0ea5e9", "Preço &bull; Estoque &bull; 24h"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
    "vidracaria": {"color": "#0ea5e9", "stat": "71%", "stat_text": "procuram vidraçaria online", "hero_h1": "{nome}, quando precisam de vidros em {cidade}, encontram sua vidraçaria?", "problem": "Sua vidraçaria em {cidade} faz trabalhos bonitos, mas quando o cliente pesquisa — não encontra portfólio de projetos.", "stat_detail": "71% procuram vidraçaria online. Sem portfólio, perde orçamentos.", "checks": ["Portfólio de <strong>projetos com fotos</strong>", "Mostra <strong>tipos de vidro e serviços</strong>", "Cliente solicita <strong>orçamento pelo site</strong>", "Pronto em <strong>2–3 dias</strong> — você aprova antes de publicar"], "upsells": [("Portfólio Online", "#0ea5e9", "Fotos &bull; Projetos &bull; Detalhes"), ("Orçamento", "#22c55e", "Formulário &bull; Medidas &bull; WhatsApp"), ("Gestão Instagram", "#ec4899", "Projetos &bull; Processo &bull; Reports"), ("Site Simples", "#8b5cf6", "Página informativa &bull; WhatsApp integrado &bull; Formulário")]},
}

def generate_template(key, data):
    c = data["color"]
    checks_html = ""
    for i, check in enumerate(data["checks"]):
        border = "border-bottom:1px solid #eee;" if i < len(data["checks"]) - 1 else ""
        checks_html += f'''                    <tr>
                        <td style="padding:10px 0;{border}">
                            <span style="color:{c};font-weight:700;">&#10003;</span>
                            <span style="color:#333;font-size:14px;">&nbsp;{check}</span>
                        </td>
                    </tr>
'''
    upsells_html = ""
    for i, (name, color, desc) in enumerate(data["upsells"]):
        if i % 2 == 0:
            upsells_html += '                <tr>\n'
        pad_left = "padding:0 6px" if i % 2 == 0 else "padding:0 0"
        pad_bottom = "12px" if i < 2 else "0"
        upsells_html += f'''                    <td width="50%" style="{pad_left} {('6px' if i%2==0 else '0')} 0 {('6px' if i%2==1 else '0')};vertical-align:top;padding:0 {'6px' if i%2==0 else '0'} {pad_bottom} {'6px' if i%2==1 else '0'};vertical-align:top;">
                        <div style="background:#fff;border:1px solid #e8e8e8;border-radius:8px;padding:16px;">
                            <p style="margin:0 0 6px 0;font-size:14px;font-weight:600;color:{color};">
                                {name}
                            </p>
                            <p style="margin:0;color:#666;font-size:12px;line-height:1.5;">
                                {desc}
                            </p>
                        </div>
                    </td>
'''
        if i % 2 == 1:
            upsells_html += '                </tr>\n'

    # Friendly name for footer
    nomes = {"bar": "bar", "clinica_medica": "clínica médica", "clinica_veterinaria": "clínica veterinária",
             "confeitaria": "confeitaria", "curso_pre_vestibular": "cursinho", "eletricista": "eletricista",
             "encanador": "encanador", "escola_de_idiomas": "escola de idiomas", "estetica": "clínica estética",
             "estudio_de_pilates": "estúdio de pilates", "farmacia": "farmácia", "floricultura": "floricultura",
             "imobiliaria": "imobiliária", "joalheria": "joalheria", "lanchonete": "lanchonete",
             "lavanderia": "lavanderia", "loja_de_bicicleta": "loja", "loja_de_celulares": "loja",
             "loja_de_moveis": "loja", "loja_de_roupas": "loja", "marcenaria": "marcenaria",
             "material_de_construcao": "loja", "otica": "ótica", "padaria": "padaria", "papelaria": "papelaria",
             "pintor": "pintor", "pizzaria": "pizzaria", "serralheria": "serralheria",
             "supermercado": "supermercado", "vidracaria": "vidraçaria"}
    footer_name = nomes.get(key, key.replace("_", " "))

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Equipe Vanderson</title>
</head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#0d0d0d;-webkit-text-size-adjust:100%;">

<!-- WRAPPER -->
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:620px;margin:0 auto;">

    <!-- TOP BAR -->
    <tr>
        <td style="padding:16px 32px;background:#111;text-align:center;border-bottom:2px solid #333;">
            <p style="margin:0;font-size:11px;color:#666;letter-spacing:3px;text-transform:uppercase;">
                Equipe Vanderson &bull; Duque de Caxias, RJ
            </p>
        </td>
    </tr>

    <!-- HERO: BIG NUMBER -->
    <tr>
        <td style="padding:48px 32px 32px 32px;background:linear-gradient(165deg,#0d0d0d 0%,#1a1a1a 100%);text-align:center;">
            <p style="margin:0 0 12px 0;font-size:72px;font-weight:800;color:{c};line-height:1;letter-spacing:-3px;">
                {data["stat"]}
            </p>
            <p style="margin:0 0 24px 0;font-size:14px;color:#888;text-transform:uppercase;letter-spacing:2px;">
                {data["stat_text"]}
            </p>
            <h1 style="margin:0;font-size:22px;color:#fff;font-weight:700;line-height:1.4;">
                {data["hero_h1"]}
            </h1>
        </td>
    </tr>

    <!-- COLOR STRIPE -->
    <tr>
        <td style="height:4px;background:linear-gradient(90deg,{c},{'{{c}}','{{c}}'.replace('{'+'c}','{c}')).replace('{{c}}',lighter());"></td>
    </tr>

    <!-- BODY -->
    <tr>
        <td style="padding:40px 32px;background:#fafafa;">

            <!-- GREETING -->
            <p style="margin:0 0 24px 0;color:#111;font-size:15px;line-height:1.7;">
                Oi <strong style="color:{c};">{{nome}}</strong>, tudo bem?
            </p>

            <!-- PROBLEM BLOCK -->
            <div style="margin:0 0 32px 0;">
                <p style="margin:0 0 12px 0;color:#333;font-size:15px;line-height:1.7;">
                    {data["problem"]}
                </p>
                <div style="background:#f0f9ff;border-left:4px solid {c};padding:16px 20px;margin:20px 0;">
                    <p style="margin:0;color:#444;font-size:14px;line-height:1.6;">
                        {data["stat_detail"]}
                    </p>
                </div>
            </div>

            <!-- SOLUTION -->
            <div style="margin:0 0 32px 0;">
                <h2 style="margin:0 0 20px 0;font-size:18px;color:#111;font-weight:700;">
                    Uma P&aacute;gina Digital resolve isso:
                </h2>

                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
{checks_html}                </table>
            </div>

            <!-- RISK-FREE -->
            <div style="text-align:center;margin:24px 0 0 0;background:#dcfce7;border:1px dashed #22c55e;border-radius:8px;padding:16px 20px;">
                <p style="margin:0;color:#166534;font-size:14px;font-weight:600;">
                    &#128274; Sem risco: voc&ecirc; s&oacute; paga quando o site estiver no ar e funcionando.
                </p>
            </div>

            <!-- PRIMARY CTA -->
            <div style="text-align:center;margin:36px 0;">
                <a href="https://vandersonavellar.com" style="display:inline-block;background:{c};color:#fff;text-decoration:none;padding:16px 48px;border-radius:4px;font-weight:700;font-size:15px;letter-spacing:0.5px;">
                    VER EXEMPLOS DE SITES
                </a>
                <p style="margin:12px 0 0 0;color:#999;font-size:12px;">
                    ou simplesmente responda este email
                </p>
            </div>

            <!-- DIVIDER -->
            <div style="border-top:1px solid #e0e0e0;margin:36px 0;"></div>

            <!-- UPSILLS -->
            <div style="text-align:center;margin:0 0 24px 0;">
                <p style="margin:0 0 4px 0;color:#333;font-size:14px;font-weight:600;">
                    P&aacute;gina Digital n&atilde;o &eacute; o que precisa agora?
                </p>
                <p style="margin:0;color:#888;font-size:13px;">
                    Sem problemas. Temos outras op&ccedil;&otilde;es:
                </p>
            </div>

            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
{upsells_html}            </table>

            <div style="text-align:center;margin:24px 0 0 0;">
                <a href="https://wa.me/5521968410983?text=Oi!%20Vi%20o%20email%20da%20Equipe%20Vanderson%20e%20quero%20saber%20mais" style="display:inline-block;background:#333;color:#fff;text-decoration:none;padding:12px 28px;border-radius:4px;font-weight:500;font-size:13px;">
                    CONVERSAR NO WHATSAPP
                </a>
            </div>

        </td>
    </tr>

    <!-- SIGNATURE -->
    <tr>
        <td style="padding:32px;background:#111;text-align:center;">
            <p style="margin:0 0 4px 0;color:#fff;font-size:14px;font-weight:700;">
                Equipe Vanderson
            </p>
            <p style="margin:0 0 4px 0;color:#666;font-size:12px;">
                Desenvolvimento Web &bull; Duque de Caxias, RJ
            </p>
            <p style="margin:0 0 12px 0;color:#888;font-size:12px;">
                (21) 96841-0983 &bull; vandersonavellar.com
            </p>
            <p style="margin:0 0 4px 0;color:#555;font-size:11px;">
                CNPJ: 65.999.597/0001-75
            </p>
        </td>
    </tr>

    <!-- FOOTER -->
    <tr>
        <td style="padding:16px 32px;background:#0a0a0a;text-align:center;">
            <p style="margin:0;color:#444;font-size:10px;line-height:1.5;">
                Encontrei seu neg&oacute;cio no Google Maps e pareceu uma boa oportunidade de conversar.<br>
                Se preferir, responda este email ou chame no WhatsApp. Sem compromisso!
            </p>
        </td>
    </tr>

</table>

<img src="https://ivqaccppqcchqshaplao.supabase.co/functions/v1/track?id={{TRACKING_ID}}" width="1" height="1" style="display:none" alt=""></body>
</html>'''


for key, data in TEMPLATE_DATA.items():
    filepath = os.path.join(TEMPLATES_DIR, f"{key}.html")
    html = generate_template(key, data)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {key}.html")

print(f"\nTotal: {len(TEMPLATE_DATA)} templates criados")
