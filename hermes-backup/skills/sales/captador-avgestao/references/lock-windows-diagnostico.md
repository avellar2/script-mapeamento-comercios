# Diagnóstico: PermissionError no Lock Global (Windows)

**Data:** 2026-06-29  
**Run afetado:** `run_20260629_014644_583c55`

## Traceback Original

```
File "config\lock.py", line 217, in _adquirir
    _escrever_metadados(GLOBAL_LOCK_FILE, metadados)
File "config\lock.py", line 76, in _escrever_metadados
    caminho.write_text(...)
PermissionError: [Errno 13] Permission denied
```

## Causa Raiz

No Windows, `msvcrt.locking(fd, LK_NBLCK, 1)` adquire lock exclusivo no byte 0 do arquivo via fd. Em seguida, `_escrever_metadados()` chamava `Path.write_text()`, que internamente faz `open(path, 'w')` — abrindo um **segundo handle** no mesmo arquivo. O Windows nega a segunda abertura com `PermissionError` porque o arquivo tem lock exclusivo.

O arquivo ficava com 0 bytes (criado por `touch()`) porque a escrita de metadados nunca completava.

## Evidência

Script `diagnostico_lock.py` provou:
- `Path.write_text()` → **PermissionError** (segundo handle negado)
- `os.write(fd, dados)` → **OK** (escrita direta no handle com lock)

## Correção Aplicada em `config/lock.py`

```python
def _escrever_metadados(caminho: Path, metadados: dict, fd: Optional[int] = None) -> None:
    conteudo = json.dumps(metadados, ensure_ascii=False, indent=2)
    if fd is not None:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            dados = conteudo.encode("utf-8")
            os.write(fd, dados)
            os.fsync(fd)
            return
        except OSError:
            # fd inválido (mock em testes) — fallback para write_text
            pass
    caminho.write_text(conteudo, encoding="utf-8")
```

- Todas as 4 chamadas de `_escrever_metadados` atualizadas para passar `fd=fd`
- Fallback `write_text` para mocks de teste que usam fd fake (999)

## Procedimento de Diagnóstico (9 Etapas)

1. **Ler traceback exato** — arquivo, função, linha, operação
2. **Verificar captador ativo** — `--status` + `ps aux | grep mapear` (NÃO matar processos)
3. **Inspecionar arquivos de lock** — tamanho, data, conteúdo (PID ativo?), permissões
4. **Testar lock sem captação** — script `diagnostico_lock.py`
5. **Auditar `lock.py` no Windows** — verificar `msvcrt.locking` vs `write_text`
6. **Limpeza segura** — backup antes de mover, NÃO `rm -f` às cegas
7. **Testes** — `pytest tests/test_lock.py` + `pytest tests/`
8. **Validar run** — `--status` confirmando tarefas/leads preservados
9. **Retomar** — `--resume --run-id <RUN_ID>`, uma única vez

## Testes

- `test_lock.py`: 16/16 ✅ (inclui mock com fd=999, fallback funciona)
- `test_navegacao_robusta.py`: 20/20 ✅
- Total: 346/346 ✅

## Arquivos de Lock

- `output/avgestao/captador_global.lock` — lock global (deletado na liberação)
- `output/avgestao/captador_global.stale_*.lock` — locks abandonados (movidos para backup)
- `output/avgestao/runs/<run_id>/run.lock` — lock por run (deletado na liberação)
- `output/avgestao/backups_locks/` — backups de locks movidos