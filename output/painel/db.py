#!/usr/bin/env python3
"""Módulo de banco de dados SQLite para o Painel de Prospecção."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "prospeccao.db"

# Status canônicos do CRM
STATUS_VALIDOS = [
    "novo",
    "pronto_para_enviar",
    "abordado",
    "respondeu",
    "follow_up",
    "interessado",
    "convertido",
    "perdido",
]

# Mapeamento de status antigos para novos
STATUS_MAP = {
    "abordar hoje": "pronto_para_enviar",
    "pronto para enviar": "pronto_para_enviar",
    "mensagem enviada": "abordado",
    "video enviado": "abordado",
    "proposta enviada": "interessado",
    "fechado": "convertido",
    "follow-up": "follow_up",
    "nao abordar": "perdido",
    "nao_abordar": "perdido",
    "não abordar": "perdido",
}

# Novas colunas para adicionar à tabela leads
NOVAS_COLUNAS = {
    "bairro": "TEXT DEFAULT ''",
    "tem_site": "TEXT DEFAULT ''",
    "url_site": "TEXT DEFAULT ''",
    "nota_google": "REAL DEFAULT 0.0",
    "qtd_avaliacoes": "INTEGER DEFAULT 0",
    "oferta_sugerida": "TEXT DEFAULT ''",
    "motivo_prioridade": "TEXT DEFAULT ''",
    "acao_recomendada": "TEXT DEFAULT ''",
    "tipo_de_material": "TEXT DEFAULT ''",
    "email": "TEXT DEFAULT ''",
    "endereco": "TEXT DEFAULT ''",
    "link_maps": "TEXT DEFAULT ''",
    "instagram": "TEXT DEFAULT ''",
    "followup_mensagem": "TEXT DEFAULT ''",
    "numero_formatado": "TEXT DEFAULT ''",
    "categoria": "TEXT DEFAULT ''",
    "proximo_followup": "TEXT DEFAULT ''",
    "resposta_cliente": "TEXT DEFAULT ''",
    "origem": "TEXT DEFAULT ''",
}


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Cria as tabelas se não existirem e executa migração."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            lead_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'novo',
            data_abordagem TEXT DEFAULT '',
            data_followup TEXT DEFAULT '',
            observacoes TEXT DEFAULT '',
            nicho TEXT DEFAULT '',
            cidade TEXT DEFAULT '',
            telefone TEXT DEFAULT '',
            whatsapp TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            prioridade TEXT DEFAULT '',
            mensagem_whatsapp TEXT DEFAULT '',
            link_whatsapp TEXT DEFAULT '',
            rodada INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS metricas_acumuladas (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_abordados INTEGER DEFAULT 0,
            mensagens_enviadas INTEGER DEFAULT 0,
            responderam INTEGER DEFAULT 0,
            interessados INTEGER DEFAULT 0,
            propostas INTEGER DEFAULT 0,
            fechados INTEGER DEFAULT 0,
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS rodadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            qtd_leads INTEGER DEFAULT 0
        );

        INSERT OR IGNORE INTO metricas_acumuladas (id) VALUES (1);
    """)
    conn.commit()
    conn.close()
    # Executar migração de novas colunas e status
    migrate_db()


def migrate_db():
    """Adiciona novas colunas e migra status antigos para canônicos."""
    conn = get_conn()

    # Adicionar novas colunas se não existirem
    colunas_existentes = [r[1] for r in conn.execute("PRAGMA table_info(leads)").fetchall()]
    for coluna, tipo in NOVAS_COLUNAS.items():
        if coluna not in colunas_existentes:
            conn.execute(f"ALTER TABLE leads ADD COLUMN {coluna} {tipo}")

    # Migrar status antigos para novos canônicos
    for antigo, novo in STATUS_MAP.items():
        conn.execute("UPDATE leads SET status = ? WHERE status = ?", (novo, antigo))

    conn.commit()
    conn.close()


