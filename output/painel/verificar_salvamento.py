#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('prospeccao.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Verificar leads com status diferente de 'novo'
cursor.execute("SELECT lead_id, nome, status, data_abordagem FROM leads WHERE status != 'novo' ORDER BY atualizado_em DESC")
leads = cursor.fetchall()

if leads:
    print('Leads atualizados:')
    for lead in leads:
        print(f"  - {lead['nome']} ({lead['lead_id']})")
        print(f"    Status: {lead['status']}")
        print(f"    Data: {lead['data_abordagem']}")
        print()
else:
    print('NENHUM lead com status diferente de "novo"')
    print('O clique não foi salvo no banco de dados.')

# Ver métricas
cursor.execute('SELECT * FROM metricas_acumuladas WHERE id=1')
m = cursor.fetchone()
if m:
    print(f"\nMétricas: enviadas={m['mensagens_enviadas']}, responderam={m['responderam']}")

conn.close()
