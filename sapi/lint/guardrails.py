"""Automated anti-drift guardrail checks from low-level Sections 14.1 and 14.3."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from sapi.contracts.semantic_specs import FLOW_MAP
from sapi.core.runtime_policy import DISALLOWED_FLOW_ENV_VARS


@dataclass(frozen=True)
class GuardrailIssue:
    check_id: str
    path: Path
    line: int
    message: str


_REGISTRY_FALLBACK_PATTERN = re.compile(r"(~\/\.sapi\/spaces\.toml|\.sapi\/spaces\.toml)")
_CANONICAL_KNOWLEDGE_SEGMENT_PATTERN = re.compile(
    r"""["'](?:sources|claims|relations|topics|profiles)(?:/|["'])"""
)

_WRITE_INTENT_TOKENS: tuple[str, ...] = (
    ".write_text(",
    ".write_bytes(",
    ".open(",
    "open(",
    "os.replace(",
    ".mkdir(",
    ".rename(",
)

_PIPELINE_AFFECTING_PATH_PREFIXES: tuple[str, ...] = (
    "sapi/ingest/",
    "sapi/query/",
    "sapi/comments/",
    "sapi/profiles/",
    "sapi/build/",
    "scripts/ingest_source.py",
    "scripts/query.py",
    "scripts/create_comments.py",
    "scripts/generate_profiles.py",
    "scripts/build_site.py",
    "scripts/evaluate_source.py",
    "ingest.sh",
    "query.sh",
    "create_comments.sh",
    "generate_profiles.sh",
    "regenerate_web.sh",
    "evaluate_source.sh",
)

_PIPELINE_CHECKLIST_REQUIRED_QUESTIONS: tuple[str, ...] = (
    "Q1 Which canonical artifacts can this command mutate?",
    "Q2 Which semantic flow keys can run, and in what order?",
    "Q3 What exactly is rolled back on terminal failure?",
    "Q4 Does run envelope include correct `flow_key`, ordered-unique `semantic_flows[]`, `semantic_flow_invocation_counts`, and required extension fields?",
    "Q5 Are manifest outputs conditional by query format as required?",
    "Q6 Are comments default-target rules, count bounds, and `comment_uid` stability preserved?",
    "Q7 Are profile/history links canonical in rendered output?",
    "Q8 Are site-root `New` refresh decisions correct for this flow?",
)
_PIPELINE_CHECKLIST_DOCS_SYNC_ITEM = (
    "Docs Sync: Contract-level changes follow `design.md` -> `low_level.md` -> code/tests order"
)
_CANONICAL_SPACE_ROOT_HINT = "space_root"
_INGEST_CANONICAL_WRITE_OWNERSHIP_PREFIXES: tuple[str, ...] = (
    "sapi/ingest/",
    "scripts/ingest_source.py",
)


def run_guardrail_checks(repo_root: Path) -> list[GuardrailIssue]:
    """Run repository anti-drift checks and return all discovered issues."""
    repo_root = repo_root.resolve()
    issues: list[GuardrailIssue] = []
    issues.extend(_check_registry_fallback_literals(repo_root))
    issues.extend(_check_env_flow_controls(repo_root))
    issues.extend(_check_semantic_contract_duplication(repo_root))
    issues.extend(_check_canonical_mutation_ownership(repo_root))
    issues.extend(_check_query_canonical_mutation_patterns(repo_root))
    return sorted(
        issues,
        key=lambda issue: (issue.check_id, str(issue.path), issue.line, issue.message),
    )


def evaluate_pipeline_pr_evidence(
    *,
    repo_root: Path,
    changed_files: list[str],
    checklist_path: str | None,
) -> list[GuardrailIssue]:
    """Validate pipeline-change PR checklist evidence for quality-gate use."""
    repo_root = repo_root.resolve()
    normalized_paths = [path.strip() for path in changed_files if path.strip()]
    pipeline_paths = [path for path in normalized_paths if _is_pipeline_affecting_path(path)]
    if not pipeline_paths:
        return []

    if checklist_path is None or not checklist_path.strip():
        return [
            GuardrailIssue(
                check_id="pipeline_pr_checklist_missing",
                path=repo_root,
                line=1,
                message=(
                    "Pipeline-affecting changes require --pipeline-pr-checklist evidence with completed "
                    "review questions and docs-sync confirmation."
                ),
            )
        ]

    resolved_checklist_path = Path(checklist_path).expanduser()
    if not resolved_checklist_path.is_absolute():
        resolved_checklist_path = (repo_root / resolved_checklist_path).resolve()
    else:
        resolved_checklist_path = resolved_checklist_path.resolve()

    if not resolved_checklist_path.is_file():
        return [
            GuardrailIssue(
                check_id="pipeline_pr_checklist_missing",
                path=resolved_checklist_path,
                line=1,
                message="Pipeline PR checklist evidence file not found.",
            )
        ]

    lines = resolved_checklist_path.read_text().splitlines()
    issues: list[GuardrailIssue] = []
    for prompt in _PIPELINE_CHECKLIST_REQUIRED_QUESTIONS + (_PIPELINE_CHECKLIST_DOCS_SYNC_ITEM,):
        line_no = _find_line_containing(lines, prompt)
        if line_no is None:
            issues.append(
                GuardrailIssue(
                    check_id="pipeline_pr_checklist_incomplete",
                    path=resolved_checklist_path,
                    line=1,
                    message=f"Missing checklist evidence item: {prompt}",
                )
            )
            continue
        if not _is_checked_line(lines[line_no - 1]):
            issues.append(
                GuardrailIssue(
                    check_id="pipeline_pr_checklist_incomplete",
                    path=resolved_checklist_path,
                    line=line_no,
                    message=f"Checklist item must be checked '[x]': {prompt}",
                )
            )
    return issues


