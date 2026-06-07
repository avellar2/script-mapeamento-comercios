#!/usr/bin/env python3
"""Servidor local para o Painel de Prospecção com Supabase como fonte da verdade."""

import json
import os
import http.server
import socketserver
import sys
import webbrowser
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# Carrega .env do projeto raiz
# Prioridade: cwd (roda do projeto raiz), fallback relativo ao script
_dotenv_path = Path.cwd() / ".env"
if not _dotenv_path.exists():
    _dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _dotenv_path.exists():
    load_dotenv(_dotenv_path, override=True)

from supabase import create_client, Client

import db

PORT = 8000
PAINEL_DIR = Path(__file__).parent

# ─── Supabase ────────────────────────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY", "")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("  [OK] Supabase conectado: {0}".format(SUPABASE_URL))
    except Exception as e:
        print("  [!] Erro ao conectar Supabase: {0}".format(e))
        supabase = None
else:
    print("  [!] SUPABASE_URL ou SUPABASE_KEY nao encontrados no .env")

HAS_SUPABASE = supabase is not None


# ─── Helpers Supabase ────────────────────────────────────────

def _metricas_from_supabase():
    """Calcula métricas diretamente do Supabase."""
    if not supabase:
        return {}
    try:
        total = supabase.table("leads").select("id", count="exact").execute()
        counts = {}
        for s in ["novo", "pronto_para_enviar", "abordado", "respondido", "follow_up", "interessado", "convertido", "perdido"]:
            r = supabase.table("leads").select("id", count="exact").eq("status", s).execute()
            counts[s] = r.count or 0

        # Contagens por regiao
        for origem in ["baixada", "rio_premium"]:
            r = supabase.table("leads").select("id", count="exact").eq("origem", origem).execute()
            counts[origem] = r.count or 0

        return {
            "total_leads": total.count or 0,
            "novo": counts.get("novo", 0),
            "pronto_para_enviar": counts.get("pronto_para_enviar", 0),
            "abordado": counts.get("abordado", 0),
            "respondido": counts.get("respondido", 0),
            "follow_up": counts.get("follow_up", 0),
            "interessado": counts.get("interessado", 0),
            "convertido": counts.get("convertido", 0),
            "perdido": counts.get("perdido", 0),
            "baixada": counts.get("baixada", 0),
            "rio_premium": counts.get("rio_premium", 0),
        }
    except Exception as e:
        print("  [!] Erro ao calcular metricas: {0}".format(e))
        return {}


def _leads_from_supabase(status_filter=None, limit=5000):
    """Busca leads do Supabase com todos os campos necessários."""
    if not supabase:
        return []

    try:
        query = supabase.table("leads").select("*").limit(limit).order("score", desc=True)
        if status_filter:
            query = query.eq("status", status_filter)

        result = query.execute()
        leads = []
        for row in result.data or []:
            leads.append({
                # Campos que o CRM espera
                "lead_id": row.get("id") or row.get("lead_id") or "",
                "nome": row.get("nome") or "",
                "status": row.get("status") or "novo",
                "telefone": row.get("telefone") or "",
                "whatsapp": row.get("whatsapp") or "",
                "telefone_normalizado": row.get("telefone_normalizado") or "",
                "link_whatsapp": row.get("link_whatsapp") or "",
                "nicho": row.get("nicho") or row.get("categoria") or "",
                "categoria": row.get("categoria") or row.get("nicho") or "",
                "cidade": row.get("cidade") or "",
                "bairro": row.get("bairro") or "",
                "score": row.get("score") or 0,
                "prioridade": row.get("prioridade") or "",
                "oferta_sugerida": row.get("oferta_sugerida") or "",
                "mensagem_whatsapp": row.get("mensagem_whatsapp") or "",
                "data_abordagem": _format_date(row.get("ultimo_contato_em") or row.get("data_abordagem") or ""),
                "proximo_followup": _format_date(row.get("proximo_followup_em") or ""),
                "data_followup": _format_date(row.get("proximo_followup_em") or ""),
                "observacoes": row.get("observacoes") or "",
                "resposta_cliente": row.get("resposta_cliente") or "",
                "followup_mensagem": row.get("followup_mensagem") or "",
                "tem_site": row.get("tem_site"),
                "url_site": row.get("url_site") or "",
                "nota_google": row.get("avaliacao") or 0,
                "qtd_avaliacoes": row.get("num_avaliacoes") or 0,
                "instagram": row.get("instagram") or "",
                "email": row.get("email") or "",
                "endereco": row.get("endereco") or row.get("endereco_completo") or "",
                "link_maps": row.get("link_maps") or "",
                "motivo_prioridade": row.get("motivo_prioridade") or "",
                "origem": row.get("origem") or "",
                "numero_formatado": row.get("telefone_normalizado") or "",  # compat
            })
        return leads
    except Exception as e:
        print("  [!] Erro ao buscar leads do Supabase: {0}".format(e))
        return []


