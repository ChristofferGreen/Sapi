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
seen_comment_user=0
seen_user_alias=0
seen_comment_page=0
seen_page_alias=0
seen_count_flag=0
seen_legacy_count=0

if [[ $# -gt 0 && "${1:0:1}" != "-" ]]; then
  if [[ ! "$1" =~ ^[0-9]+$ ]]; then
    echo "Error: legacy positional count must be a positive integer." >&2
    usage
    exit 2
  fi
  seen_legacy_count=1
  echo "Warning: positional count argument is deprecated; use --count <n>." >&2
  normalized_args+=("--count" "$1")
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --comment-user)
      if [[ $seen_user_alias -eq 1 ]]; then
        echo "Error: cannot combine --comment-user with alias --user" >&2
        usage
        exit 2
      fi
      if [[ $# -lt 2 ]]; then
        echo "Error: --comment-user requires a value." >&2
        usage
        exit 2
      fi
      seen_comment_user=1
      normalized_args+=("--comment-user" "$2")
      shift 2
      ;;
    --user)
      if [[ $seen_comment_user -eq 1 ]]; then
        echo "Error: cannot combine alias --user with --comment-user" >&2
        usage
        exit 2
      fi
      if [[ $# -lt 2 ]]; then
        echo "Error: --user requires a value." >&2
        usage
        exit 2
      fi
      seen_user_alias=1
      echo "Warning: --user is deprecated; use --comment-user." >&2
      normalized_args+=("--comment-user" "$2")
      shift 2
      ;;
    --comment-page)
      if [[ $seen_page_alias -eq 1 ]]; then
        echo "Error: cannot combine --comment-page with alias --page" >&2
        usage
        exit 2
      fi
      if [[ $# -lt 2 ]]; then
        echo "Error: --comment-page requires a value." >&2
        usage
        exit 2
      fi
      seen_comment_page=1
      normalized_args+=("--comment-page" "$2")
      shift 2
      ;;
    --page)
      if [[ $seen_comment_page -eq 1 ]]; then
        echo "Error: cannot combine alias --page with --comment-page" >&2
        usage
        exit 2
      fi
      if [[ $# -lt 2 ]]; then
        echo "Error: --page requires a value." >&2
        usage
        exit 2
      fi
      seen_page_alias=1
      echo "Warning: --page is deprecated; use --comment-page." >&2
      normalized_args+=("--comment-page" "$2")
      shift 2
      ;;
    --count)
      if [[ $seen_legacy_count -eq 1 ]]; then
        echo "Error: cannot combine positional count alias with --count" >&2
        usage
        exit 2
      fi
      if [[ $# -lt 2 ]]; then
        echo "Error: --count requires a value." >&2
        usage
        exit 2
      fi
      seen_count_flag=1
      normalized_args+=("--count" "$2")
      shift 2
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

if [[ $seen_count_flag -eq 0 && $seen_legacy_count -eq 0 ]]; then
  echo "Error: missing required --count <n> (or legacy positional <n>)." >&2
  usage
  exit 2
fi

exec python3 "$script_dir/scripts/create_comments.py" "$space_name" --registry-path "$registry_path" "${normalized_args[@]}"
