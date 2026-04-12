#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: generate_profiles.sh <site_path> <space_name> [--persona-id <persona_id> ...] [--verbose]" >&2
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
exec python3 "$script_dir/scripts/generate_profiles.py" "$space_name" --registry-path "$registry_path" "$@"
