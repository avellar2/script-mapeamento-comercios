#!/usr/bin/env python3
"""
Diagnóstico isolado do lock global.
NÃO abre navegador, NÃO altera o run, NÃO mata processos.
Tenta adquirir e liberar o lock usando a mesma implementação de config/lock.py.
"""
import sys
import os
import time
import json
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.lock import (
    _lock_arquivo, _unlock_arquivo, _escrever_metadados, _ler_metadados,
    GLOBAL_LOCK_FILE, _pid_esta_vivo, _agora_iso, _hostname, _comando
)

def diagnosticar_lock():
    """Diagnóstico completo do lock global."""
    print("=" * 60)
    print("  DIAGNÓSTICO DO LOCK GLOBAL")
    print("=" * 60)
    
    # 1. Verificar estado atual do arquivo
    print("\n1. ESTADO ATUAL DO ARQUIVO:")
    if GLOBAL_LOCK_FILE.exists():
        stat = GLOBAL_LOCK_FILE.stat()
        print(f"   Arquivo: {GLOBAL_LOCK_FILE}")
        print(f"   Tamanho: {stat.st_size} bytes")
        print(f"   Modificado: {time.ctime(stat.st_mtime)}")
        print(f"   Permissões: {oct(stat.st_mode)[-3:]}")
        print(f"   Proprietário UID: {stat.st_uid}")
        
        metadados = _ler_metadados(GLOBAL_LOCK_FILE)
        if metadados:
            print(f"   Metadados: {json.dumps(metadados, indent=2, ensure_ascii=False)}")
            pid = metadados.get("pid")
            if pid:
                vivo = _pid_esta_vivo(pid)
                print(f"   PID {pid} está vivo? {vivo}")
        else:
            print("   Metadados: VAZIO (0 bytes ou inválido)")
    else:
        print(f"   Arquivo {GLOBAL_LOCK_FILE} NÃO EXISTE")
    
    # 2. Testar abertura simples (sem lock)
    print("\n2. TESTE DE ABERTURA SIMPLES (sem lock):")
    try:
        with open(GLOBAL_LOCK_FILE, 'r') as f:
            conteudo = f.read()
            print(f"   Abertura para leitura: OK ({len(conteudo)} bytes)")
    except PermissionError as e:
        print(f"   ABERTURA PARA LEITURA FALHOU: {e}")
    except FileNotFoundError:
        print("   Arquivo não existe (será criado)")
    
    try:
        test_path = GLOBAL_LOCK_FILE.with_suffix('.test_write')
        test_path.write_text("teste", encoding='utf-8')
        print(f"   Escrita em arquivo teste: OK")
        test_path.unlink()
    except PermissionError as e:
        print(f"   ESCRITA NO DIRETÓRIO FALHOU: {e}")
    
    # 3. Testar lock real (msvcrt.locking)
    print("\n3. TESTE DE LOCK REAL (msvcrt.locking):")
    fd = None
    try:
        fd = _lock_arquivo(GLOBAL_LOCK_FILE)
        if fd is not None:
            print(f"   Lock adquirido com sucesso! fd={fd}")
            
            # 4. Testar escrita COM o lock (o bug reportado)
            print("\n4. TESTE DE ESCRITA COM LOCK ADQUIRIDO:")
            try:
                metadados_teste = {
                    "pid": os.getpid(),
                    "run_id": "diagnostico_lock",
                    "inicio": _agora_iso(),
                    "hostname": _hostname(),
                    "comando": "diagnostico_playwright_maps.py",
                    "tipo": "global",
                    "diagnostico": True,
                }
                _escrever_metadados(GLOBAL_LOCK_FILE, metadados_teste)
                print("   write_text COM lock: OK (inesperado — bug pode ter sido corrigido)")
                
                # Verificar se os metadados foram escritos
                lidos = _ler_metadados(GLOBAL_LOCK_FILE)
                if lidos:
                    print(f"   Metadados lidos: {json.dumps(lidos, indent=2, ensure_ascii=False)}")
                else:
                    print("   ATENÇÃO: Metadados não foram lidos após escrita!")
                
            except PermissionError as e:
                print(f"   BUG CONFIRMADO: write_text falhou com lock adquirido!")
                print(f"   PermissionError: {e}")
                print(f"   Isso acontece porque write_text() abre um segundo handle")
                print(f"   no mesmo arquivo que já tem msvcrt.locking() ativo.")
                
                # 4b. Tentar escrever via fd (direto no handle com lock)
                print("\n4b. TENTATIVA VIA fd (os.write):")
                try:
                    os.lseek(fd, 0, os.SEEK_SET)
                    dados = json.dumps(metadados_teste, ensure_ascii=False, indent=2)
                    dados_bytes = dados.encode('utf-8')
                    os.write(fd, dados_bytes)
                    os.fsync(fd)
                    print(f"   os.write via fd: OK ({len(dados_bytes)} bytes)")
                    
                    # Verificar se foi escrito
                    os.lseek(fd, 0, os.SEEK_SET)
                    lido = os.read(fd, 1024)
                    print(f"   Leitura via fd: {lido[:100]}")
                except Exception as e2:
                    print(f"   os.write via fd falhou: {e2}")
            
            # 5. Liberar o lock
            print("\n5. LIBERAÇÃO DO LOCK:")
            _unlock_arquivo(fd)
            fd = None
            print("   Lock liberado com sucesso")
            
        else:
            print("   Lock JÁ ESTÁ OCUPADO por outro processo")
            # Verificar quem é o dono
            metadados = _ler_metadados(GLOBAL_LOCK_FILE)
            if metadados:
                print(f"   Dono: {json.dumps(metadados, indent=2, ensure_ascii=False)}")
                pid = metadados.get("pid")
                if pid:
                    vivo = _pid_esta_vivo(pid)
                    print(f"   PID {pid} está vivo? {vivo}")
                    if not vivo:
                        print("   → Lock ABANDONADO (PID morto)")
                    else:
                        print("   → Lock ATIVO (PID vivo)")
            else:
                print("   Sem metadados — lock sem dono conhecido")
    
    except Exception as e:
        print(f"   ERRO INESPERADO: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if fd is not None:
            try:
                _unlock_arquivo(fd)
            except Exception:
                pass
    
    # 6. Estado final
    print("\n6. ESTADO FINAL:")
    if GLOBAL_LOCK_FILE.exists():
        stat = GLOBAL_LOCK_FILE.stat()
        print(f"   Arquivo existe: {stat.st_size} bytes")
        metadados = _ler_metadados(GLOBAL_LOCK_FILE)
        if metadados:
            print(f"   Metadados: {json.dumps(metadados, indent=2, ensure_ascii=False)}")
        else:
            print("   Metadados: VAZIO")
    else:
        print("   Arquivo NÃO EXISTE (foi deletado na liberação)")
    
    print("\n" + "=" * 60)
    print("  DIAGNÓSTICO CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    diagnosticar_lock()