def _followups_from_supabase():
    """Busca follow-ups de hoje do Supabase."""
    if not supabase:
        return []

    try:
        hoje = date.today().isoformat()
        result = supabase.table("leads").select("*").lte("proximo_followup_em", hoje).order("proximo_followup_em").limit(200).execute()
        # Filtra status no Python (supabase-py not_ syntax é instável entre versões)
        rows = [r for r in (result.data or []) if r.get("status") not in ("convertido", "perdido")]

        leads = []
        for row in rows:
            leads.append({
                "lead_id": row.get("id") or row.get("lead_id") or "",
                "nome": row.get("nome") or "",
                "status": row.get("status") or "",
                "telefone": row.get("telefone") or "",
                "whatsapp": row.get("whatsapp") or "",
                "telefone_normalizado": row.get("telefone_normalizado") or "",
                "link_whatsapp": row.get("link_whatsapp") or "",
                "nicho": row.get("nicho") or row.get("categoria") or "",
                "cidade": row.get("cidade") or "",
                "score": row.get("score") or 0,
                "prioridade": row.get("prioridade") or "",
                "proximo_followup": _format_date(row.get("proximo_followup_em") or ""),
                "data_followup": _format_date(row.get("proximo_followup_em") or ""),
                "observacoes": row.get("observacoes") or "",
            })
        return leads
    except Exception as e:
        print("  [!] Erro ao buscar follow-ups: {0}".format(e))
        return []


def _format_date(val):
    """Normaliza data para DD/MM/YYYY."""
    if not val:
        return ""
    if isinstance(val, str) and "-" in val:
        parts = val.split("T")[0].split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return str(val)


def _update_supabase_status(lead_id, status=None, observacoes=None, resposta_cliente=None,
                             ultimo_contato_em=None, proximo_followup_em=None):
    """Atualiza campos de um lead no Supabase."""
    if not supabase:
        return False
    try:
        update = {}
        if status:
            update["status"] = status
        if observacoes is not None:
            update["observacoes"] = observacoes
        if resposta_cliente is not None:
            update["resposta_cliente"] = resposta_cliente
        if ultimo_contato_em:
            update["ultimo_contato_em"] = ultimo_contato_em
        if proximo_followup_em:
            update["proximo_followup_em"] = proximo_followup_em

        if not update:
            return False

        supabase.table("leads").update(update).eq("id", lead_id).execute()
        return True
    except Exception as e:
        print("  [!] Erro ao atualizar lead {0}: {1}".format(lead_id, e))
        return False


def _criar_interacao_supabase(lead_id, tipo, canal="whatsapp", mensagem="", observacao=""):
    """Cria registro de interação no Supabase."""
    if not supabase:
        return
    try:
        supabase.table("lead_interactions").insert({
            "lead_id": lead_id,
            "tipo": tipo,
            "canal": canal,
            "mensagem": mensagem,
            "observacao": observacao,
        }).execute()
    except Exception as e:
        print("  [!] Erro ao criar interacao: {0}".format(e))


