flow_key: query_synthesis
version: v1
schema_path: schemas/query_synthesis.v1.schema.json
output_json_path: <space_root>/outputs/query/<query_id>/query.json
context_paths:
  - <space_root>/topics
  - <space_root>/claims
  - <space_root>/sources
---
## Task
Generate one strict JSON object for query synthesis at `output_json_path`.

## Context Interpretation Rules
- Use only evidence from `context_paths`.
- When evidence conflicts or is incomplete, capture uncertainty in `warnings` and counters.
- Do not invent claim/source identifiers not grounded in provided context.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "query_id": "",
  "answer": "",
  "claims_used": [],
  "sources_used": [],
  "retrieval_counts": {},
  "contradictions_considered": 0,
  "falsification_signals": [],
  "mode": "strict",
  "scope": "space",
  "execution": {},
  "warnings": []
}
```
