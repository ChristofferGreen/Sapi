from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from sapi.core.locks import IngestLockHeldError, acquire_ingest_lock, ingest_lock, ingest_lock_path


class IngestLockContractTests(unittest.TestCase):
    def test_exclusive_lock_fails_fast_when_live_holder_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            handle = acquire_ingest_lock(space_root)
            self.addCleanup(handle.release)

            with self.assertRaises(IngestLockHeldError):
                acquire_ingest_lock(space_root)

    def test_stale_lock_with_dead_pid_is_auto_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            lock_path = ingest_lock_path(space_root)
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(
                json.dumps(
                    {
                        "pid": _dead_pid_candidate(),
                        "token": "stale-token",
                        "acquired_at": "2026-04-12T12:00:00Z",
                    }
                )
                + "\n"
            )

            with ingest_lock(space_root):
                payload = json.loads(lock_path.read_text())
                self.assertNotEqual(payload["token"], "stale-token")
                self.assertEqual(payload["pid"], os.getpid())

            self.assertFalse(lock_path.exists())

    def test_lock_is_released_in_finally_when_body_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            lock_path = ingest_lock_path(space_root)
            with self.assertRaisesRegex(RuntimeError, "boom"):
                with ingest_lock(space_root):
                    self.assertTrue(lock_path.exists())
                    raise RuntimeError("boom")
            self.assertFalse(lock_path.exists())


def _dead_pid_candidate() -> int:
    # Pick a value far from current process ID to avoid collisions in ephemeral test hosts.
    return os.getpid() + 10_000_000


if __name__ == "__main__":
    unittest.main()
