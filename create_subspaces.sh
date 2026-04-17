#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: create_subspaces.sh <site_path> <subspaces_tsv>" >&2
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
subspaces_tsv="$2"

if [[ ! -f "$subspaces_tsv" ]]; then
  echo "Error: missing subspaces TSV: $subspaces_tsv" >&2
  exit 2
fi

python3 - "$script_dir" "$site_path" "$subspaces_tsv" <<'PY'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
site_path = Path(sys.argv[2]).resolve()
subspaces_tsv = Path(sys.argv[3]).resolve()

sys.path.insert(0, str(repo_root))
from sapi.core.site_scope import write_subspaces_metadata

rows_by_parent: dict[str, list[dict[str, str]]] = {}
for raw_line in subspaces_tsv.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    parent_slug, _parent_title, child_slug, child_title = line.split("\t")
    rows_by_parent.setdefault(parent_slug, []).append(
        {
            "space_name": child_slug,
            "space_root": str((site_path / "spaces" / child_slug).resolve()),
            "title": child_title,
        }
    )

for parent_slug, rows in rows_by_parent.items():
    write_subspaces_metadata(
        space_root=(site_path / "spaces" / parent_slug),
        subspaces=rows,
    )
PY

printf 'Initialized subspace metadata from %s\n' "$subspaces_tsv"
