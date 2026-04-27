flow_key: source_revision_detection
version: v1
schema_path: schemas/source_revision_detection.v1.schema.json
output_json_path: <space_root>/runs/<run_id>/semantic/source_revision_detection.json
context_paths:
  - <space_root>/sources/records
  - <space_root>/sources/artifacts
---
## Task
Generate one strict JSON object that decides whether the newly ingested source is certainly a new
revision of exactly one provided candidate source.

## Context Interpretation Rules
- Use only evidence available under `context_paths` and `task_context`.
- Candidate source IDs are bounded by `task_context`; do not search for or invent other candidate IDs.
- Default to inspecting `source.md` and `source_extraction.json` for the new source and candidate sources.
- Inspect the original PDF/binary only when markdown quality metadata is degraded, unusable, or insufficient
  for a confident revision decision.
- A revision decision requires strong evidence that the documents are different versions of the same
  underlying work, such as matching canonical identifier, title/authorship plus revision/version markers,
  or near-identical body text with clear update signals.
- Similar topic, shared authors, citation relationship, or topical overlap alone is not enough.
- If certainty is not high, return `decision: "new_source"` or `decision: "uncertain"` with
  `certainty: false`.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.
- Do not invent source IDs.
- Use `matched_source_id: null` unless `decision` is `revision` and `certainty` is `true`.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "decision": "uncertain",
  "certainty": false,
  "matched_source_id": null,
  "candidate_source_ids": ["source-example--0123456789ab"],
  "rationale": "The sources discuss the same topic, but no version marker or shared identifier proves a revision.",
  "evidence": ["Both sources discuss the same subject, but titles and identifiers differ."]
}
```
