flow_key: comment_section_generation
version: v1
schema_path: schemas/comment_section_generation.v1.schema.json
output_json_path: <space_root>/runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json
context_paths:
  - <space_root>/topics
  - <space_root>/sources
  - <space_root>/comments
  - <site_path>/config/discussion_controls.json
---
## Task
Generate one strict JSON object for comment section generation at `output_json_path`.

## Context Interpretation Rules
- Use only the provided topic/comment/control context from `context_paths`.
- Preserve the requested page target semantics from input context.
- Do not invent persona identifiers or thread references outside evidence.
- Score each generated comment neutrally using the comment body, surrounding thread chain, and original source context.
- Emit one `score_assessment` object per comment with an integer `score` and concise `rationale`.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "page_ref": "",
  "requested_count": 0,
  "comments": [
    {
      "comment_ref": "",
      "persona_id": "",
      "body": "",
      "parent_ref": null,
      "score_assessment": {
        "score": 0,
        "rationale": ""
      }
    }
  ]
}
```
