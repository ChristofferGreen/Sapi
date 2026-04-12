flow_key: topic_generation
version: v1
schema_path: schemas/topic_generation.v1.schema.json
output_json_path: <space_root>/topics/<topic_id>.json
context_paths:
  - <space_root>/sources
  - <space_root>/claims
---
## Task
Generate one strict JSON object for topic generation at `output_json_path`.

## Context Interpretation Rules
- Use only evidence available under `context_paths`.
- If support is weak/ambiguous, reflect that in section content rather than inventing facts.
- Do not invent canonical IDs outside schema contracts.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "topic_id": "",
  "title": "",
  "structure_type": "wiki",
  "sections": [],
  "claim_ids": [],
  "source_ids": []
}
```
