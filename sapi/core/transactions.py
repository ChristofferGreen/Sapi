"""Invocation-scoped artifact journaling and rollback helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil


class _JournalKind(str, Enum):
    CREATE = "create"
    REPLACE = "replace"
    DELETE = "delete"
    MKDIR = "mkdir"


@dataclass(frozen=True)
class _JournalEntry:
    kind: _JournalKind
    path: Path
    backup_path: Path | None = None


@dataclass(frozen=True)
class TerminalFailureDisposition:
    """Rollback/retention decision for one terminal pipeline failure."""

    force_mode: bool
    rollback_applied: bool
    rollback_skipped: bool
    run_container_removed: bool


class ArtifactTransaction:
    """Track invocation-scoped filesystem mutations for rollback/commit."""

    def __init__(self) -> None:
        self._entries: list[_JournalEntry] = []
        self._finalized = False

    def mark_create(self, path: Path) -> None:
        self._require_open()
        self._entries.append(_JournalEntry(kind=_JournalKind.CREATE, path=path))

    def mark_replace(self, path: Path, backup_path: Path) -> None:
        self._require_open()
        self._entries.append(
            _JournalEntry(kind=_JournalKind.REPLACE, path=path, backup_path=backup_path)
        )

    def mark_delete(self, path: Path, backup_path: Path) -> None:
        self._require_open()
        self._entries.append(
            _JournalEntry(kind=_JournalKind.DELETE, path=path, backup_path=backup_path)
        )

    def mark_mkdir(self, path: Path) -> None:
        self._require_open()
        self._entries.append(_JournalEntry(kind=_JournalKind.MKDIR, path=path))

    def commit(self) -> None:
        """Finalize successful invocation and discard rollback backups."""
        self._require_open()
        for entry in self._entries:
            if entry.backup_path is not None:
                _remove_path(entry.backup_path)
        self._entries.clear()
        self._finalized = True

    def rollback(self) -> None:
        """Restore/deletes tracked invocation-scoped writes in reverse order."""
        if self._finalized:
            return

        for entry in reversed(self._entries):
            if entry.kind == _JournalKind.REPLACE:
                self._restore_from_backup(path=entry.path, backup_path=entry.backup_path)
            elif entry.kind == _JournalKind.DELETE:
                self._restore_from_backup(path=entry.path, backup_path=entry.backup_path)
            elif entry.kind == _JournalKind.CREATE:
                _remove_path(entry.path)
            elif entry.kind == _JournalKind.MKDIR:
                _remove_path(entry.path)

        for entry in self._entries:
            if entry.backup_path is not None:
                _remove_path(entry.backup_path)

        self._entries.clear()
        self._finalized = True

    def _restore_from_backup(self, *, path: Path, backup_path: Path | None) -> None:
        if backup_path is None or not backup_path.exists():
            _remove_path(path)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        _copy_path(src=backup_path, dst=path)

    def _require_open(self) -> None:
        if self._finalized:
            raise RuntimeError("Transaction already finalized.")


def apply_terminal_failure_policy(
    *,
    transaction: ArtifactTransaction,
    pipeline_flow_key: str,
    force_mode: bool,
    run_container_path: Path | None,
) -> TerminalFailureDisposition:
    """Apply default rollback or ingest force-mode retention on terminal failure."""
    if force_mode and pipeline_flow_key != "ingest_pipeline":
        raise ValueError("`--force` rollback override is ingest-only.")

    if force_mode and pipeline_flow_key == "ingest_pipeline":
        return TerminalFailureDisposition(
            force_mode=True,
            rollback_applied=False,
            rollback_skipped=True,
            run_container_removed=False,
        )

    existed_before = run_container_path is not None and run_container_path.exists()
    transaction.rollback()
    if run_container_path is not None and run_container_path.exists():
        _remove_path(run_container_path)
    removed = bool(existed_before and run_container_path is not None and not run_container_path.exists())

    return TerminalFailureDisposition(
        force_mode=False,
        rollback_applied=True,
        rollback_skipped=False,
        run_container_removed=removed,
    )


def _copy_path(*, src: Path, dst: Path) -> None:
    _remove_path(dst)
    if src.is_dir() and not src.is_symlink():
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
