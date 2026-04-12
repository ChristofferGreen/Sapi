#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: create_site.sh <site_path> <site_name>" >&2
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

site_path="$1"
site_name="$2"

mkdir -p "$site_path/config" "$site_path/spaces" "$site_path/outputs/llm_traces"

if [[ ! -f "$site_path/site.json" ]]; then
  python3 - "$site_name" "$site_path/site.json" <<'PY'
import json
import sys
from pathlib import Path

site_name = sys.argv[1]
site_json_path = Path(sys.argv[2])
payload = {
    "schema_version": "site_scope_v1",
    "site_name": site_name,
    "site_root": ".",
}
site_json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
PY
fi

if [[ ! -f "$site_path/spaces.toml" ]]; then
  cat > "$site_path/spaces.toml" <<'TOML'
# Sapi space registry bootstrap scaffold
TOML
fi

if [[ ! -f "$site_path/config/discussion_controls.json" ]]; then
  cat > "$site_path/config/discussion_controls.json" <<'JSON'
{
  "schema_version": "comment_section_discussion_controls_v1",
  "defaults": {},
  "pages": {}
}
JSON
fi

printf 'Initialized site scaffold at %s\n' "$site_path"
