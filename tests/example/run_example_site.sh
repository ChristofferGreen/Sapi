#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: run_example_site.sh <site_path>" >&2
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SITE_PATH_INPUT="$1"
mkdir -p "$SITE_PATH_INPUT"
SITE_PATH="$(cd "$SITE_PATH_INPUT" && pwd -P)"
SITE_NAME="Example Site"
REGISTRY_PATH="$SITE_PATH/spaces.toml"
STATE_DIR="$SITE_PATH/example_runner"
LOG_DIR="$STATE_DIR/logs"
STATUS_FILE="$STATE_DIR/status.env"
SUBSPACES_TSV="$SCRIPT_DIR/subspaces.tsv"
INGEST_PLAN_TSV="$SCRIPT_DIR/ingest_plan.tsv"
COMMENT_COUNT=5

mkdir -p "$STATE_DIR" "$LOG_DIR"

BOOTSTRAP_DONE=0
INGEST_INDEX=0
COMMENT_INDEX=0
DONE=0
CURRENT_STEP=none
LAST_FAILED_STEP=none
LAST_LOG=none

write_status() {
  local tmp="${STATUS_FILE}.tmp"
  cat > "$tmp" <<EOF
BOOTSTRAP_DONE=$BOOTSTRAP_DONE
INGEST_INDEX=$INGEST_INDEX
COMMENT_INDEX=$COMMENT_INDEX
DONE=$DONE
CURRENT_STEP=$CURRENT_STEP
LAST_FAILED_STEP=$LAST_FAILED_STEP
LAST_LOG=$LAST_LOG
EOF
  mv "$tmp" "$STATUS_FILE"
}

