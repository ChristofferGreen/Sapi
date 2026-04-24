#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: create_comments.sh <site_path> <space_name> --count <n> [--verbose] [--comment-user ...] [--comment-page ...] [--comment-seed ...] [--comment-evidence-mode ...]" >&2
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

normalized_args=()
seen_count_flag=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --comment-user)
      if [[ $# -lt 2 ]]; then
        echo "Error: --comment-user requires a value." >&2
        usage
        exit 2
      fi
      normalized_args+=("--comment-user" "$2")
      shift 2
      ;;
    --user)
      echo "Error: --user has been removed; use --comment-user." >&2
      usage
      exit 2
      ;;
    --comment-page)
      if [[ $# -lt 2 ]]; then
        echo "Error: --comment-page requires a value." >&2
        usage
        exit 2
      fi
      normalized_args+=("--comment-page" "$2")
      shift 2
      ;;
    --page)
      echo "Error: --page has been removed; use --comment-page." >&2
      usage
      exit 2
      ;;
    --count)
      if [[ $# -lt 2 ]]; then
        echo "Error: --count requires a value." >&2
        usage
        exit 2
      fi
      seen_count_flag=1
      normalized_args+=("--count" "$2")
      shift 2
      ;;
    --comment-web-evidence)
      echo "Error: --comment-web-evidence has been removed; use --comment-evidence-mode web-augmented." >&2
      usage
      exit 2
      ;;
    --llm-backend|--llm-model|--llm-reasoning-effort|--llm-timeout-secs|--llm-trace-dir|--warning-budget|--run-search-visibility|--site-presentation-mode)
      if [[ $# -lt 2 ]]; then
        echo "Error: $1 requires a value." >&2
        usage
        exit 2
      fi
      normalized_args+=("$1" "$2")
      shift 2
      ;;
    --llm-backend=*|--llm-model=*|--llm-reasoning-effort=*|--llm-timeout-secs=*|--llm-trace-dir=*|--warning-budget=*|--run-search-visibility=*|--site-presentation-mode=*)
      normalized_args+=("$1")
      shift
      ;;
    --llm-trace|--trace-llm-io|--mock-llm|--enable-source-index)
      normalized_args+=("$1")
      shift
      ;;
    -*)
      normalized_args+=("$1")
      shift
      ;;
    *)
      echo "Error: unexpected positional argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ $seen_count_flag -eq 0 ]]; then
  echo "Error: missing required --count <n>." >&2
  usage
  exit 2
fi

exec python3 "$script_dir/scripts/create_comments.py" "$space_name" --registry-path "$registry_path" "${normalized_args[@]}"
