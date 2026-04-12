#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ingest.sh <site_path> <space_name> <source_path_or_url> [--source-only] [--force] [--verbose]" >&2
}

if [[ $# -lt 3 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
space_name="$2"
source_path_or_url="$3"
shift 3

registry_path="$site_path/spaces.toml"

normalized_args=()
seen_source_only=0
seen_query_only=0

for arg in "$@"; do
  case "$arg" in
    --source-only)
      if [[ $seen_query_only -eq 1 ]]; then
        echo "Error: cannot combine --source-only with alias --query-only" >&2
        usage
        exit 2
      fi
      seen_source_only=1
      normalized_args+=("--source-only")
      ;;
    --query-only)
      if [[ $seen_source_only -eq 1 ]]; then
        echo "Error: cannot combine --source-only with alias --query-only" >&2
        usage
        exit 2
      fi
      seen_query_only=1
      echo "Warning: --query-only is deprecated; use --source-only." >&2
      normalized_args+=("--source-only")
      ;;
    *)
      normalized_args+=("$arg")
      ;;
  esac
done

exec python3 "$script_dir/scripts/ingest_source.py" "$space_name" "$source_path_or_url" --registry-path "$registry_path" "${normalized_args[@]}"
