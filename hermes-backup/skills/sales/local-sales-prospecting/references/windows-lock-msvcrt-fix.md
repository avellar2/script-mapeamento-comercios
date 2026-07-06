# Windows Lock Fix — msvcrt.locking + os.write

## Problema

No Windows, `config/lock.py` falhava com `PermissionError` ao escrever metadados no arquivo de lock após adquirir a trava via `msvcrt.locking()`.

## Causa Raiz

`Path.write_text()` abre um **segundo handle** no mesmo arquivo que já tem um lock exclusivo via `msvcrt.locking()`. O Windows nega a segunda abertura com `PermissionError [Errno 13]`.

```
_lock_arquivo() → os.open(O_RDWR | O_CREAT) → fd=3
msvcrt.locking(fd, LK_NBLCK, 1) → lock adquirido no byte 0
_escrever_metadados() → Path.write_text() → open(path, 'w') → PermissionError!
```

O arquivo ficava com 0 bytes (criado por `touch()` em `_lock_arquivo`, nunca escrito).

## Diagnóstico

Script `scripts/diagnostico_lock.py` confirma:
1. Lock adquirido com sucesso (fd=3)
2. `write_text()` → `PermissionError: [Errno 13] Permission denied`
3. `os.write(fd, ...)` → funciona perfeitamente (221 bytes)
4. Lock liberado com sucesso

## Correção

`_escrever_metadados()` agora aceita `fd` e usa `os.write` quando o lock está ativo:

```python
def _escrever_metadados(caminho: Path, metadados: dict, fd: Optional[int] = None) -> None:
    conteudo = json.dumps(metadados, ensure_ascii=False, indent=2)
    if fd is not None:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            os.write(fd, conteudo.encode("utf-8"))
            os.fsync(fd)
            return
        except OSError:
            pass  # fd inválido (mock em testes) — fallback
    caminho.write_text(conteudo, encoding="utf-8")
```

Todas as 4 chamadas em `LockGlobal._adquirir()` e `LockRun._adquirir()` passam `fd=fd`.

## Fallback para Testes

O `except OSError` no `os.write` garante que mocks de teste (que retornam `fd=999`) caiam no fallback `write_text` sem quebrar.

## Limpeza de Locks Stale

Locks abandonados (PID morto) são movidos para `captador_global.stale_<timestamp>.lock`. Antes de retomar um run:

1. Verificar se nenhum captador está ativo (`wmic process` + `--status`)
2. Fazer backup dos stale em `output/avgestao/backups_locks/<timestamp>/`
3. Remover os stale do diretório principal
4. Rodar diagnóstico do lock para confirmar

## Arquivos Relevantes

- `config/lock.py` — implementação do lock global e por run
- `scripts/diagnostico_lock.py` — diagnóstico isolado
- `tests/test_lock.py` — 16 testes (todos passando)