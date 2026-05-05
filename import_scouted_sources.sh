#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: import_scouted_sources.sh <site_path> <space_name> [--count n] [--question-id id] [--mock-llm] [--verbose]" >&2
}

if [[ $# -lt 2 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
space_name="$2"
shift 2

exec python3 "$script_dir/scripts/import_scouted_sources.py" \
  "$space_name" \
  --registry-path "$site_path/spaces.toml" \
  "$@"
