#!/usr/bin/env python3
import requests
import json

# Testar a API
try:
    print('Testando API...')
    response = requests.get('http://localhost:8000/api/leads')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Total de leads na API: {len(data.get("leads", []))}')
        print(f'Métricas: {data.get("metricas", {})}')
        # Verificar se algum lead tem status diferente de novo
        leads_nao_novos = [l for l in data.get('leads', []) if l.get('status') != 'novo']
        print(f'Leads com status != novo: {len(leads_nao_novos)}')
        if leads_nao_novos:
            print(f'Exemplo: {leads_nao_novos[0]["nome"]} - {leads_nao_novos[0]["status"]}')
    else:
        print(f'Erro: {response.text}')
except Exception as e:
    print(f'Erro ao conectar: {e}')
    print('O servidor pode não estar rodando')
