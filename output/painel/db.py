#!/usr/bin/env python3
"""Módulo de banco de dados SQLite para o Painel de Prospecção."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "prospeccao.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Cria as tabelas se não existirem."""
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


def upsert_lead(conn, lead_id, nome, status="novo", data_abordagem="",
                 data_followup="", observacoes="", nicho="", cidade="",
                 telefone="", whatsapp="", score=0, prioridade="",
                 mensagem_whatsapp="", link_whatsapp="", rodada=1):
    """Insere ou atualiza um lead."""
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


def update_status(conn, lead_id, status, data_abordagem=None, data_followup=None, observacoes=None):
    """Atualiza o status de um lead e recalcula métricas."""
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
    params.append(lead_id)
    conn.execute(f"UPDATE leads SET {', '.join(sets)} WHERE lead_id = ?", params)
    conn.commit()
    recalcular_metricas(conn)


def recalcular_metricas(conn):
    """Recalcula as métricas acumuladas com base nos status dos leads."""
    rows = conn.execute("SELECT status FROM leads").fetchall()
    enviadas = sum(1 for r in rows if r["status"] in ["mensagem enviada", "video enviado", "respondeu", "interessado", "proposta enviada", "fechado", "follow-up"])
    responderam = sum(1 for r in rows if r["status"] in ["respondeu", "interessado", "proposta enviada", "fechado"])
    interessados = sum(1 for r in rows if r["status"] in ["interessado", "proposta enviada", "fechado"])
    propostas = sum(1 for r in rows if r["status"] in ["proposta enviada", "fechado"])
    fechados = sum(1 for r in rows if r["status"] == "fechado")
    conn.execute("""
        UPDATE metricas_acumuladas SET
            total_abordados = (SELECT COUNT(*) FROM leads),
            mensagens_enviadas = ?,
            responderam = ?,
            interessados = ?,
            propostas = ?,
            fechados = ?,
            atualizado_em = datetime('now','localtime')
        WHERE id = 1
    """, (enviadas, responderam, interessados, propostas, fechados))
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