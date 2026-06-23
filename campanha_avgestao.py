#!/usr/bin/env python3
"""
Campanha AVGESTÃO — Roteiro completo com follow-ups
Mensagens: Vanderson
"""
import os, json, urllib.request, ssl
from pathlib import Path
from collections import defaultdict
from urllib.parse import quote

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
api_url = f"{url}/rest/v1/leads"
ctx = ssl.create_default_context()
headers = {"apikey": key, "Authorization": f"Bearer {key}"}

# ============================================================
# MENSAGENS DO VANDERSON
# ============================================================

# --- DOR POR NICHO (para follow-ups) ---
DORES = {
    "oficina_mecanica": "serviços autorizados, peças usadas, valores e entrega do veículo",
    "assistencia_tecnica": "aparelhos, diagnóstico, peças e andamento do serviço",
    "oficina_producao": "medidas, alterações, orçamento e retrabalho",
    "prestador_servico": "quem aprovou, serviço pendente e pagamento em aberto",
    "ar_refrigeracao": "chamados, equipamentos, histórico e garantia",
    "seguranca": "serviços, orçamentos e histórico de atendimentos",
}

# --- ABORDAGEM INICIAL (Dia 1) ---
ABORDAGEM = {
    "oficina_mecanica": lambda nome: (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços, veículos e orçamentos.\n\n"
        f"Um dos maiores problemas de uma oficina é perder o controle de qual serviço foi autorizado, o que já foi feito e quanto o cliente ainda precisa pagar. Isso pode causar atraso, retrabalho e até discussão na hora da entrega.\n\n"
        f"No AVGESTÃO vocês conseguem abrir a ordem de serviço, registrar tudo que será feito, enviar o orçamento para aprovação do cliente e acompanhar cada etapa do veículo.\n\n"
        f"Estou liberando 15 dias gratuitos para teste.\n\n"
        f"Posso criar um acesso para vocês entrarem no sistema e testarem na própria oficina?"
    ),
    "assistencia_tecnica": lambda nome: (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para ajudar assistências técnicas a controlar os aparelhos recebidos e o andamento dos serviços.\n\n"
        f"Uma das situações mais complicadas desse ramo é o cliente deixar um aparelho e depois ninguém encontrar rapidamente o diagnóstico, o orçamento, as peças utilizadas ou em qual etapa o serviço está. Além da perda de tempo, isso pode prejudicar a confiança do cliente.\n\n"
        f"No AVGESTÃO vocês conseguem abrir a ordem de serviço, registrar o aparelho, montar o orçamento e enviar um link para o cliente acompanhar e aprovar.\n\n"
        f"Estou oferecendo 15 dias gratuitos para teste.\n\n"
        f"Posso liberar um login para vocês entrarem e testarem com um atendimento real?"
    ),
    "oficina_producao": lambda nome: (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços personalizados e orçamentos.\n\n"
        f"Um dos maiores riscos desse segmento é uma medida, alteração ou observação importante ficar perdida entre várias conversas no WhatsApp. Um detalhe esquecido pode gerar orçamento errado, retrabalho e prejuízo no material.\n\n"
        f"No AVGESTÃO vocês conseguem registrar o cliente, organizar as informações do serviço, montar o orçamento e enviar um link para o cliente aprovar antes da produção.\n\n"
        f"O sistema está disponível para teste gratuito durante 15 dias.\n\n"
        f"Posso criar um acesso para vocês entrarem e testarem no próprio negócio?"
    ),
    "prestador_servico": lambda nome: (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas e profissionais que trabalham com atendimentos e serviços externos.\n\n"
        f"Um dos maiores problemas nessa rotina é perder o controle de quem pediu orçamento, quem aprovou, qual serviço ainda está pendente e qual cliente ainda não pagou.\n\n"
        f"No AVGESTÃO vocês conseguem organizar os clientes, criar orçamentos, abrir ordens de serviço e acompanhar os valores recebidos e pendentes em um só lugar.\n\n"
        f"Estou liberando 15 dias gratuitos para teste.\n\n"
        f"Posso criar um login para vocês entrarem no sistema e testarem com os próprios serviços?"
    ),
    "ar_refrigeracao": lambda nome: (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas de manutenção, refrigeração e climatização.\n\n"
        f"Uma das maiores dificuldades desse ramo é controlar vários chamados ao mesmo tempo e depois não encontrar rapidamente o histórico do equipamento, o orçamento aprovado, o que foi trocado ou se o serviço ainda está na garantia.\n\n"
        f"No AVGESTÃO vocês conseguem registrar o cliente e o equipamento, abrir a ordem de serviço, enviar o orçamento para aprovação e manter todo o histórico do atendimento organizado.\n\n"
        f"Estou oferecendo 15 dias gratuitos para teste.\n\n"
        f"Posso liberar um acesso para vocês entrarem e usarem o sistema em um atendimento real?"
    ),
    "seguranca": lambda nome: (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços e orçamentos.\n\n"
        f"Quando entram vários orçamentos e serviços ao mesmo tempo, controlar tudo pelo WhatsApp ou caderno pode gerar confusão e retrabalho.\n\n"
        f"No AVGESTÃO vocês conseguem registrar o cliente, abrir a ordem de serviço, enviar orçamento para aprovação e acompanhar cada etapa.\n\n"
        f"Estou liberando 15 dias gratuitos para teste.\n\n"
        f"Posso criar um acesso para vocês entrarem no sistema e testarem?"
    ),
}

