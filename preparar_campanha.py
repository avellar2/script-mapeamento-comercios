#!/usr/bin/env python3
"""
Preparar campanha diária de prospecção.
Seleciona os melhores leads com status 'novo', gera mensagens curtas e humanas,
e salva lista pronta para envio manual via WhatsApp.

Nunca envia mensagens automaticamente. Nunca altera status no Supabase.
"""

import os, json, csv, argparse
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client
from urllib.parse import quote
from config.regioes import resolve_regiao, get_output_dir
from config.mensagens import gerar_mensagem_whatsapp


def gerar_link_wa(tel_norm, msg):
    if not tel_norm:
        return ''
    return f"https://wa.me/{tel_norm}?text={quote(msg)}"

def horario_recomendado(nicho):
    nicho_lower = (nicho or '').lower()
    manha_cedo = '09:00-10:00'
    manha = '09:30-11:00'
    antes_almoco = '10:30-11:30'
    
    if nicho_lower in ['barbearia', 'estética', 'salão de beleza', 'estúdio de pilates', 'academia', 'dentista']:
        return manha_cedo  # profissionais respondem bem cedo
    elif nicho_lower in ['pizzaria', 'restaurante', 'lanchonete', 'confeitaria', 'padaria']:
        return antes_almoco  # antes do rush
    elif nicho_lower in ['bar']:
        return '14:00-16:00'  # tarde, antes de abrir
    else:
        return manha

def main():
    parser = argparse.ArgumentParser(description='Preparar campanha diaria de prospeccao')
    parser.add_argument('--regiao', choices=['baixada', 'rio_premium', 'todas'], default=None,
                        help='Regiao de prospeccao (padrao: baixada)')
    args = parser.parse_args()

    regioes = resolve_regiao(args.regiao)

    load_dotenv(Path('.env'))
    sb = create_client(os.environ['SUPABASE_URL'], os.environ.get('SUPABASE_ANON_KEY') or os.environ.get('SUPABASE_KEY', ''))

    # Processar cada regiao separadamente
    for regiao in regioes:
        _processar_regiao(sb, regiao)


