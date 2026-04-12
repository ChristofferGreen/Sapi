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
_QUERY_CANONICAL_SEGMENT_PATTERN = re.compile(
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


def run_guardrail_checks(repo_root: Path) -> list[GuardrailIssue]:
    """Run repository anti-drift checks and return all discovered issues."""
    repo_root = repo_root.resolve()
    issues: list[GuardrailIssue] = []
    issues.extend(_check_registry_fallback_literals(repo_root))
    issues.extend(_check_env_flow_controls(repo_root))
    issues.extend(_check_semantic_contract_duplication(repo_root))
    issues.extend(_check_query_canonical_mutation_patterns(repo_root))
    return sorted(
        issues,
        key=lambda issue: (issue.check_id, str(issue.path), issue.line, issue.message),
    )


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
            if _QUERY_CANONICAL_SEGMENT_PATTERN.search(line):
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
