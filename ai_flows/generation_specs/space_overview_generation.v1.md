flow_key: space_overview_generation
version: v1
schema_path: schemas/space_overview_generation.v1.schema.json
output_json_path: <space_root>/outputs/space_overview/<overview_id>/overview.json
context_paths:
  - <space_root>/outputs/space_overview/<overview_id>/context.json
  - <space_root>/sources/records
  - <space_root>/claims
  - <space_root>/relations
  - <space_root>/topics
  - <space_root>/subspaces.json
---
## Task
Generate one strict JSON object for space or subspace overview synthesis at `output_json_path`.

## Context Interpretation Rules
- Treat `<space_root>/outputs/space_overview/<overview_id>/context.json` as the authoritative scope-selection document.
- Use only canonical `source_id`, `claim_id`, and `topic_id` values grounded in `context_paths`.
- Do not invent sources, claims, subspaces, or citation anchors that are not supported by the provided context.
- When evidence is incomplete or conflicting, capture the uncertainty in section prose and `warnings`.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.
- Emit exactly the five required narrative sections and keep `references.citation_anchors[]` aligned with the cited `source_id` and `claim_id` values.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "schema_version": "space_overview_v1",
  "metadata": {
    "overview_id": "space--alpha",
    "scope_kind": "space",
    "space_name": "alpha",
    "scope_name": "alpha",
    "title": "State of the Evidence in Alpha",
    "summary": "Short lede for the overview article."
  },
  "sections": [
    {
      "section_id": "topic_framing",
      "heading": "Topic framing",
      "body": "Summary paragraph.",
      "source_ids": ["source-alpha--aaaaaaaaaaaa"],
      "claim_ids": ["claim-alpha--bbbbbbbbbbbb"],
      "citation_anchor_ids": ["anchor-alpha"]
    }
  ],
  "references": {
    "source_ids": ["source-alpha--aaaaaaaaaaaa"],
    "claim_ids": ["claim-alpha--bbbbbbbbbbbb"],
    "citation_anchors": [
      {
        "anchor_id": "anchor-alpha",
        "label": "[S1]",
        "source_id": "source-alpha--aaaaaaaaaaaa",
        "claim_ids": ["claim-alpha--bbbbbbbbbbbb"],
        "locator": "pp. 1-2"
      }
    ]
  },
  "freshness": {
    "generated_at": "2026-04-24T12:00:00Z",
    "input_signature": "sha256:abc123",
    "source_record_count": 12,
    "claim_count": 38,
    "relation_count": 9,
    "topic_count": 4
  },
  "warnings": []
}
```
