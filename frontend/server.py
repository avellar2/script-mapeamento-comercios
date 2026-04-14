#!/usr/bin/env python3
"""
Servidor local simples para o dashboard de comércios.
Execute este script para abrir o dashboard no navegador.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Configurações
PORT = 8000
DIRECTORY = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Adicionar headers CORS para permitir carregar o JSON
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print(f"\n{'='*60}")
        print(f"  🚀 Servidor iniciado!")
        print(f"{'='*60}")
        print(f"\n  Abrindo dashboard em: {url}\n")
        print(f"  Pressione Ctrl+C para parar o servidor\n")
        print(f"{'='*60}\n")

        # Abrir navegador automaticamente
        webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n\n{'='*60}")
            print("  ✅ Servidor encerrado")
            print(f"{'='*60}\n")
            sys.exit(0)

if __name__ == "__main__":
    start_server()
