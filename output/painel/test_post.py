#!/usr/bin/env python3
import requests
import json

# Testar a API POST
try:
    print('Testando POST /api/status-single...')
    payload = {
        'lead_id': 'flora-est-tica-mesquita',
        'status': 'mensagem enviada',
        'data_abordagem': '21/05/2026',
        'data_followup': '',
        'observacoes': 'Teste de envio'
    }
    response = requests.post(
        'http://localhost:8000/api/status-single',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    print(f'Status: {response.status_code}')
    print(f'Resposta: {response.text}')

    # Verificar se salvou
    print('\nVerificando se salvou...')
    check = requests.get('http://localhost:8000/api/leads')
    data = check.json()
    lead = next((l for l in data['leads'] if l['lead_id'] == 'flora-est-tica-mesquita'), None)
    if lead:
        print(f'Status do lead: {lead["status"]}')
    else:
        print('Lead não encontrado')

except Exception as e:
    print(f'Erro: {e}')
