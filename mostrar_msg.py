#!/usr/bin/env python3
"""Mostrar exemplos reais das mensagens por nicho"""
import os, json, urllib.request, ssl
from pathlib import Path

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

DORES = {
    "oficina_mecanica": "serviços autorizados, peças usadas, valores e entrega do veículo",
    "assistencia_tecnica": "aparelhos, diagnóstico, peças e andamento do serviço",
    "oficina_producao": "medidas, alterações, orçamento e retrabalho",
    "prestador_servico": "quem aprovou, serviço pendente e pagamento em aberto",
    "ar_refrigeracao": "chamados, equipamentos, histórico e garantia",
    "seguranca": "serviços, orçamentos e histórico de atendimentos",
}

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

def followup1(nome, dor):
    return (
        f"Boa tarde, pessoal da {nome}! Tudo bem?\n\n"
        f"Passando para saber se conseguiram ver minha mensagem sobre o AVGESTÃO.\n\n"
        f"O sistema reúne clientes, orçamentos, ordens de serviço, andamento dos atendimentos, valores e histórico em um só lugar.\n\n"
        f"Além disso, o cliente pode receber um link para visualizar e aprovar o orçamento e acompanhar o serviço sem precisar perguntar toda hora pelo WhatsApp.\n\n"
        f"O acesso fica liberado gratuitamente por 15 dias, para vocês testarem com atendimentos reais e decidirem somente depois.\n\n"
        f"Posso criar o login de teste para vocês?"
    )

def followup2(nome, dor):
    return (
        f"Boa tarde, pessoal da {nome}!\n\n"
        f"Esse será meu último contato para não incomodar.\n\n"
        f"Acredito que o AVGESTÃO pode ajudar vocês a economizar tempo e evitar informações perdidas entre conversas, papel e planilhas.\n\n"
        f"No sistema ficam organizados o cadastro do cliente, orçamento, aprovação, ordem de serviço, andamento, valores e histórico de cada atendimento.\n\n"
        f"O teste é gratuito por 15 dias, sem compromisso, e vocês podem conhecer o sistema por dentro usando na própria rotina.\n\n"
        f"Quer que eu deixe um acesso preparado para vocês?"
    )

# Exemplos reais
exemplos = [
    ("oficina_mecanica", "Oficina do Mineiro"),
    ("assistencia_tecnica", "Mundo Eletro Cell Santa Marta Loja 2"),
    ("oficina_producao", "GJS Serralheria"),
    ("prestador_servico", "WCA ELÉTRICA ELETRICISTA PADRÃO LIGHT RJ"),
    ("ar_refrigeracao", "K&L refrigeração e climatização"),
    ("seguranca", "MEDSERVE Medicina e Segurança do Trabalho"),
]

for cat, nome in exemplos:
    dor = DORES.get(cat, "serviços e orçamentos")
    msg1 = ABORDAGEM.get(cat, ABORDAGEM["seguranca"])(nome)
    msg_fup1 = followup1(nome, dor)
    msg_fup2 = followup2(nome, dor)

    print("=" * 80)
    print(f"  🏷️ {cat.upper()}")
    print(f"  🏪 {nome}")
    print("=" * 80)
    print()
    print("📅 DIA 1 — ABORDAGEM INICIAL:")
    print(msg1)
    print()
    print("📅 DIA 3 — FOLLOW-UP 1:")
    print(msg_fup1)
    print()
    print("📅 DIA 7 — FOLLOW-UP 2 (ÚLTIMO):")
    print(msg_fup2)
    print()