load_status() {
  if [[ -f "$STATUS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$STATUS_FILE"
  else
    write_status
  fi
}

log() {
  printf '[example-runner] %s\n' "$*"
}

run_step() {
  local step_id="$1"
  shift

  local step_log="$LOG_DIR/${step_id}.log"
  local before_file="$LOG_DIR/${step_id}.traces.before"
  local after_file="$LOG_DIR/${step_id}.traces.after"
  local diff_file="$LOG_DIR/${step_id}.traces.txt"

  CURRENT_STEP="$step_id"
  LAST_FAILED_STEP="$step_id"
  LAST_LOG="$step_log"
  write_status

  mkdir -p "$SITE_PATH/outputs/llm_traces"
  find "$SITE_PATH/outputs/llm_traces" -mindepth 1 -maxdepth 1 -type d | sort > "$before_file"

  {
    printf 'step=%s\n' "$step_id"
    printf 'started_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'cwd=%s\n' "$REPO_ROOT"
    printf 'command='
    printf '%q ' "$@"
    printf '\n\n'
  } > "$step_log"

  set +e
  (
    cd "$REPO_ROOT"
    "$@"
  ) 2>&1 | tee -a "$step_log"
  local cmd_status=${PIPESTATUS[0]}
  set -e

  find "$SITE_PATH/outputs/llm_traces" -mindepth 1 -maxdepth 1 -type d | sort > "$after_file"
  comm -13 "$before_file" "$after_file" > "$diff_file" || true

  if [[ -s "$diff_file" ]]; then
    {
      printf '\ntrace_directories_created:\n'
      cat "$diff_file"
      printf '\ntrace_artifacts:\n'
      while IFS= read -r trace_dir; do
        [[ -n "$trace_dir" ]] || continue
        printf 'trace_dir=%s\n' "$trace_dir"
        printf 'prompt_file=%s/semantic.prompt.txt\n' "$trace_dir"
        printf 'reasoning_stdout_file=%s/semantic.codex.stdout.jsonl\n' "$trace_dir"
        printf 'stderr_file=%s/semantic.codex.stderr.txt\n' "$trace_dir"
      done < "$diff_file"
    } >> "$step_log"
  fi

  if [[ $cmd_status -ne 0 ]]; then
    printf '\nexit_status=%s\n' "$cmd_status" >> "$step_log"
    write_status
    log "step failed: $step_id"
    log "see: $step_log"
    if [[ -s "$diff_file" ]]; then
      log "new llm traces listed in: $diff_file"
    fi
    exit "$cmd_status"
  fi

  LAST_FAILED_STEP=none
  write_status
}

bootstrap_site() {
  run_step "000-create-site" bash "$REPO_ROOT/create_site.sh" "$SITE_PATH" "$SITE_NAME"

  local parent_seen=""
  local child_seen=""
  while IFS=$'\t' read -r parent_slug _parent_title child_slug _child_title; do
    [[ -n "${parent_slug:-}" ]] || continue
    [[ "${parent_slug:0:1}" == "#" ]] && continue

    if [[ " $parent_seen " != *" $parent_slug "* ]]; then
      run_step "001-space-${parent_slug}" bash "$REPO_ROOT/create_space.sh" "$SITE_PATH" "$parent_slug"
      parent_seen+=" $parent_slug"
    fi

    if [[ " $child_seen " != *" $child_slug "* ]]; then
      run_step "001-space-${child_slug}" bash "$REPO_ROOT/create_space.sh" "$SITE_PATH" "$child_slug"
      child_seen+=" $child_slug"
    fi
  done < "$SUBSPACES_TSV"

  run_step "002-write-subspaces" \
    bash "$REPO_ROOT/create_subspaces.sh" "$SITE_PATH" "$SUBSPACES_TSV"

  BOOTSTRAP_DONE=1
  write_status
}

load_tsv_rows() {
  local tsv_path="$1"
  grep -v '^[[:space:]]*#' "$tsv_path" | sed '/^[[:space:]]*$/d'
}

load_status

if [[ $DONE -eq 1 ]]; then
  log "example site run already completed"
  log "status file: $STATUS_FILE"
  exit 0
fi

if [[ $BOOTSTRAP_DONE -eq 0 ]]; then
  bootstrap_site
fi

mapfile -t INGEST_ROWS < <(load_tsv_rows "$INGEST_PLAN_TSV")
mapfile -t SUBSPACE_ROWS < <(load_tsv_rows "$SUBSPACES_TSV")

while [[ $INGEST_INDEX -lt ${#INGEST_ROWS[@]} ]]; do
  IFS=$'\t' read -r step_id space_slug pdf_relpath <<< "${INGEST_ROWS[$INGEST_INDEX]}"
  pdf_path="$SCRIPT_DIR/$pdf_relpath"
  if [[ ! -f "$pdf_path" ]]; then
    log "missing PDF for ingest step $step_id: $pdf_path"
    exit 2
  fi
  run_step "ingest-${step_id}-${space_slug}" \
    bash "$REPO_ROOT/ingest.sh" \
      "$SITE_PATH" \
      "$space_slug" \
      "$pdf_path" \
      --verbose
  INGEST_INDEX=$((INGEST_INDEX + 1))
  write_status
done

mapfile -t COMMENT_SPACES < <(
  while IFS=$'\t' read -r _parent_slug _parent_title child_slug _child_title; do
    printf '%s\n' "$child_slug"
  done < <(printf '%s\n' "${SUBSPACE_ROWS[@]}") | awk '!seen[$0]++'
)

while [[ $COMMENT_INDEX -lt ${#COMMENT_SPACES[@]} ]]; do
  space_slug="${COMMENT_SPACES[$COMMENT_INDEX]}"
  run_step "comments-${space_slug}" \
    bash "$REPO_ROOT/create_comments.sh" \
      "$SITE_PATH" \
      "$space_slug" \
      --count "$COMMENT_COUNT" \
      --verbose
  COMMENT_INDEX=$((COMMENT_INDEX + 1))
  write_status
done

DONE=1
CURRENT_STEP=done
LAST_FAILED_STEP=none
write_status

log "example site completed"
log "status file: $STATUS_FILE"
log "command logs: $LOG_DIR"
log "llm traces: $SITE_PATH/outputs/llm_traces"