# --- FOLLOW-UP 1 (Dia 3) ---
def followup1(nome, dor):
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Passando para saber se conseguiram ver minha mensagem sobre o AVGESTÃO.\n\n"
        f"O sistema reúne clientes, orçamentos, ordens de serviço, andamento dos atendimentos, valores e histórico em um só lugar.\n\n"
        f"Além disso, o cliente pode receber um link para visualizar e aprovar o orçamento e acompanhar o serviço sem precisar perguntar toda hora pelo WhatsApp.\n\n"
        f"O acesso fica liberado gratuitamente por 15 dias, para vocês testarem com atendimentos reais e decidirem somente depois.\n\n"
        f"Posso criar o login de teste para vocês?"
    )

# --- FOLLOW-UP 2 (Dia 7) ---
def followup2(nome, dor):
    return (
        f"Boa tarde, pessoal da {nome}!\n\n"
        f"Esse será meu último contato para não incomodar.\n\n"
        f"Acredito que o AVGESTÃO pode ajudar vocês a economizar tempo e evitar informações perdidas entre conversas, papel e planilhas.\n\n"
        f"No sistema ficam organizados o cadastro do cliente, orçamento, aprovação, ordem de serviço, andamento, valores e histórico de cada atendimento.\n\n"
        f"O teste é gratuito por 15 dias, sem compromisso, e vocês podem conhecer o sistema por dentro usando na própria rotina.\n\n"
        f"Quer que eu deixe um acesso preparado para vocês?"
    )

# ============================================================
# CLASSIFICAÇÃO
# ============================================================
CATEGORIAS = {
    "oficina_mecanica": ["oficina", "mecânica", "mecanica", "auto elétrica", "autoeletrica", "autoelétrica", "borracharia", "funilaria", "lanternagem", "pintura automotiva", "guincho", "reboque", "carroceria"],
    "assistencia_tecnica": ["assistência técnica", "assistencia tecnica", "assistência", "informática", "informatica", "celular", "smartphone", "tablet", "notebook", "computador", "pc", "manutenção", "manutencao"],
    "prestador_servico": ["eletricista", "encanador", "bombeiro", "pintor", "reforma", "construção", "construcao", "dedetização", "dedetizacao", "chaveiro", "jardinagem", "piscina", "piscineiro", "instalação", "instalacao", "montagem", "montador", "limpeza", "lavanderia", "higienização", "higienizacao"],
    "oficina_producao": ["serralheria", "marcenaria", "vidraçaria", "vidracaria", "marceneiro", "serralheiro", "gráfica", "grafica", "estofaria", "tapecaria", "corte a laser", "corte laser", "impressão", "impressao", "banner", "adesivo", "comunicação visual", "comunicacao visual", "persiana", "cortina", "colchão", "colchao", "solda"],
    "ar_refrigeracao": ["ar condicionado", "refrigeração", "refrigeracao"],
    "seguranca": ["segurança", "seguranca", "cftv", "alarme", "camera"],
}

def classificar(nicho, nome, categoria):
    texto = f"{nicho} {categoria} {nome}".lower()
    for cat, alvos in CATEGORIAS.items():
        for alvo in alvos:
            if alvo in texto:
                return cat
    return "outro"

