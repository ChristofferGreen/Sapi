#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: evaluate_source.sh <site_path> <space_name> <source_path_or_url> [--out <artifact_dir>] [--comments <n>] [--comment-user ...] [--comment-page ...] [--verbose]" >&2
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
exec python3 "$script_dir/scripts/evaluate_source.py" "$space_name" "$source_path_or_url" --registry-path "$registry_path" "$@"