def upsert_lead(conn, lead_id, nome, status="novo", data_abordagem="",
                 data_followup="", observacoes="", nicho="", cidade="",
                 telefone="", whatsapp="", score=0, prioridade="",
                 mensagem_whatsapp="", link_whatsapp="", rodada=1):
    """Insere ou atualiza um lead (campos originais)."""
    conn.execute("""
        INSERT INTO leads (lead_id, nome, status, data_abordagem, data_followup,
                           observacoes, nicho, cidade, telefone, whatsapp, score,
                           prioridade, mensagem_whatsapp, link_whatsapp, rodada)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(lead_id) DO UPDATE SET
            nome = excluded.nome,
            status = excluded.status,
            data_abordagem = CASE WHEN excluded.status != 'novo' OR leads.status = 'novo'
                             THEN excluded.data_abordagem ELSE leads.data_abordagem END,
            data_followup = excluded.data_followup,
            observacoes = CASE WHEN excluded.observacoes != '' THEN excluded.observacoes ELSE leads.observacoes END,
            nicho = excluded.nicho,
            cidade = excluded.cidade,
            telefone = excluded.telefone,
            whatsapp = excluded.whatsapp,
            score = excluded.score,
            prioridade = excluded.prioridade,
            mensagem_whatsapp = excluded.mensagem_whatsapp,
            link_whatsapp = excluded.link_whatsapp,
            rodada = excluded.rodada,
            atualizado_em = datetime('now','localtime')
    """, (lead_id, nome, status, data_abordagem, data_followup, observacoes,
          nicho, cidade, telefone, whatsapp, score, prioridade,
          mensagem_whatsapp, link_whatsapp, rodada))


