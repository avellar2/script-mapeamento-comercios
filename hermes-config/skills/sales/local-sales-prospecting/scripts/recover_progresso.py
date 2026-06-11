#!/usr/bin/env python3
"""
Recupera progresso.json corrompido quando 2+ scripts escrevem no mesmo arquivo.
Uso: python scripts/recover_progresso.py output/rio_premium/playwright/progresso.json
"""
import json, sys, os
from pathlib import Path

def recover(path: Path) -> dict:
    """Lê o progresso.json corrompido e extrai o primeiro JSON válido."""
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    
    # Usa JSONDecoder para pegar só o primeiro objeto válido
    decoder = json.JSONDecoder()
    obj, end = decoder.raw_decode(text)
    
    # Salva limpo
    backup = path.with_suffix('.json.bak')
    path.rename(backup)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    
    return obj

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python recover_progresso.py <caminho_do_progresso.json>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Arquivo não encontrado: {path}")
        sys.exit(1)
    
    data = recover(path)
    comercios = len(data.get('comercios', []))
    prontas = len(data.get('categorias_prontas', []))
    sem_site = sum(1 for c in data.get('comercios', []) if not c.get('tem_site'))
    
    print(f"Recuperado! Backup salvo em: {path}.bak")
    print(f"Comércios: {comercios}")
    print(f"Categorias prontas: {prontas}")
    print(f"Sem site: {sem_site}")