def _processar_regiao(sb, regiao):
    """Processa campanha para uma regiao especifica."""
    nicho_prio = regiao.nicho_prio
    cidades_prio = regiao.cidade_prio
    nicho_tipo = regiao.nicho_tipo

    # Buscar leads novo sem site, filtrando por regiao quando possivel
    query = sb.table('leads').select('*').eq('status', 'novo').is_('tem_site', 'false')
    query = query.eq('origem', regiao.key)
    result = query.order('score', desc=True).limit(500).execute()
    leads = result.data

    # Score composto
    for l in leads:
        nicho = (l.get('nicho') or '').lower()
        cidade = (l.get('cidade') or '').strip()
        base = l.get('score') or 0
        np = nicho_prio.get(nicho, 1)
        cp = cidades_prio.get(cidade, 0)
        l['_comp'] = base + np * 5 + cp * 3
        l['_tipo'] = nicho_tipo.get(nicho, 'presença')

    leads.sort(key=lambda x: x['_comp'], reverse=True)

    # Selecionar no máx 2 por nicho e 3 por cidade
    selecionados = []
    nichos_count = {}
    cidades_count = {}
    for l in leads:
        nicho = (l.get('nicho') or '').lower()
        cidade = (l.get('cidade') or '').strip()
        nc = nichos_count.get(nicho, 0)
        cc = cidades_count.get(cidade, 0)
        if nc >= 2:
            continue
        if cc >= 5:  # max 5 por cidade
            continue
        selecionados.append(l)
        nichos_count[nicho] = nc + 1
        cidades_count[cidade] = cc + 1
        if len(selecionados) >= 15:
            break

    # Gerar output
    hoje = datetime.now().strftime('%Y-%m-%d')
    # Se hoje é sexta, a campanha é segunda
    dia_semana = datetime.now().weekday()  # 0=seg, 5=sab, 6=dom
    if dia_semana >= 5:  # fim de semana
        data_campanha = (datetime.now() + __import__('datetime').timedelta(days=7-dia_semana)).strftime('%Y-%m-%d')
    else:
        # Se for segunda, usar hoje; se for outro dia, usar próxima segunda
        if dia_semana == 0:
            data_campanha = hoje
        else:
            data_campanha = (datetime.now() + __import__('datetime').timedelta(days=7-dia_semana)).strftime('%Y-%m-%d')

    out = []
    for i, l in enumerate(selecionados, 1):
        nome = l.get('nome', '')
        nicho = l.get('nicho', '')
        cidade = l.get('cidade', '')
        bairro = l.get('bairro', '') or ''
        tel = l.get('telefone_normalizado', '') or ''
        aval = l.get('avaliacao') or ''
        n_aval = l.get('num_avaliacoes') or 0
        score = l.get('score', 0)
        comp = l['_comp']
        tipo = l['_tipo']
        
        msg = gerar_mensagem_whatsapp(l, regiao)
        link = gerar_link_wa(tel, msg)
        hr = horario_recomendado(nicho)
        
        out.append({
            'pos': i, 'nome': nome, 'nicho': nicho, 'cidade': cidade, 'bairro': bairro,
            'telefone': tel, 'avaliacao': aval, 'num_avaliacoes': n_aval,
            'score': score, 'score_composto': comp,
            'tipo_pagina': tipo, 'mensagem': msg, 'link_wame': link,
            'horario_recomendado': hr,
        })

    # Salvar JSON
    out_dir = Path(__file__).parent / 'output' / 'painel'
    out_dir.mkdir(parents=True, exist_ok=True)

    regiao_key = regiao.key
    with open(out_dir / f'campanha_{regiao_key}_{data_campanha}.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Salvar TXT
    with open(out_dir / f'campanha_{regiao_key}_{data_campanha}.txt', 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write(f'📋 CAMPANHA DE PROSPECÇÃO — {regiao.label} — SEGUNDA-FEIRA {data_campanha}\n')
        f.write('=' * 80 + '\n')
        f.write(f'Região: {regiao.label}\n')
        f.write(f'Total de leads: {len(selecionados)}\n')
        f.write(f'Status: NOVO (nenhum status alterado)\n')
        f.write(f'Regra: enviar entre 09:00 e 11:00\n\n')
        
        nichos_sel = sorted(set(o['nicho'] for o in out))
        cidades_sel = sorted(set(o['cidade'] for o in out))
        f.write(f'Nichos: {", ".join(nichos_sel)}\n')
        f.write(f'Cidades: {", ".join(cidades_sel)}\n\n')
        
        for o in out:
            f.write(f'{"─" * 80}\n')
            f.write(f'{o["pos"]:2}. {o["nome"]}\n')
            f.write(f'    Nicho: {o["nicho"]} | Cidade: {o["cidade"]}')
            if o['bairro']:
                f.write(f' | Bairro: {o["bairro"]}')
            f.write('\n')
            f.write(f'    Telefone: {o["telefone"]}\n')
            ava = f'{o["avaliacao"]}★ ({o["num_avaliacoes"]} avaliações)' if o['avaliacao'] else '—'
            f.write(f'    Avaliação: {ava} | Score: {o["score"]} | Composto: {o["score_composto"]}\n')
            f.write(f'    Tipo de página: {o["tipo_pagina"]}\n')
            f.write(f'    Horário recomendado: {o["horario_recomendado"]}\n')
            f.write(f'\n    📱 Mensagem:\n    {o["mensagem"]}\n\n')
            f.write(f'    🔗 Link wa.me:\n    {o["link_wame"]}\n\n')

    print(f'✅ Campanha salva: campanha_{regiao_key}_{data_campanha}.json e .txt')
    print(f'📊 {len(selecionados)} leads selecionados ({regiao.label})')
    print(f'Nichos: {", ".join(nichos_sel)}')
    print(f'Cidades: {", ".join(cidades_sel)}')
    print()
    for o in out:
        print(f'{o["pos"]:2}. {o["nome"][:45]:45} | {o["nicho"]:20} | {o["cidade"]:20} | {o["horario_recomendado"]}')

if __name__ == '__main__':
    main()