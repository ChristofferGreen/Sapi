#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: create_questions.sh <site_path> <questions_tsv> [space_name]" >&2
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
questions_tsv="$2"
space_name="${3:-}"
registry_path="$site_path/spaces.toml"

cmd=(
  python3
  "$script_dir/scripts/create_prepared_questions.py"
  --registry-path "$registry_path"
  --questions-tsv "$questions_tsv"
)
if [[ -n "$space_name" ]]; then
  cmd+=(--space-name "$space_name")
fi

exec "${cmd[@]}"
