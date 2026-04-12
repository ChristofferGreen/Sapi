#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: regenerate_web.sh <site_path> [space_name] [--verbose] [--site-presentation-mode <public|debug>]" >&2
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_path="$1"
shift

space_name=""
if [[ $# -gt 0 && "$1" != -* ]]; then
  space_name="$1"
  shift
fi

normalized_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose)
      normalized_args+=("--verbose")
      shift
      ;;
    --site-presentation-mode)
      if [[ $# -lt 2 ]]; then
        echo "Error: --site-presentation-mode requires a value." >&2
        usage
        exit 2
      fi
      if [[ "$2" != "public" && "$2" != "debug" ]]; then
        echo "Error: --site-presentation-mode must be 'public' or 'debug'." >&2
        usage
        exit 2
      fi
      normalized_args+=("--site-presentation-mode" "$2")
      shift 2
      ;;
    --site-presentation-mode=*)
      mode_value="${1#*=}"
      if [[ "$mode_value" != "public" && "$mode_value" != "debug" ]]; then
        echo "Error: --site-presentation-mode must be 'public' or 'debug'." >&2
        usage
        exit 2
      fi
      normalized_args+=("--site-presentation-mode" "$mode_value")
      shift
      ;;
    --registry-path|--registry-path=*)
      echo "Error: --registry-path is wrapper-managed and cannot be overridden." >&2
      usage
      exit 2
      ;;
    -*)
      echo "Error: unknown flag: $1" >&2
      usage
      exit 2
      ;;
    *)
      echo "Error: unexpected positional argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

registry_path="$site_path/spaces.toml"
cmd=(python3 "$script_dir/scripts/build_site.py" --workflow-key build_site --registry-path "$registry_path")
if [[ -n "$space_name" ]]; then
  cmd+=("$space_name")
fi
cmd+=("${normalized_args[@]}")

exec "${cmd[@]}"
