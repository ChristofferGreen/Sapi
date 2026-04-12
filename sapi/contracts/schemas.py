"""JSON schema loading and machine-readable validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class SchemaValidationIssue:
    """Normalized schema-validation error detail."""

    path: str
    message: str
    validator: str
    validator_value: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "message": self.message,
            "validator": self.validator,
            "validator_value": self.validator_value,
        }


class SchemaValidationError(ValueError):
    """Raised when instance validation fails against a JSON schema."""

    def __init__(self, issues: list[SchemaValidationIssue]) -> None:
        self.issues = issues
        super().__init__(f"Schema validation failed with {len(issues)} error(s).")


def load_json_schema(schema_path: Path) -> dict[str, Any]:
    """Load one JSON schema object from disk."""
    schema = json.loads(schema_path.read_text())
    if not isinstance(schema, dict):
        raise ValueError(f"Schema document must be a JSON object: {schema_path}")
    return schema


def validate_json_instance(instance: Any, schema: dict[str, Any]) -> list[SchemaValidationIssue]:
    """Return deterministic, machine-readable schema-validation issues."""
    validator = Draft202012Validator(schema)
    raw_errors = sorted(validator.iter_errors(instance), key=lambda err: list(err.absolute_path))
    return [
        SchemaValidationIssue(
            path="/" + "/".join(str(part) for part in err.absolute_path),
            message=err.message,
            validator=err.validator,
            validator_value=err.validator_value,
        )
        for err in raw_errors
    ]


def require_valid_json_instance(instance: Any, schema: dict[str, Any]) -> None:
    """Raise SchemaValidationError when any validation issue is present."""
    issues = validate_json_instance(instance, schema)
    if issues:
        raise SchemaValidationError(issues)
