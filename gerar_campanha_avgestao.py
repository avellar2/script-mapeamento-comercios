#!/usr/bin/env python3
"""Gera HTML da campanha AVGESTÃO com 30 leads - só abordagem inicial"""
import os, json, urllib.request, ssl, random
from pathlib import Path
from urllib.parse import quote
from collections import Counter

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
api_url = f"{url}/rest/v1/leads"
ctx = ssl.create_default_context()
headers = {"apikey": key, "Authorization": f"Bearer {key}"}

nichos_alvo = ["oficina mecânica", "serralheria", "eletricista", "pintor", "marcenaria", "encanador"]
leads_por_nicho = {}

for nicho in nichos_alvo:
    all_data = []
    offset = 0
    page_size = 1000
    while True:
        nicho_encoded = quote(nicho)
        req = urllib.request.Request(
            f"{api_url}?nicho=ilike.*{nicho_encoded}*&status=in.(novo,pronto_para_enviar)&select=nome,telefone,telefone_normalizado,cidade,bairro,nicho,status&limit={page_size}&offset={offset}",
            headers=headers
        )
        with urllib.request.urlopen(req, context=ctx) as r:
            data = json.loads(r.read().decode())
            if not data:
                break
            all_data.extend(data)
            if len(data) < page_size:
                break
            offset += page_size
    leads_por_nicho[nicho] = all_data

random.seed(42)
selecionados = []
for nicho in nichos_alvo:
    leads = leads_por_nicho[nicho]
    random.shuffle(leads)
    selecionados.extend(leads[:5])

CAT_MAP = {
    "oficina mecânica": "oficina_mecanica",
    "serralheria": "oficina_producao",
    "marcenaria": "oficina_producao",
    "eletricista": "prestador_servico",
    "pintor": "prestador_servico",
    "encanador": "prestador_servico",
}

def msg_abordagem(cat, nome):
    if cat == "oficina_mecanica":
        return (
            f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
            f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços, veículos e orçamentos.\n\n"
            f"Um dos maiores problemas de uma oficina é perder o controle de qual serviço foi autorizado, o que já foi feito e quanto o cliente ainda precisa pagar. Isso pode causar atraso, retrabalho e até discussão na hora da entrega.\n\n"
            f"No AVGESTÃO vocês conseguem abrir a ordem de serviço, registrar tudo que será feito, enviar o orçamento para aprovação do cliente e acompanhar cada etapa do veículo.\n\n"
            f"Estou liberando 15 dias gratuitos para teste.\n\n"
            f"Posso criar um acesso para vocês entrarem no sistema e testarem na própria oficina?"
        )
    elif cat == "oficina_producao":
        return (
            f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
            f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas que trabalham com serviços personalizados e orçamentos.\n\n"
            f"Um dos maiores riscos desse segmento é uma medida, alteração ou observação importante ficar perdida entre várias conversas no WhatsApp. Um detalhe esquecido pode gerar orçamento errado, retrabalho e prejuízo no material.\n\n"
            f"No AVGESTÃO vocês conseguem registrar o cliente, organizar as informações do serviço, montar o orçamento e enviar um link para o cliente aprovar antes da produção.\n\n"
            f"O sistema está disponível para teste gratuito durante 15 dias.\n\n"
            f"Posso criar um acesso para vocês entrarem e testarem no próprio negócio?"
        )
    else:
        return (
            f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
            f"Meu nome é Vanderson e desenvolvi o AVGESTÃO para empresas e profissionais que trabalham com atendimentos e serviços externos.\n\n"
            f"Um dos maiores problemas nessa rotina é perder o controle de quem pediu orçamento, quem aprovou, qual serviço ainda está pendente e qual cliente ainda não pagou.\n\n"
            f"No AVGESTÃO vocês conseguem organizar os clientes, criar orçamentos, abrir ordens de serviço e acompanhar os valores recebidos e pendentes em um só lugar.\n\n"
            f"Estou liberando 15 dias gratuitos para teste.\n\n"
            f"Posso criar um login para vocês entrarem no sistema e testarem com os próprios serviços?"
        )

html_parts = []
html_parts.append('''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Campanha AVGESTÃO - 30 Leads</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #111; color: #e0e0e0; margin: 0; padding: 20px; }
  h1 { color: #f59e0b; text-align: center; margin-bottom: 5px; }
  .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
  .lead { background: #1a1a2e; border: 1px solid #333; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
  .lead h2 { margin: 0 0 5px 0; color: #fff; font-size: 18px; }
  .lead .info { color: #aaa; font-size: 13px; margin-bottom: 12px; }
  .lead .info span { margin-right: 15px; }
  .msg { background: #0d0d1a; border-left: 3px solid #f59e0b; padding: 12px; border-radius: 6px; white-space: pre-wrap; font-size: 13px; line-height: 1.5; color: #ccc; margin-bottom: 10px; }
  .msg-label { font-size: 12px; color: #f59e0b; font-weight: bold; margin-bottom: 4px; }
  .link { display: inline-block; background: #25D366; color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: bold; margin-top: 8px; }
  .link:hover { background: #1da851; }
  .nicho-tag { display: inline-block; background: #333; color: #f59e0b; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
</style>
</head>
<body>
<h1>🚗 Campanha AVGESTÃO</h1>
<p class="subtitle">30 leads variados - Baixada Fluminense - 15 dias grátis</p>
''')

for i, l in enumerate(selecionados, 1):
    nome = l["nome"]
    nicho = l.get("nicho", "")
    cidade = l.get("cidade", "")
    bairro = l.get("bairro", "")
    tel = l.get("telefone_normalizado") or l.get("telefone") or ""
    cat = CAT_MAP.get(nicho, "prestador_servico")
    msg1 = msg_abordagem(cat, nome)
    link = f"whatsapp://send?phone={tel}&text={quote(msg1)}"

    html_parts.append(f'''
<div class="lead">
  <h2>{i}. {nome}</h2>
  <div class="info">
    <span>📍 {cidade} - {bairro}</span>
    <span>📞 {tel}</span>
    <span class="nicho-tag">{nicho}</span>
  </div>
  <div class="msg-label">📅 DIA 1 — Abordagem Inicial</div>
  <div class="msg">{msg1}</div>
  <a class="link" href="{link}" target="_blank">📤 Enviar WhatsApp</a>
</div>''')

html_parts.append('''
</body>
</html>''')

html = "\n".join(html_parts)

output_path = Path(__file__).parent / "campanha_avgestao_30.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ HTML salvo: {output_path}")
print(f"Total leads: {len(selecionados)}")

nicho_count = Counter(l.get("nicho", "") for l in selecionados)
print(f"\nDistribuição:")
for n, c in sorted(nicho_count.items()):
    print(f"  {n}: {c}")
