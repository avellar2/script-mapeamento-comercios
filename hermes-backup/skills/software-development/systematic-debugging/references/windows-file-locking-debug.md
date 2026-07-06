# Windows File Locking Debug Patterns

## The msvcrt.locking() + Path.write_text() Bug

### Symptom
`PermissionError: [Errno 13] Permission denied` when calling `Path.write_text()` on a file that has an active `msvcrt.locking()` lock.

### Root Cause
On Windows, `msvcrt.locking(fd, LK_NBLCK, 1)` acquires an exclusive OS-level lock on byte 0 of the file. `Path.write_text()` internally calls `open(path, 'w')` which opens a **second file handle**. Windows denies the second handle because the first handle has an exclusive lock via `msvcrt.locking()`.

### The Fix
Write metadata directly through the already-open file descriptor (fd), not through a new handle:

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

### Diagnostic Pattern
1. **Isolate the lock**: Create a standalone script that exercises the exact same `_lock_arquivo()` → `_escrever_metadados()` path
2. **Test with real OS lock**: Don't mock `msvcrt.locking()` — the bug only manifests with the real OS-level lock
3. **Test writing via fd**: If `os.write(fd, ...)` works but `Path.write_text()` fails, the bug is confirmed
4. **Add fallback for mocks**: Tests often use fake fds (e.g., `fd=999`). The fix must handle both real fds (use `os.write`) and fake fds (fallback to `write_text`)

### General Technique: Isolated Diagnostic Script

When debugging production failures that involve side effects (file locks, browser state, network), create a **standalone diagnostic script** that:

1. **Exercises the exact same code path** as the failing operation — imports the same functions, calls them with the same parameters
2. **Has zero side effects** — no browser launch, no run modification, no process killing, no file deletion
3. **Tests each step independently** — open file, acquire lock, write metadata, read back, release lock
4. **Reports each step's result** — success/failure with details, so you can pinpoint exactly which operation fails
5. **Can be run repeatedly** — cleans up after itself, doesn't leave state behind

This pattern catches bugs that only manifest with real OS state (not mocks) and avoids the "fix blindly and retry" cycle.

### Key Functions on Windows
- `os.open(path, os.O_RDWR | os.O_CREAT)` — opens a file descriptor
- `msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)` — acquires non-blocking exclusive lock on byte 0
- `msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)` — releases the lock
- `os.lseek(fd, 0, os.SEEK_SET)` — seek to beginning
- `os.ftruncate(fd, 0)` — truncate to zero bytes
- `os.write(fd, data)` — write bytes through the fd
- `os.fsync(fd)` — flush to disk
- `os.close(fd)` — close the fd (releases the lock)

### Pitfalls
- `Path.write_text()` and `Path.read_text()` both open new handles — they fail with `PermissionError` when the file has an active `msvcrt.locking()` lock
- `os.ftruncate()` is available on Windows in Python 3.8+
- Always close the fd in a `finally` block to release the OS lock
- Test mocks (fake fds like 999) will fail on `os.lseek()` — handle with try/except fallback
- The lock file may be 0 bytes if `_escrever_metadados` failed — this is a symptom, not the root cause
