#!/usr/bin/env python3
import sqlite3
import sys

try:
    conn = sqlite3.connect('prospeccao.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Verificar se a tabela leads existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tabelas:', [t[0] for t in tables])

    # Verificar quantos leads existem
    cursor.execute('SELECT COUNT(*) FROM leads')
    count = cursor.fetchone()[0]
    print(f'Quantidade de leads: {count}')

    # Verificar métricas
    cursor.execute('SELECT * FROM metricas_acumuladas WHERE id=1')
    metricas = cursor.fetchone()
    if metricas:
        print(f'Métricas: total={metricas["total_abordados"]}, enviadas={metricas["mensagens_enviadas"]}, responderam={metricas["responderam"]}')
    else:
        print('Métricas: Nenhuma encontrada')

    # Verificar alguns leads com status diferente de novo
    cursor.execute("SELECT lead_id, nome, status FROM leads WHERE status != 'novo' LIMIT 10")
    leads = cursor.fetchall()
    if leads:
        print(f'Leads com status diferente de novo:')
        for lead in leads:
            print(f'  - {lead["nome"]}: {lead["status"]}')
    else:
        print('Nenhum lead com status diferente de "novo"')

    conn.close()
    print('\nBanco de dados verificado com sucesso!')
except Exception as e:
    print(f'Erro: {e}')
    sys.exit(1)