def upsert_lead_full(conn, lead_id, nome, status="novo", data_abordagem="",
                     data_followup="", observacoes="", nicho="", cidade="",
                     bairro="", telefone="", whatsapp="", score=0, prioridade="",
                     mensagem_whatsapp="", link_whatsapp="", rodada=1,
                     tem_site="", url_site="", nota_google=0.0,
                     qtd_avaliacoes=0, oferta_sugerida="", motivo_prioridade="",
                     acao_recomendada="", tipo_de_material="", email="",
                     endereco="", link_maps="", instagram="",
                     followup_mensagem="", numero_formatado="", categoria="",
                     proximo_followup="", resposta_cliente=""):
    """Insere ou atualiza um lead com todos os campos."""
    # Normalizar status para canônico
    status_normalizado = STATUS_MAP.get(status, status)
    if status_normalizado not in STATUS_VALIDOS:
        status_normalizado = "novo"

    conn.execute("""
        INSERT INTO leads (lead_id, nome, status, data_abordagem, data_followup,
                           observacoes, nicho, cidade, bairro, telefone, whatsapp,
                           score, prioridade, mensagem_whatsapp, link_whatsapp, rodada,
                           tem_site, url_site, nota_google, qtd_avaliacoes,
                           oferta_sugerida, motivo_prioridade, acao_recomendada,
                           tipo_de_material, email, endereco, link_maps, instagram,
                           followup_mensagem, numero_formatado, categoria,
                           proximo_followup, resposta_cliente)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(lead_id) DO UPDATE SET
            nome = CASE WHEN excluded.nome != '' THEN excluded.nome ELSE leads.nome END,
            status = CASE WHEN leads.status IN ('novo', 'pronto_para_enviar')
                      OR excluded.status NOT IN ('novo', 'pronto_para_enviar')
                      THEN excluded.status ELSE leads.status END,
            data_abordagem = CASE WHEN excluded.data_abordagem != '' THEN excluded.data_abordagem ELSE leads.data_abordagem END,
            data_followup = CASE WHEN excluded.data_followup != '' THEN excluded.data_followup ELSE leads.data_followup END,
            observacoes = CASE WHEN excluded.observacoes != '' THEN excluded.observacoes ELSE leads.observacoes END,
            nicho = CASE WHEN excluded.nicho != '' THEN excluded.nicho ELSE leads.nicho END,
            cidade = CASE WHEN excluded.cidade != '' THEN excluded.cidade ELSE leads.cidade END,
            bairro = CASE WHEN excluded.bairro != '' THEN excluded.bairro ELSE leads.bairro END,
            telefone = CASE WHEN excluded.telefone != '' THEN excluded.telefone ELSE leads.telefone END,
            whatsapp = CASE WHEN excluded.whatsapp != '' THEN excluded.whatsapp ELSE leads.whatsapp END,
            score = CASE WHEN excluded.score != 0 THEN excluded.score ELSE leads.score END,
            prioridade = CASE WHEN excluded.prioridade != '' THEN excluded.prioridade ELSE leads.prioridade END,
            mensagem_whatsapp = CASE WHEN excluded.mensagem_whatsapp != '' THEN excluded.mensagem_whatsapp ELSE leads.mensagem_whatsapp END,
            link_whatsapp = CASE WHEN excluded.link_whatsapp != '' THEN excluded.link_whatsapp ELSE leads.link_whatsapp END,
            rodada = excluded.rodada,
            tem_site = CASE WHEN excluded.tem_site != '' THEN excluded.tem_site ELSE leads.tem_site END,
            url_site = CASE WHEN excluded.url_site != '' THEN excluded.url_site ELSE leads.url_site END,
            nota_google = CASE WHEN excluded.nota_google != 0.0 THEN excluded.nota_google ELSE leads.nota_google END,
            qtd_avaliacoes = CASE WHEN excluded.qtd_avaliacoes != 0 THEN excluded.qtd_avaliacoes ELSE leads.qtd_avaliacoes END,
            oferta_sugerida = CASE WHEN excluded.oferta_sugerida != '' THEN excluded.oferta_sugerida ELSE leads.oferta_sugerida END,
            motivo_prioridade = CASE WHEN excluded.motivo_prioridade != '' THEN excluded.motivo_prioridade ELSE leads.motivo_prioridade END,
            acao_recomendada = CASE WHEN excluded.acao_recomendada != '' THEN excluded.acao_recomendada ELSE leads.acao_recomendada END,
            tipo_de_material = CASE WHEN excluded.tipo_de_material != '' THEN excluded.tipo_de_material ELSE leads.tipo_de_material END,
            email = CASE WHEN excluded.email != '' THEN excluded.email ELSE leads.email END,
            endereco = CASE WHEN excluded.endereco != '' THEN excluded.endereco ELSE leads.endereco END,
            link_maps = CASE WHEN excluded.link_maps != '' THEN excluded.link_maps ELSE leads.link_maps END,
            instagram = CASE WHEN excluded.instagram != '' THEN excluded.instagram ELSE leads.instagram END,
            followup_mensagem = CASE WHEN excluded.followup_mensagem != '' THEN excluded.followup_mensagem ELSE leads.followup_mensagem END,
            numero_formatado = CASE WHEN excluded.numero_formatado != '' THEN excluded.numero_formatado ELSE leads.numero_formatado END,
            categoria = CASE WHEN excluded.categoria != '' THEN excluded.categoria ELSE leads.categoria END,
            proximo_followup = CASE WHEN excluded.proximo_followup != '' THEN excluded.proximo_followup ELSE leads.proximo_followup END,
            resposta_cliente = CASE WHEN excluded.resposta_cliente != '' THEN excluded.resposta_cliente ELSE leads.resposta_cliente END,
            atualizado_em = datetime('now','localtime')
    """, (lead_id, nome, status_normalizado, data_abordagem, data_followup,
          observacoes, nicho, cidade, bairro, telefone, whatsapp, score,
          prioridade, mensagem_whatsapp, link_whatsapp, rodada,
          tem_site, url_site, nota_google, qtd_avaliacoes,
          oferta_sugerida, motivo_prioridade, acao_recomendada,
          tipo_de_material, email, endereco, link_maps, instagram,
          followup_mensagem, numero_formatado, categoria,
          proximo_followup, resposta_cliente))


def get_all_leads(conn, rodada=None):
    """Retorna todos os leads, opcionalmente filtrados por rodada."""
    if rodada:
        rows = conn.execute("SELECT * FROM leads WHERE rodada = ? ORDER BY score DESC", (rodada,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM leads ORDER BY rodada DESC, score DESC").fetchall()
    return [dict(r) for r in rows]


def get_lead(conn, lead_id):
    """Retorna um lead específico."""
    row = conn.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,)).fetchone()
    return dict(row) if row else None


def get_followups_hoje(conn):
    """Retorna leads com follow-up vencido (proximo_followup <= hoje) e status ativo."""
    from datetime import date
    hoje = date.today().isoformat()
    rows = conn.execute("""
        SELECT * FROM leads
        WHERE proximo_followup <= ?
        AND status NOT IN ('convertido', 'perdido')
        AND proximo_followup != ''
        ORDER BY proximo_followup ASC, score DESC
    """, (hoje,)).fetchall()
    return [dict(r) for r in rows]


