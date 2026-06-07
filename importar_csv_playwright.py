#!/usr/bin/env python3
"""
Importar leads_sem_site.csv do Playwright para o Supabase.
Deduplicação estrita por telefone_normalizado.
Apenas INSERT - nunca sobrescreve leads existentes.
"""
import csv, os, re, sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

def normalizar_telefone(tel):
    """Remove tudo que não é dígito de telefone."""
    if not tel:
        return ""
    return re.sub(r'\D', '', tel.strip())

def main():
    # Carregar credenciais
    env_path = Path(r'C:\projetos\script-mapear-comércios\.env')
    load_dotenv(env_path)
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                os.environ.setdefault(k.strip(), v.strip())

    url = os.environ['SUPABASE_URL']
    key = os.environ['SUPABASE_ANON_KEY']
    sb = create_client(url, key)

    # Ler CSV
    csv_path = Path(r'C:\projetos\script-mapear-comércios\output\playwright\leads_sem_site.csv')
    with open(csv_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f'Total no CSV: {len(rows)}')

    # Filtrar só quem tem telefone/whatsapp
    uteis = []
    sem_tel = 0
    for r in rows:
        tel = r.get('telefone','').strip()
        wpp = r.get('whatsapp','').strip()
        if tel or wpp:
            uteis.append(r)
        else:
            sem_tel += 1

    print(f'Com telefone/WhatsApp: {len(uteis)}')
    print(f'Sem contato (ignorados): {sem_tel}')

    # Normalizar telefones e preparar batch
    leads_para_inserir = []
    for r in uteis:
        tel_raw = r.get('whatsapp','') or r.get('telefone','')
        tel_norm = normalizar_telefone(tel_raw)
        if not tel_norm:
            continue

        avalia = r.get('avaliacao','0').strip()
        try:
            nota = float(avalia.replace(',', '.')) if avalia else 0.0
        except:
            nota = 0.0

        qtd_av = r.get('num_avaliacoes','0').strip()
        try:
            qtd = int(re.sub(r'\D', '', qtd_av)) if qtd_av else 0
        except:
            qtd = 0

        leads_para_inserir.append({
            'nome': r.get('nome','').strip()[:200],
            'telefone': r.get('telefone','').strip()[:30],
            'whatsapp': r.get('whatsapp','').strip()[:30],
            'telefone_normalizado': tel_norm[:30],
            'instagram': r.get('instagram','').strip()[:200],
            'email': r.get('email','').strip()[:200],
            'categoria': r.get('categoria','').strip()[:100],
            'cidade': r.get('cidade','').strip()[:100],
            'bairro': r.get('bairro','').strip()[:100],
            'endereco': r.get('endereco','').strip()[:255],
            'tem_site': False,  # Já são leads sem site
            'url_site': '',
            'avaliacao': nota,
            'num_avaliacoes': qtd,
            'score': 0,
            'status': 'novo',
            'origem': 'baixada',
        })

    print(f'Leads preparados para verificar: {len(leads_para_inserir)}')

    # BUSCAR TODOS os telefones normalizados existentes no Supabase (com paginação)
    print('Buscando leads existentes no Supabase...')
    telefones_existentes = set()
    offset = 0
    batch_size = 500
    while True:
        batch = sb.table('leads').select('telefone_normalizado').range(offset, offset + batch_size - 1).execute()
        if not batch.data:
            break
        for r in batch.data:
            t = r.get('telefone_normalizado', '')
            if t:
                telefones_existentes.add(t)
        offset += batch_size
        if len(batch.data) < batch_size:
            break

    print(f'Telefones existentes no Supabase: {len(telefones_existentes)}')

    # Filtrar só os realmente novos
    realmente_novos = []
    duplicados = 0
    for lead in leads_para_inserir:
        if lead['telefone_normalizado'] in telefones_existentes:
            duplicados += 1
        else:
            realmente_novos.append(lead)
            telefones_existentes.add(lead['telefone_normalizado'])  # Evita duplicar dentro do próprio lote

    print(f'\n=== RESULTADO ===')
    print(f'Leads úteis (com telefone): {len(leads_para_inserir)}')
    print(f'Já existentes (duplicados): {duplicados}')
    print(f'Novos para importar: {len(realmente_novos)}')

    if not realmente_novos:
        print('Nada a importar!')
        return

    # Mostrar amostra
    print(f'\n--- Amostra dos 3 primeiros ---')
    for l in realmente_novos[:3]:
        print(f'  {l["nome"]} | {l["telefone_normalizado"]} | {l["cidade"]} | {l["categoria"]}')

    # BLOCO DE VERIFICAÇÃO: mostrar resumo antes de inserir e pedir confirmação
    print(f'\n{"="*50}')
    print(f'⚠️  CONFIRMAÇÃO NECESSÁRIA')
    print(f'{"="*50}')
    print(f'Serão inseridos {len(realmente_novos)} leads NOVOS no Supabase.')
    print(f'Não haverá duplicação (via telefone_normalizado).')
    print(f'Os {duplicados} duplicados serão ignorados.')
    print(f'{"="*50}')
    print()
    print('Para continuar, execute com --confirmar')
    print()

    # Se não tiver --confirmar, apenas mostrar
    if '--confirmar' not in sys.argv:
        print('Modo seco (dry-run). Execute com --confirmar para importar de fato.')
        return

    # --- IMPORTAR DE FATO ---
    importados = 0
    erros = 0
    batch_insert = 50

    for i in range(0, len(realmente_novos), batch_insert):
        lote = realmente_novos[i:i + batch_insert]
        try:
            result = sb.table('leads').insert(lote).execute()
            importados += len(result.data)
            print(f'  ✅ Lote {i//batch_insert + 1}: {len(result.data)} inseridos')
        except Exception as e:
            erros += len(lote)
            print(f'  ❌ Lote {i//batch_insert + 1} ERRO: {e}')

    print(f'\n=== IMPORTACAO CONCLUIDA ===')
    print(f'Inseridos: {importados}')
    print(f'Erros: {erros}')
    print(f'Duplicados ignorados: {duplicados}')

if __name__ == '__main__':
    main()