#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ingest.sh <site_path> <space_name> <source_path_or_url> [--revises-source-id <source_id>] [--force] [--verbose]" >&2
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

for arg in "$@"; do
  case "$arg" in
    --source-only|--query-only)
      echo "Error: $arg has been removed; ingest now always runs semantic extraction and topic generation." >&2
      usage
      exit 2
      ;;
    *)
      normalized_args+=("$arg")
      ;;
  esac
done

exec python3 "$script_dir/scripts/ingest_source.py" "$space_name" "$source_path_or_url" --registry-path "$registry_path" "${normalized_args[@]}"