def get_leads_by_status(conn, status_list):
    """Retorna leads filtrados por lista de status."""
    placeholders = ",".join("?" * len(status_list))
    rows = conn.execute(
        f"SELECT * FROM leads WHERE status IN ({placeholders}) ORDER BY score DESC",
        status_list
    ).fetchall()
    return [dict(r) for r in rows]


def update_status(conn, lead_id, status, data_abordagem=None, data_followup=None,
                  observacoes=None, proximo_followup=None, resposta_cliente=None):
    """Atualiza o status de um lead e recalcula métricas."""
    # Normalizar status
    status = STATUS_MAP.get(status, status)

    sets = ["status = ?", "atualizado_em = datetime('now','localtime')"]
    params = [status]
    if data_abordagem is not None:
        sets.append("data_abordagem = ?")
        params.append(data_abordagem)
    if data_followup is not None:
        sets.append("data_followup = ?")
        params.append(data_followup)
    if observacoes is not None:
        sets.append("observacoes = ?")
        params.append(observacoes)
    if proximo_followup is not None:
        sets.append("proximo_followup = ?")
        params.append(proximo_followup)
    if resposta_cliente is not None:
        sets.append("resposta_cliente = ?")
        params.append(resposta_cliente)
    params.append(lead_id)
    conn.execute(f"UPDATE leads SET {', '.join(sets)} WHERE lead_id = ?", params)
    conn.commit()
    recalcular_metricas(conn)


def marcar_como_enviado(conn, lead_id):
    """Marca lead como abordado com data de hoje e follow-up para daqui 7 dias."""
    from datetime import date, timedelta
    hoje = date.today().isoformat()
    followup = (date.today() + timedelta(days=7)).isoformat()
    conn.execute("""
        UPDATE leads SET
            status = 'abordado',
            data_abordagem = ?,
            proximo_followup = ?,
            atualizado_em = datetime('now','localtime')
        WHERE lead_id = ?
    """, (hoje, followup, lead_id))
    conn.commit()
    recalcular_metricas(conn)
    return {"data_abordagem": hoje, "proximo_followup": followup}


def recalcular_metricas(conn):
    """Recalcula as métricas acumuladas com base nos status canônicos."""
    rows = conn.execute("SELECT status FROM leads").fetchall()
    total = len(rows)
    pronto_enviar = sum(1 for r in rows if r["status"] == "pronto_para_enviar")
    abordados = sum(1 for r in rows if r["status"] in ["abordado", "respondeu", "follow_up", "interessado", "convertido"])
    responderam = sum(1 for r in rows if r["status"] in ["respondeu", "interessado", "convertido"])
    interessados = sum(1 for r in rows if r["status"] in ["interessado", "convertido"])
    convertidos = sum(1 for r in rows if r["status"] == "convertido")
    perdidos = sum(1 for r in rows if r["status"] == "perdido")
    conn.execute("""
        UPDATE metricas_acumuladas SET
            total_abordados = ?,
            mensagens_enviadas = ?,
            responderam = ?,
            interessados = ?,
            propostas = ?,
            fechados = ?,
            atualizado_em = datetime('now','localtime')
        WHERE id = 1
    """, (total, abordados, responderam, interessados, convertidos, convertidos))
    conn.commit()


def get_metricas(conn):
    """Retorna as métricas acumuladas."""
    row = conn.execute("SELECT * FROM metricas_acumuladas WHERE id = 1").fetchone()
    return dict(row) if row else {
        "total_abordados": 0,
        "mensagens_enviadas": 0,
        "responderam": 0,
        "interessados": 0,
        "propostas": 0,
        "fechados": 0,
    }


def get_rodada_atual(conn):
    """Retorna o número da última rodada."""
    row = conn.execute("SELECT MAX(rodada) as r FROM leads").fetchone()
    return row["r"] if row["r"] else 0


def importar_status_json(conn, status_dict, rodada=1):
    """Importa leads de um dicionário status_leads.json."""
    for lid, dados in status_dict.items():
        upsert_lead(conn,
            lead_id=lid,
            nome=dados.get("nome", ""),
            status=dados.get("status", "novo"),
            data_abordagem=dados.get("data_abordagem", ""),
            data_followup=dados.get("data_followup", ""),
            observacoes=dados.get("observacoes", ""),
            rodada=rodada)
    recalcular_metricas(conn)