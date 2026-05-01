#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: refresh_questions.sh <site_path> <space_name> [--question-id <id> ...] [--all] [--force] [--build-deferred] [--verbose]" >&2
}

if [[ $# -lt 2 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
space_name="$2"
shift 2

registry_path="$site_path/spaces.toml"

for arg in "$@"; do
  case "$arg" in
    --registry-path)
      echo "Error: refresh_questions.sh manages --registry-path from <site_path>; do not pass it manually." >&2
      usage
      exit 2
      ;;
  esac
done

exec python3 "$script_dir/scripts/refresh_questions.py" "$space_name" --registry-path "$registry_path" "$@"
