#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: scout_sources.sh <site_path> <space_name> <question_id> [--count n] [--mock-llm] [--mock-candidate-plan <path>] [--verbose]" >&2
}

if [[ $# -lt 3 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
space_name="$2"
question_id="$3"
shift 3

exec python3 "$script_dir/scripts/scout_sources.py" \
  "$space_name" \
  "$question_id" \
  --registry-path "$site_path/spaces.toml" \
  "$@"
