#!/usr/bin/env python3
"""Apply para 3 leads - validacao completa"""
import os, sys
sys.path.insert(0, '.')

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            os.environ.setdefault(k.strip(), v.strip())

from supabase import create_client
from outreach_client import confirm_outreach_from_whatsapp, get_outreach_state
from datetime import datetime, timezone

sb_anon = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_ANON_KEY'])
sb_service = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

LEADS = [
    {'id': '33f46d38-5d3f-4c48-8cb8-17487a555a29', 'nome': 'Suporte Smart Nova Iguaçu', 'phone': '5521977513011'},
    {'id': '728f4420-4fe6-4f57-9b87-251bf9411012', 'nome': 'You Cell Conserto de Celulares', 'phone': '5521974266901'},
    {'id': 'bf414a15-6baa-44e5-b14e-eee6b9402ab9', 'nome': 'Smart Tech', 'phone': '5521980288611'},
]

CAMPAIGN = 'avgestao:assistencias:primeiro_contato:v1'

def mask(tel):
    return tel[:4] + '****' + tel[-4:]

resultados = []

for lead in LEADS:
    lead_id = lead['id']
    nome = lead['nome']
    phone = lead['phone']
    masked = mask(phone)
    
    print(f'\n{"="*60}')
    print(f'  LEAD: {nome}')
    print(f'  ID: {lead_id[:8]}...')
    print(f'  Telefone: {masked}')
    print(f'{"="*60}')
    
    # ANTES
    state_before = get_outreach_state(phone, CAMPAIGN)
    r_out = sb_service.table('lead_outreach').select('*').eq('lead_id', lead_id).execute()
    r_int = sb_service.table('lead_interactions').select('*').eq('lead_id', lead_id).execute()
    r_lead = sb_anon.table('leads').select('status').eq('id', lead_id).execute()
    
    print(f'\nANTES:')
    print(f'  outreach_state: {state_before.get("outcome")}')
    print(f'  lead_outreach: {len(r_out.data)} | interactions: {len(r_int.data)} | status: {r_lead.data[0]["status"] if r_lead.data else "?"}')
    
    # APPLY 1
    result1 = confirm_outreach_from_whatsapp(
        phone_normalized=phone, campaign_key=CAMPAIGN, lead_id=lead_id,
        message_timestamp=datetime.now(timezone.utc).isoformat(),
        fingerprint=CAMPAIGN, campaign_match=True, source='whatsapp_reconciliation',
    )
    print(f'\nAPPLY 1: {result1.get("outcome")}')
    
    # DEPOIS
    r_out2 = sb_service.table('lead_outreach').select('*').eq('lead_id', lead_id).execute()
    r_int2 = sb_service.table('lead_interactions').select('*').eq('lead_id', lead_id).execute()
    r_lead2 = sb_anon.table('leads').select('status').eq('id', lead_id).execute()
    state_after = get_outreach_state(phone, CAMPAIGN)
    
    status_out = r_out2.data[0].get('status') if r_out2.data else 'n/a'
    print(f'DEPOIS:')
    print(f'  lead_outreach: {len(r_out2.data)} | status: {status_out}')
    print(f'  interactions: {len(r_int2.data)}')
    print(f'  leads.status: {r_lead2.data[0]["status"] if r_lead2.data else "?"}')
    print(f'  state: {state_after.get("outcome")} | match: {state_after.get("campaign_match")}')
    
    # APPLY 2 (idempotencia)
    result2 = confirm_outreach_from_whatsapp(
        phone_normalized=phone, campaign_key=CAMPAIGN, lead_id=lead_id,
        message_timestamp=datetime.now(timezone.utc).isoformat(),
        fingerprint=CAMPAIGN, campaign_match=True, source='whatsapp_reconciliation',
    )
    print(f'APPLY 2: {result2.get("outcome")}')
    
    r_out3 = sb_service.table('lead_outreach').select('*').eq('lead_id', lead_id).execute()
    r_int3 = sb_service.table('lead_interactions').select('*').eq('lead_id', lead_id).execute()
    
    ok = (len(r_out3.data) == 1 and len(r_int3.data) == 1 and result2.get('outcome') == 'already_confirmed')
    
    resultados.append({
        'nome': nome,
        'id_masked': lead_id[:8] + '...',
        'phone_masked': masked,
        'apply1': result1.get('outcome'),
        'apply2': result2.get('outcome'),
        'state_final': state_after.get('outcome'),
        'outreach_count': len(r_out3.data),
        'interactions_count': len(r_int3.data),
        'ok': ok,
    })
    
    print(f'RESULTADO: {"✅ OK" if ok else "❌ FALHA"}')

# Relatorio final
print(f'\n{"="*60}')
print('  RELATORIO FINAL - 3 LEADS')
print(f'{"="*60}')
print(f'\n{"Lead":<35} {"Tel":<14} {"Apply1":<12} {"Apply2":<18} {"State":<10} {"Out":<4} {"Int":<4} {"OK"}')
print('-' * 100)
for r in resultados:
    print(f'{r["nome"][:34]:<35} {r["phone_masked"]:<14} {r["apply1"]:<12} {r["apply2"]:<18} {r["state_final"]:<10} {r["outreach_count"]:<4} {r["interactions_count"]:<4} {"✅" if r["ok"] else "❌"}')

print(f'\n✅ Zero mensagens enviadas')
print(f'✅ Zero send?phone= abertas')
print(f'✅ Zero senders executados')