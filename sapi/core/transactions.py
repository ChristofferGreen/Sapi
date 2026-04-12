"""Invocation-scoped artifact journaling and rollback helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
        explicit_targets = self.explicit_cleanup_targets()
        for entry in self._entries:
            if entry.backup_path is not None:
                _remove_path(entry.backup_path, explicit_targets=explicit_targets)
        self._entries.clear()
        self._finalized = True

    def rollback(self) -> None:
        """Restore/deletes tracked invocation-scoped writes in reverse order."""
        if self._finalized:
            return

        explicit_targets = self.explicit_cleanup_targets()
        for entry in reversed(self._entries):
            if entry.kind == _JournalKind.REPLACE:
                self._restore_from_backup(
                    path=entry.path,
                    backup_path=entry.backup_path,
                    explicit_targets=explicit_targets,
                )
            elif entry.kind == _JournalKind.DELETE:
                self._restore_from_backup(
                    path=entry.path,
                    backup_path=entry.backup_path,
                    explicit_targets=explicit_targets,
                )
            elif entry.kind == _JournalKind.CREATE:
                _remove_path(entry.path, explicit_targets=explicit_targets)
            elif entry.kind == _JournalKind.MKDIR:
                _remove_path(entry.path, explicit_targets=explicit_targets)

        for entry in self._entries:
            if entry.backup_path is not None:
                _remove_path(entry.backup_path, explicit_targets=explicit_targets)

        self._entries.clear()
        self._finalized = True

    def _restore_from_backup(
        self,
        *,
        path: Path,
        backup_path: Path | None,
        explicit_targets: set[Path],
    ) -> None:
        if backup_path is None or not backup_path.exists():
            _remove_path(path, explicit_targets=explicit_targets)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        _copy_path(src=backup_path, dst=path, explicit_targets=explicit_targets)

    def _require_open(self) -> None:
        if self._finalized:
            raise RuntimeError("Transaction already finalized.")

    def explicit_cleanup_targets(self) -> set[Path]:
        targets: set[Path] = set()
        for entry in self._entries:
            targets.add(entry.path.resolve())
            if entry.backup_path is not None:
                targets.add(entry.backup_path.resolve())
        return targets


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
    explicit_targets = transaction.explicit_cleanup_targets()
    if run_container_path is not None:
        explicit_targets.add(run_container_path.resolve())
    transaction.rollback()
    if run_container_path is not None and run_container_path.exists():
        _remove_path(run_container_path, explicit_targets=explicit_targets)
    removed = bool(existed_before and run_container_path is not None and not run_container_path.exists())

    return TerminalFailureDisposition(
        force_mode=False,
        rollback_applied=True,
        rollback_skipped=False,
        run_container_removed=removed,
    )


def _copy_path(*, src: Path, dst: Path, explicit_targets: set[Path]) -> None:
    _remove_path(dst, explicit_targets=explicit_targets)
    if src.is_dir() and not src.is_symlink():
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _remove_path(path: Path, *, explicit_targets: set[Path]) -> None:
    _validate_safe_delete_target(path, explicit_targets=explicit_targets)
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _validate_safe_delete_target(path: Path, *, explicit_targets: set[Path]) -> None:
    raw = str(path).strip()
    if raw in {"", "."}:
        raise ValueError("Cleanup blocked: empty or current-directory delete target is prohibited.")

    resolved = path.resolve()
    root = Path(resolved.anchor)
    dangerous_targets = {
        root,
        Path.home().resolve(),
        _REPO_ROOT.resolve(),
    }
    if resolved in dangerous_targets:
        raise ValueError(f"Cleanup blocked for dangerous delete target: {resolved}")

    if resolved not in explicit_targets:
        raise ValueError(
            "Cleanup blocked: delete target is outside explicit transaction/run cleanup targets: "
            f"{resolved}"
        )