def _iter_code_files(repo_root: Path) -> list[Path]:
    roots = (
        repo_root / "sapi",
        repo_root / "scripts",
    )
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix == ".py")
    for wrapper in repo_root.glob("*.sh"):
        if wrapper.is_file():
            files.append(wrapper)
    return sorted(set(path.resolve() for path in files))


def _check_registry_fallback_literals(repo_root: Path) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    for path in _iter_code_files(repo_root):
        for line_no, line in enumerate(path.read_text().splitlines(), start=1):
            if _REGISTRY_FALLBACK_PATTERN.search(line):
                issues.append(
                    GuardrailIssue(
                        check_id="registry_fallback",
                        path=path,
                        line=line_no,
                        message="Implicit registry fallback is prohibited; require explicit --registry-path.",
                    )
                )
    return issues


def _check_env_flow_controls(repo_root: Path) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    runtime_policy_path = (repo_root / "sapi" / "core" / "runtime_policy.py").resolve()
    for path in _iter_code_files(repo_root):
        if path == runtime_policy_path:
            continue
        lines = path.read_text().splitlines()
        for line_no, line in enumerate(lines, start=1):
            for env_key in DISALLOWED_FLOW_ENV_VARS:
                if env_key in line:
                    issues.append(
                        GuardrailIssue(
                            check_id="env_flow_control",
                            path=path,
                            line=line_no,
                            message=(
                                f"Flow behavior env var `{env_key}` must not be read outside runtime-policy guardrails."
                            ),
                        )
                    )
    return issues


def _check_semantic_contract_duplication(repo_root: Path) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    allowed_paths = {
        (repo_root / "sapi" / "contracts" / "semantic_specs.py").resolve(),
    }
    protected_fragments: set[str] = set()
    for entry in FLOW_MAP.values():
        protected_fragments.add(entry.spec_relpath)
        protected_fragments.add(entry.schema_relpath)
        protected_fragments.add(entry.output_json_path_template)

    for path in _iter_code_files(repo_root):
        if path in allowed_paths:
            continue
        lines = path.read_text().splitlines()
        for line_no, line in enumerate(lines, start=1):
            for fragment in protected_fragments:
                if fragment in line:
                    issues.append(
                        GuardrailIssue(
                            check_id="semantic_contract_duplication",
                            path=path,
                            line=line_no,
                            message=(
                                "Semantic schema/output/spec ownership is duplicated outside "
                                "sapi/contracts/semantic_specs.py."
                            ),
                        )
                    )
    return issues


def _check_query_canonical_mutation_patterns(repo_root: Path) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    query_paths: list[Path] = []
    query_pkg = repo_root / "sapi" / "query"
    if query_pkg.exists():
        query_paths.extend(path for path in query_pkg.rglob("*.py") if path.is_file())
    query_entrypoint = repo_root / "scripts" / "query.py"
    if query_entrypoint.exists():
        query_paths.append(query_entrypoint)

    for path in sorted(set(path.resolve() for path in query_paths)):
        text = path.read_text()
        if not any(token in text for token in _WRITE_INTENT_TOKENS):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _CANONICAL_KNOWLEDGE_SEGMENT_PATTERN.search(line):
                issues.append(
                    GuardrailIssue(
                        check_id="query_canonical_mutation",
                        path=path,
                        line=line_no,
                        message=(
                            "Query flow must not target canonical sources/claims/relations/topics/profiles paths."
                        ),
                    )
                )
    return issues


def _check_canonical_mutation_ownership(repo_root: Path) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    for path in _iter_code_files(repo_root):
        text = path.read_text()
        if not any(token in text for token in _WRITE_INTENT_TOKENS):
            continue
        relpath = path.resolve().relative_to(repo_root.resolve()).as_posix()
        if any(relpath.startswith(prefix) for prefix in _INGEST_CANONICAL_WRITE_OWNERSHIP_PREFIXES):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _CANONICAL_KNOWLEDGE_SEGMENT_PATTERN.search(line) and _CANONICAL_SPACE_ROOT_HINT in line:
                issues.append(
                    GuardrailIssue(
                        check_id="canonical_mutation_ownership",
                        path=path,
                        line=line_no,
                        message=(
                            "Canonical sources/claims/relations/topics/profiles mutations are ingest-owned "
                            "and must not be written from non-ingest components."
                        ),
                    )
                )
    return issues


def _is_pipeline_affecting_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/").lstrip("./")
    return any(normalized.startswith(prefix) for prefix in _PIPELINE_AFFECTING_PATH_PREFIXES)


def _find_line_containing(lines: list[str], needle: str) -> int | None:
    for index, line in enumerate(lines, start=1):
        if needle in line:
            return index
    return None


def _is_checked_line(line: str) -> bool:
    return re.match(r"^\s*-\s*\[x\]\s+", line) is not None
