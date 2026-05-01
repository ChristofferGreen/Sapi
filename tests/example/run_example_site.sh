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
QUESTIONS_TSV="$SCRIPT_DIR/prepared_questions.tsv"
COMMENT_COUNT=5
STEP_TIMEOUT_SECS=1200
STEP_MAX_ATTEMPTS=10

mkdir -p "$STATE_DIR" "$LOG_DIR"

BOOTSTRAP_DONE=0
INGEST_INDEX=0
OVERVIEW_INDEX=0
COMMENT_INDEX=0
DONE=0
CURRENT_STEP=none
LAST_FAILED_STEP=none
LAST_LOG=none
STEP_ATTEMPT=0

write_status() {
  local tmp="${STATUS_FILE}.tmp"
  cat > "$tmp" <<EOF
BOOTSTRAP_DONE=$BOOTSTRAP_DONE
INGEST_INDEX=$INGEST_INDEX
OVERVIEW_INDEX=$OVERVIEW_INDEX
COMMENT_INDEX=$COMMENT_INDEX
DONE=$DONE
CURRENT_STEP=$CURRENT_STEP
LAST_FAILED_STEP=$LAST_FAILED_STEP
LAST_LOG=$LAST_LOG
STEP_ATTEMPT=$STEP_ATTEMPT
STEP_TIMEOUT_SECS=$STEP_TIMEOUT_SECS
STEP_MAX_ATTEMPTS=$STEP_MAX_ATTEMPTS
EOF
  mv "$tmp" "$STATUS_FILE"
}

load_status() {
  if [[ -f "$STATUS_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$STATUS_FILE"
    : "${STEP_ATTEMPT:=0}"
    : "${STEP_TIMEOUT_SECS:=1200}"
    : "${STEP_MAX_ATTEMPTS:=10}"
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

  local attempt
  local cmd_status=0
  for ((attempt = 1; attempt <= STEP_MAX_ATTEMPTS; attempt++)); do
    STEP_ATTEMPT=$attempt
    write_status

    {
      printf 'attempt=%s/%s\n' "$attempt" "$STEP_MAX_ATTEMPTS"
      printf 'timeout_secs=%s\n' "$STEP_TIMEOUT_SECS"
      printf 'attempt_started_at=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    } >> "$step_log"

    local status_file
    status_file="$(mktemp "$STATE_DIR/.${step_id}.status.XXXXXX")"

    set +e
    perl -e '
      use strict;
      use warnings;
      use POSIX qw(setsid WNOHANG);

      my ($timeout, $status_path, @cmd) = @ARGV;
      my $pid = fork();
      die "fork failed: $!\n" unless defined $pid;

      if ($pid == 0) {
        setsid() or die "setsid failed: $!\n";
        exec @cmd or die "exec failed: $!\n";
      }

      my $result;
      while (1) {
        my $done = waitpid($pid, WNOHANG);
        if ($done == $pid) {
          $result = $? >> 8;
          last;
        }
        if ($done == -1) {
          $result = 1;
          last;
        }
        if ($timeout <= 0) {
          sleep 1;
          next;
        }
        if (--$timeout <= 0) {
          kill q(TERM), -$pid;
          sleep 5;
          kill q(KILL), -$pid;
          waitpid($pid, 0);
          $result = 124;
          last;
        }
        sleep 1;
      }

      open my $fh, q(>), $status_path or die "open status file failed: $!\n";
      print {$fh} $result;
      close $fh or die "close status file failed: $!\n";
    ' "$STEP_TIMEOUT_SECS" "$status_file" bash -lc \
      "cd $(printf '%q' "$REPO_ROOT") && exec $(printf '%q ' "$@")" \
      2>&1 | tee -a "$step_log"
    cmd_status=$(cat "$status_file")
    rm -f "$status_file"
    set -e

    printf 'attempt_exit_status=%s\n\n' "$cmd_status" >> "$step_log"

    if [[ $cmd_status -eq 0 ]]; then
      break
    fi

    if [[ $cmd_status -eq 124 && $attempt -lt STEP_MAX_ATTEMPTS ]]; then
      log "step timed out after ${STEP_TIMEOUT_SECS}s: $step_id (attempt $attempt/$STEP_MAX_ATTEMPTS)"
      printf 'timeout_retry=1\n\n' >> "$step_log"
      continue
    fi

    break
  done

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

  STEP_ATTEMPT=0
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

  run_step "003-seed-prepared-questions" \
    bash "$REPO_ROOT/create_questions.sh" "$SITE_PATH" "$QUESTIONS_TSV"

  BOOTSTRAP_DONE=1
  write_status
}

load_tsv_rows() {
  local tsv_path="$1"
  grep -v '^[[:space:]]*#' "$tsv_path" | sed '/^[[:space:]]*$/d'
}

collect_comment_page_rows() {
  local space_slug="$1"
  local space_root="$SITE_PATH/spaces/$space_slug"
  local page_refs=()
  local path

  if [[ -d "$space_root/topics" ]]; then
    while IFS= read -r path; do
      [[ -n "$path" ]] || continue
      page_refs+=("topic:${path##*/}")
    done < <(
      find "$space_root/topics" -maxdepth 1 -type f -name '*.json' ! -name '.*' -print \
        | sed 's#\.json$##' \
        | sort
    )
  fi

  if [[ -d "$space_root/sources/records" ]]; then
    while IFS= read -r path; do
      [[ -n "$path" ]] || continue
      page_refs+=("source:${path##*/}")
    done < <(
      find "$space_root/sources/records" -maxdepth 1 -type f -name '*.json' -print \
        | sed 's#\.json$##' \
        | sort
    )
  fi

  if [[ ${#page_refs[@]} -eq 0 ]]; then
    return 0
  fi

  printf '%s\n' "${page_refs[@]}" | sort | while IFS= read -r page_ref; do
    [[ -n "$page_ref" ]] || continue
    printf '%s\t%s\n' "$space_slug" "$page_ref"
  done
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

mapfile -t WORK_SPACES < <(
  while IFS=$'\t' read -r _parent_slug _parent_title child_slug _child_title; do
    printf '%s\n' "$child_slug"
  done < <(printf '%s\n' "${SUBSPACE_ROWS[@]}") | awk '!seen[$0]++'
)

while [[ $OVERVIEW_INDEX -lt ${#WORK_SPACES[@]} ]]; do
  space_slug="${WORK_SPACES[$OVERVIEW_INDEX]}"
  run_step "overview-${space_slug}" \
    bash "$REPO_ROOT/generate_overview.sh" \
      "$SITE_PATH" \
      "$space_slug" \
      --verbose
  OVERVIEW_INDEX=$((OVERVIEW_INDEX + 1))
  write_status
done

COMMENT_PAGE_ROWS=()
for space_slug in "${WORK_SPACES[@]}"; do
  while IFS= read -r row; do
    [[ -n "$row" ]] || continue
    COMMENT_PAGE_ROWS+=("$row")
  done < <(collect_comment_page_rows "$space_slug")
done

while [[ $COMMENT_INDEX -lt ${#COMMENT_PAGE_ROWS[@]} ]]; do
  IFS=$'\t' read -r space_slug page_ref <<< "${COMMENT_PAGE_ROWS[$COMMENT_INDEX]}"
  page_ref_key="${page_ref//:/-}"
  run_step "comments-${space_slug}-${page_ref_key}" \
    bash "$REPO_ROOT/create_comments.sh" \
      "$SITE_PATH" \
      "$space_slug" \
      --comment-page "$page_ref" \
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