# ─── HTTP Handler ────────────────────────────────────────────

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PAINEL_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path

        # ── API: todos os leads (Supabase) ──────────────────────
        if path == "/api/leads":
            metricas = _metricas_from_supabase() if HAS_SUPABASE else {}
            if HAS_SUPABASE:
                leads = _leads_from_supabase()
            else:
                # Fallback SQLite
                conn = db.get_conn()
                leads = db.get_all_leads(conn)
                # Garante campo origem nos leads do SQLite
                for lead in leads:
                    lead.setdefault("origem", lead.get("origem") or "")
                metricas = db.get_metricas(conn)
                conn.close()
            self.send_json({"leads": leads, "metricas": metricas})
            return

        # ── API: follow-ups de hoje (Supabase) ──────────────────
        if path == "/api/leads/followups":
            if HAS_SUPABASE:
                leads = _followups_from_supabase()
            else:
                conn = db.get_conn()
                leads = db.get_followups_hoje(conn)
                conn.close()
            self.send_json({"leads": leads, "count": len(leads)})
            return

        # ── API: métricas ───────────────────────────────────────
        if path == "/api/metricas":
            if HAS_SUPABASE:
                metricas = _metricas_from_supabase()
            else:
                conn = db.get_conn()
                metricas = db.get_metricas(conn)
                # Contagens por regiao (SQLite)
                for origem in ["baixada", "rio_premium"]:
                    try:
                        row = conn.execute("SELECT COUNT(*) as c FROM leads WHERE origem = ?", (origem,)).fetchone()
                        metricas[origem] = row["c"] if row else 0
                    except Exception:
                        metricas[origem] = 0
                conn.close()
            self.send_json(metricas)
            return

        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path

        # ── API: atualizar status de um lead ───────────────────
        if path == "/api/status-single":
            try:
                data = self.read_body()
                lead_id = data.get("lead_id")
                if not lead_id:
                    self.send_json({"error": "lead_id obrigatório"}, status=400)
                    return

                if HAS_SUPABASE:
                    status = data.get("status")
                    observacoes = data.get("observacoes")
                    resposta_cliente = data.get("resposta_cliente")
                    proximo_followup = data.get("proximo_followup")

                    # Calcula próximo follow-up se status for seguido
                    if status == "abordado":
                        from datetime import timedelta
                        hoje = date.today()
                        proximo = (hoje + timedelta(days=7)).isoformat()
                        _update_supabase_status(lead_id,
                            status=status,
                            observacoes=observacoes,
                            resposta_cliente=resposta_cliente,
                            ultimo_contato_em=hoje.isoformat(),
                            proximo_followup_em=proximo)
                    else:
                        _update_supabase_status(lead_id,
                            status=status,
                            observacoes=observacoes,
                            resposta_cliente=resposta_cliente,
                            proximo_followup_em=proximo)

                    metricas = _metricas_from_supabase()
                    self.send_json({"ok": True, "metricas": metricas})
                else:
                    # Fallback SQLite
                    conn = db.get_conn()
                    db.update_status(conn,
                        lead_id=lead_id,
                        status=data.get("status", "novo"),
                        data_abordagem=data.get("data_abordagem"),
                        data_followup=data.get("data_followup"),
                        observacoes=data.get("observacoes"),
                        proximo_followup=data.get("proximo_followup"),
                        resposta_cliente=data.get("resposta_cliente"))
                    metricas = db.get_metricas(conn)
                    conn.close()
                    self.send_json({"ok": True, "metricas": metricas})
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        # ── API: marcar como enviado ────────────────────────────
        if path == "/api/marcar-enviado":
            try:
                data = self.read_body()
                lead_id = data.get("lead_id") or data.get("leadId")
                if not lead_id:
                    self.send_json({"error": "lead_id obrigatório"}, status=400)
                    return

                hoje = date.today().isoformat()
                followup = (date.today() + timedelta(days=7)).isoformat()

                if HAS_SUPABASE:
                    _update_supabase_status(lead_id,
                        status="abordado",
                        ultimo_contato_em=hoje,
                        proximo_followup_em=followup)
                    _criar_interacao_supabase(lead_id, "primeira_abordagem", canal="whatsapp")
                    metricas = _metricas_from_supabase()
                    self.send_json({"ok": True, "metricas": metricas, "data_abordagem": hoje, "proximo_followup": followup})
                else:
                    conn = db.get_conn()
                    result = db.marcar_como_enviado(conn, lead_id)
                    metricas = db.get_metricas(conn)
                    conn.close()
                    self.send_json({"ok": True, "metricas": metricas, **result})
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        # ── API: salvar resposta do cliente ────────────────────
        if path == "/api/resposta-cliente":
            try:
                data = self.read_body()
                lead_id = data.get("lead_id") or data.get("leadId")
                if not lead_id:
                    self.send_json({"error": "lead_id obrigatório"}, status=400)
                    return

                resposta = data.get("resposta_cliente") or ""
                observacoes = data.get("observacoes")

                if HAS_SUPABASE:
                    update = {"resposta_cliente": resposta}
                    if observacoes is not None:
                        update["observacoes"] = observacoes
                    supabase.table("leads").update(update).eq("id", lead_id).execute()
                    if resposta:
                        _criar_interacao_supabase(lead_id, "resposta_cliente", observacao=resposta[:200])
                    self.send_json({"ok": True})
                else:
                    conn = db.get_conn()
                    db.update_status(conn,
                        lead_id=lead_id,
                        status=None,
                        observacoes=observacoes,
                        resposta_cliente=resposta)
                    conn.close()
                    self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        # ── API: salvar observações ─────────────────────────────
        if path == "/api/observacoes":
            try:
                data = self.read_body()
                lead_id = data.get("lead_id")
                observacoes = data.get("observacoes", "")

                if HAS_SUPABASE:
                    _update_supabase_status(lead_id, observacoes=observacoes)
                    self.send_json({"ok": True})
                else:
                    conn = db.get_conn()
                    db.update_status(conn, lead_id=lead_id, status=None, observacoes=observacoes)
                    conn.close()
                    self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        # ── APIs legadas (SQLite only) ─────────────────────────

        if path == "/api/status":
            try:
                data = self.read_body()
                conn = db.get_conn()
                for lid, dados in data.items():
                    db.update_status(conn, lid,
                        status=dados.get("status", "novo"),
                        data_abordagem=dados.get("data_abordagem"),
                        data_followup=dados.get("data_followup"),
                        observacoes=dados.get("observacoes"))
                conn.close()
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        if path == "/api/importar-leads":
            try:
                data = self.read_body()
                leads_list = data if isinstance(data, list) else data.get("leads", [])
                conn = db.get_conn()
                rodada = db.get_rodada_atual(conn) + 1
                count = 0
                for lead in leads_list:
                    db.upsert_lead_full(conn,
                        lead_id=lead.get("lead_id", ""),
                        nome=lead.get("nome", ""),
                        status=lead.get("status", "pronto_para_enviar"),
                        data_abordagem=lead.get("data_abordagem", ""),
                        data_followup=lead.get("data_followup", ""),
                        observacoes=lead.get("observacoes", ""),
                        nicho=lead.get("nicho", ""),
                        cidade=lead.get("cidade", ""),
                        bairro=lead.get("bairro", ""),
                        telefone=lead.get("telefone", ""),
                        whatsapp=lead.get("whatsapp", ""),
                        score=lead.get("score", 0),
                        prioridade=lead.get("prioridade", ""),
                        mensagem_whatsapp=lead.get("mensagem_whatsapp", ""),
                        link_whatsapp=lead.get("link_whatsapp", lead.get("link_wame", "")),
                        rodada=rodada,
                        tem_site=lead.get("tem_site", ""),
                        url_site=lead.get("url_site", ""),
                        nota_google=lead.get("nota_google", 0),
                        qtd_avaliacoes=lead.get("qtd_avaliacoes", 0),
                        oferta_sugerida=lead.get("oferta_sugerida", ""),
                        motivo_prioridade=lead.get("motivo_prioridade", lead.get("motivo", "")),
                        acao_recomendada=lead.get("acao_recomendada", ""),
                        tipo_de_material=lead.get("tipo_de_material", ""),
                        email=lead.get("email", ""),
                        endereco=lead.get("endereco", ""),
                        link_maps=lead.get("link_maps", ""),
                        instagram=lead.get("instagram", ""),
                        followup_mensagem=lead.get("followup_mensagem", ""),
                        numero_formatado=lead.get("numero_formatado", ""),
                        categoria=lead.get("categoria", lead.get("nicho", "")),
                        proximo_followup=lead.get("proximo_followup", lead.get("data_followup", "")),
                        resposta_cliente=lead.get("resposta_cliente", ""))
                    count += 1
                db.recalcular_metricas(conn)
                conn.close()
                self.send_json({"ok": True, "imported": count, "rodada": rodada})
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        self.send_response(404)
        self.end_headers()


def start():
    db.init_db()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/crm.html"
        print(f"\n  CRM de Prospecção rodando em: {url}")
        print(f"  Painel antigo em: http://localhost:{PORT}/index.html")
        print(f"  Fonte de dados: {'Supabase' if HAS_SUPABASE else 'SQLite (fallback)'}")
        print(f"  Banco local: {db.DB_PATH}")
        print(f"  Ctrl+C para parar\n")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Servidor encerrado")
            sys.exit(0)


if __name__ == "__main__":
    start()