# ============================================================
# BUSCAR LEADS
# ============================================================
todos_leads = []
page = 0
while True:
    r_start = page * 1000
    req = urllib.request.Request(
        f"{api_url}?origem=eq.baixada&status=eq.novo&select=id,nome,nicho,categoria,cidade,bairro,telefone_normalizado,telefone,instagram,score,avaliacao,num_avaliacoes&limit=1000&offset={r_start}",
        headers=headers
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        data = json.loads(resp.read())
        if not data: break
        todos_leads.extend(data)
        page += 1
        if len(data) < 1000: break

por_categoria = defaultdict(list)
for l in todos_leads:
    nicho = (l.get("nicho") or "").lower()
    categoria = (l.get("categoria") or "").lower()
    nome = (l.get("nome") or "").lower()
    tel = l.get("telefone_normalizado") or l.get("telefone") or ""
    if not tel: continue
    cat = classificar(nicho, nome, categoria)
    if cat == "outro": continue
    score = (l.get("score") or 0) + (l.get("avaliacao") or 0) * 10
    por_categoria[cat].append({**l, "_cat": cat, "_score_total": score})

cotas = {"oficina_mecanica": 5, "assistencia_tecnica": 5, "oficina_producao": 8, "prestador_servico": 4, "ar_refrigeracao": 4, "seguranca": 2, "prestador_geral": 2}
selecionados = []
for cat, qtd in cotas.items():
    leads_cat = sorted(por_categoria.get(cat, []), key=lambda l: -l["_score_total"])
    selecionados.extend(leads_cat[:qtd])

if len(selecionados) < 30:
    restantes = []
    usados = {l["id"] for l in selecionados}
    for cat in por_categoria:
        for l in por_categoria[cat]:
            if l["id"] not in usados:
                restantes.append(l)
    restantes.sort(key=lambda l: -l["_score_total"])
    selecionados.extend(restantes[:30 - len(selecionados)])

selecionados = selecionados[:30]

# ============================================================
# GERAR ROTEIRO COMPLETO
# ============================================================
print("=" * 80)
print("  🚀 CAMPANHA AVGESTÃO — ROTEIRO COMPLETO")
print("  Vanderson — Abordagem + Follow-ups")
print("=" * 80)
print()
print("📅 CRONOGRAMA:")
print("  Dia 1 → Abordagem inicial")
print("  Dia 3 → Primeiro follow-up")
print("  Dia 7 → Segundo e último follow-up")
print("  Depois → Encerrar (marcar como 'sem retorno')")
print()
print("📋 INSTRUÇÕES:")
print("  1. Abrir WhatsApp Business (perfil salvo)")
print("  2. Para cada lead, clicar no link")
print("  3. Copiar e colar a mensagem")
print("  4. Enviar")
print("  5. Marcar como 'abordado' no Supabase")
print("  6. Agendar follow-up conforme cronograma")
print()

for i, l in enumerate(selecionados, 1):
    cat = l["_cat"]
    cidade = (l.get("cidade") or "").strip()
    bairro = (l.get("bairro") or "").strip()
    tel = l.get("telefone_normalizado") or l.get("telefone") or ""
    aval = l.get("avaliacao") or 0
    dor = DORES.get(cat, "serviços e orçamentos")
    
    msg1 = ABORDAGEM.get(cat, ABORDAGEM["seguranca"])(l["nome"])
    msg_fup1 = followup1(l["nome"], dor)
    msg_fup2 = followup2(l["nome"], dor)
    
    link1 = f"https://web.whatsapp.com/send?phone={tel}&text={quote(msg1)}"
    link_fup1 = f"https://web.whatsapp.com/send?phone={tel}&text={quote(msg_fup1)}"
    link_fup2 = f"https://web.whatsapp.com/send?phone={tel}&text={quote(msg_fup2)}"
    
    print("─" * 80)
    print(f"  #{i} — {l['nome']}")
    print(f"  📍 {cidade} | {bairro}")
    print(f"  📞 {tel}")
    print(f"  🏷️ {cat}  ★{aval}")
    print()
    
    print(f"  📅 DIA 1 — ABORDAGEM INICIAL:")
    for linha in msg1.split("\n"):
        print(f"    {linha}")
    print(f"    🔗 {link1}")
    print()
    
    print(f"  📅 DIA 3 — FOLLOW-UP 1:")
    for linha in msg_fup1.split("\n"):
        print(f"    {linha}")
    print(f"    🔗 {link_fup1}")
    print()
    
    print(f"  📅 DIA 7 — FOLLOW-UP 2 (ÚLTIMO):")
    for linha in msg_fup2.split("\n"):
        print(f"    {linha}")
    print(f"    🔗 {link_fup2}")
    print()
    
    print(f"  ⏹️  APÓS DIA 7: Marcar como 'sem retorno' no Supabase")
    print()

print("=" * 80)
print("  📊 RESUMO")
print("=" * 80)
print(f"  Total: 30 leads")
print(f"  🔧 Oficinas: {sum(1 for l in selecionados if l['_cat']=='oficina_mecanica')}")
print(f"  📱 Assistência Técnica: {sum(1 for l in selecionados if l['_cat']=='assistencia_tecnica')}")
print(f"  🪚 Serralheria/Marcenaria/Vidraçaria: {sum(1 for l in selecionados if l['_cat']=='oficina_producao')}")
print(f"  ⚡ Prestadores: {sum(1 for l in selecionados if l['_cat']=='prestador_servico')}")
print(f"  ❄️ Ar Condicionado: {sum(1 for l in selecionados if l['_cat']=='ar_refrigeracao')}")
print(f"  🛡️ Segurança: {sum(1 for l in selecionados if l['_cat']=='seguranca')}")
print()
print(f"  ⏰ Horário: 9h-11h ou 14h-16h")
print(f"  🆓 15 dias grátis")
print(f"  💰 R$49/mês")
print()
print("  📅 CRONOGRAMA DE ENVIOS:")
print("  Lote 1 (Dia 1): 30 abordagens iniciais")
print("  Lote 2 (Dia 3): follow-up 1 para quem não respondeu")
print("  Lote 3 (Dia 7): follow-up 2 para quem não respondeu")
print("  Após Dia 7: marcar como 'sem retorno' e encerrar")
print("=" * 80)
