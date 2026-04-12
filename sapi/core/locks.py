"""Ingest lock primitives with stale-lock recovery and finally-safe release."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
import errno
import json
import os
from pathlib import Path
import secrets
from typing import Iterator


_INGEST_LOCK_FILENAME = "ingest.lock"


class IngestLockError(RuntimeError):
    """Base lock error for ingest lock operations."""


class IngestLockHeldError(IngestLockError):
    """Raised when a live ingest lock holder is detected."""


@dataclass(frozen=True)
class IngestLockState:
    """Decoded lock payload persisted in `<space_root>/.locks/ingest.lock`."""

    pid: int
    token: str
    acquired_at: str


@dataclass
class IngestLockHandle:
    """Lock handle returned by `acquire_ingest_lock`."""

    lock_path: Path
    token: str
    released: bool = False

    def release(self) -> None:
        if self.released:
            return
        self.released = True
        _release_lock_file(lock_path=self.lock_path, expected_token=self.token)


def ingest_lock_path(space_root: Path) -> Path:
    """Return canonical ingest lock path for one space root."""
    return space_root / ".locks" / _INGEST_LOCK_FILENAME


def acquire_ingest_lock(space_root: Path) -> IngestLockHandle:
    """Acquire exclusive ingest lock with stale-lock recovery."""
    lock_path = ingest_lock_path(space_root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    token = _new_lock_token()

    while True:
        try:
            fd = os.open(
                str(lock_path),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644,
            )
        except FileExistsError as exc:
            state = _read_lock_state(lock_path)
            if state is not None and _is_pid_alive(state.pid):
                raise IngestLockHeldError(
                    f"Ingest lock is already held by live pid {state.pid}: {lock_path}"
                ) from exc
            _safe_unlink(lock_path)
            continue

        state = IngestLockState(
            pid=os.getpid(),
            token=token,
            acquired_at=_utc_now_rfc3339(),
        )
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "pid": state.pid,
                    "token": state.token,
                    "acquired_at": state.acquired_at,
                },
                handle,
                sort_keys=True,
            )
            handle.write("\n")
        return IngestLockHandle(lock_path=lock_path, token=token)


@contextmanager
def ingest_lock(space_root: Path) -> Iterator[IngestLockHandle]:
    """Context manager that always releases ingest lock on exit."""
    handle = acquire_ingest_lock(space_root)
    try:
        yield handle
    finally:
        handle.release()


def _release_lock_file(*, lock_path: Path, expected_token: str) -> None:
    if not lock_path.exists():
        return

    state = _read_lock_state(lock_path)
    if state is None:
        _safe_unlink(lock_path)
        return

    # Do not remove lock files that were replaced by another holder.
    if state.token != expected_token:
        return
    _safe_unlink(lock_path)


def _read_lock_state(lock_path: Path) -> IngestLockState | None:
    if not lock_path.is_file():
        return None

    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None

    pid = payload.get("pid")
    token = payload.get("token")
    acquired_at = payload.get("acquired_at")
    if (
        not isinstance(pid, int)
        or pid <= 0
        or not isinstance(token, str)
        or not token.strip()
        or not isinstance(acquired_at, str)
        or not acquired_at.strip()
    ):
        return None
    return IngestLockState(pid=pid, token=token, acquired_at=acquired_at)


def _is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        return True
    return True


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _new_lock_token() -> str:
    return secrets.token_hex(16)


def _utc_now_rfc3339() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
