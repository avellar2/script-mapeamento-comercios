#!/usr/bin/env python3
"""Servidor local para o Painel de Prospecção com SQLite."""

import json
import http.server
import socketserver
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

import db

PORT = 8000
PAINEL_DIR = Path(__file__).parent


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

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/leads":
            conn = db.get_conn()
            rodada = db.get_rodada_atual(conn)
            leads = db.get_all_leads(conn, rodada=rodada)
            metricas = db.get_metricas(conn)
            conn.close()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"leads": leads, "metricas": metricas, "rodada_atual": rodada}, ensure_ascii=False).encode("utf-8"))
            return
        if path == "/api/metricas":
            conn = db.get_conn()
            metricas = db.get_metricas(conn)
            conn.close()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(metricas, ensure_ascii=False).encode("utf-8"))
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                conn = db.get_conn()
                for lid, dados in data.items():
                    db.update_status(conn, lid,
                        status=dados.get("status", "novo"),
                        data_abordagem=dados.get("data_abordagem"),
                        data_followup=dados.get("data_followup"),
                        observacoes=dados.get("observacoes"))
                conn.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        if path == "/api/status-single":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                conn = db.get_conn()
                db.update_status(conn,
                    lead_id=data["lead_id"],
                    status=data.get("status", "novo"),
                    data_abordagem=data.get("data_abordagem"),
                    data_followup=data.get("data_followup"),
                    observacoes=data.get("observacoes"))
                metricas = db.get_metricas(conn)
                conn.close()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "metricas": metricas}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()


def start():
    db.init_db()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print(f"\n  Painel de Prospecção rodando em: {url}")
        print(f"  Banco de dados: {db.DB_PATH}")
        print(f"  Ctrl+C para parar\n")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Servidor encerrado")
            sys.exit(0)


if __name__ == "__main__":
    start()