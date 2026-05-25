#!/usr/bin/env python3
"""
Script para sincronizar dados do localStorage com o SQLite.
Execute este script após copiar o conteúdo do localStorage do navegador.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "prospeccao.db"

def sync_from_localstorage(localstorage_data):
    """Sincroniza dados do localStorage com o SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    for lead_id, dados in localstorage_data.items():
        status = dados.get('status', 'novo')
        data_abordagem = dados.get('data_abordagem', '')
        data_followup = dados.get('data_followup', '')
        observacoes = dados.get('observacoes', '')

        # Verificar se o lead existe
        cursor = conn.execute("SELECT lead_id FROM leads WHERE lead_id = ?", (lead_id,))
        if cursor.fetchone():
            # Atualizar
            conn.execute("""
                UPDATE leads SET
                    status = ?,
                    data_abordagem = ?,
                    data_followup = ?,
                    observacoes = ?,
                    atualizado_em = datetime('now','localtime')
                WHERE lead_id = ?
            """, (status, data_abordagem, data_followup, observacoes, lead_id))
            print(f"Atualizado: {lead_id} -> {status}")
        else:
            print(f"Lead não encontrado no banco: {lead_id}")

    conn.commit()

    # Recalcular métricas
    from db import recalcular_metricas
    recalcular_metricas(conn)

    conn.close()
    print("\nSincronização concluída!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Ler de arquivo
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
        sync_from_localstorage(data)
    else:
        print("""
Uso: python sync_localstorage.py <arquivo.json>

Para usar:
1. No navegador, abra o console (F12)
2. Execute: copy(localStorage.getItem('prospeccao_status_v2'))
3. Cole o conteúdo em um arquivo JSON
4. Execute: python sync_localstorage.py dados.json
        """)
