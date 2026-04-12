flow_key: ingest_extraction
version: v1
schema_path: schemas/ingest_extraction.v1.schema.json
output_json_path: <space_root>/runs/<run_id>/semantic/ingest_extraction.json
context_paths:
  - <space_root>/sources
  - <space_root>/claims
  - <space_root>/relations
---
## Task
Generate one strict JSON object for ingest extraction at `output_json_path`.

## Context Interpretation Rules
- Treat `context_paths` as the only evidence scope for this generation.
- If context is missing or ambiguous, keep values conservative and place details in `warnings`.
- Do not invent canonical IDs beyond schema-allowed fields.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "source_date_inference": null,
  "source": {},
  "claims": [],
  "relations": [],
  "summary": "",
  "warnings": []
}
```
