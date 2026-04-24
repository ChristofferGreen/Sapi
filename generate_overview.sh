#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: generate_overview.sh <site_path> <space_name> [--force] [--verbose]" >&2
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
exec python3 "$script_dir/scripts/generate_overview.py" "$space_name" --registry-path "$registry_path" "$@"
