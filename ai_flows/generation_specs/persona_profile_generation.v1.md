flow_key: persona_profile_generation
version: v1
schema_path: schemas/persona_profile_generation.v1.schema.json
output_json_path: <space_root>/profiles/persona-<persona_id>.json
context_paths:
  - personas/social_users.json
  - <space_root>/comments
---
## Task
Generate one strict JSON object for persona profile generation at `output_json_path`.

## Context Interpretation Rules
- Use only seeded persona catalog and space comment context declared in `context_paths`.
- Keep profile narratives evidence-grounded and avoid unsupported claims.
- Do not invent persona identities beyond schema fields.
- Incorporate seeded `biography_profile` and `short_cv` into profile sections when present.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "persona_id": "",
  "space_name": "",
  "profile_sections": [],
  "profile_image_path": null,
  "accountability_summary": ""
}
```
