#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: create_space.sh <site_path> <space_name> [--seed-example-questions]" >&2
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 2
fi

site_path="$1"
space_name="$2"
seed_example_questions=0
if [[ $# -eq 3 ]]; then
  if [[ "$3" != "--seed-example-questions" ]]; then
    usage
    exit 2
  fi
  seed_example_questions=1
fi
registry_path="$site_path/spaces.toml"
space_root="$site_path/spaces/$space_name"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
example_questions_tsv="$script_dir/tests/example/prepared_questions.tsv"

if [[ ! "$space_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "Error: <space_name> must be lowercase kebab-case." >&2
  usage
  exit 2
fi

mkdir -p \
  "$space_root/sources/records" \
  "$space_root/sources/artifacts" \
  "$space_root/claims" \
  "$space_root/relations" \
  "$space_root/topics" \
  "$space_root/questions" \
  "$space_root/profiles" \
  "$space_root/projections/markdown" \
  "$space_root/runs" \
  "$space_root/outputs/query" \
  "$space_root/outputs/persona_profile_history" \
  "$space_root/outputs/comment_quality" \
  "$space_root/site" \
  "$space_root/raw/snapshots/comment_sections" \
  "$space_root/.locks" \
  "$space_root/.cache"

if [[ ! -f "$space_root/imports.lock.md" ]]; then
  cat > "$space_root/imports.lock.md" <<'MD'
# imports.lock.md
MD
fi

if [[ ! -f "$registry_path" ]]; then
  mkdir -p "$site_path"
  cat > "$registry_path" <<'TOML'
# Sapi space registry bootstrap scaffold
TOML
fi

if ! grep -Eq "^[[:space:]]*(space_name|name)[[:space:]]*=[[:space:]]*\"$space_name\"[[:space:]]*$" "$registry_path"; then
  cat >> "$registry_path" <<TOML

[[spaces]]
space_name = "$space_name"
space_root = "spaces/$space_name"
TOML
fi

if [[ "$seed_example_questions" -eq 1 && -f "$example_questions_tsv" ]] && awk -F '\t' -v space="$space_name" '
  /^[[:space:]]*#/ || /^[[:space:]]*$/ { next }
  $1 == space { found = 1 }
  END { exit found ? 0 : 1 }
' "$example_questions_tsv"; then
  bash "$script_dir/create_questions.sh" "$site_path" "$example_questions_tsv" "$space_name"
fi

printf 'Initialized space scaffold at %s\n' "$space_root"
