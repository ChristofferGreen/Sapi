#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: query.sh <site_path> <space_name> <question> [--verbose]" >&2
}

if [[ $# -lt 3 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
space_name="$2"
question="$3"
shift 3

registry_path="$site_path/spaces.toml"
exec python3 "$script_dir/scripts/query.py" "$space_name" "$question" --registry-path "$registry_path" "$@"
