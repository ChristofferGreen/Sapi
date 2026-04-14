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
- `source.display_title` is required and MUST be a high-quality post-style title for UI display.
  - target length: `4..12` words (`12..120` chars) for high-quality outputs
  - schema lower bound is `4` chars for compatibility with short canonical titles; still prefer `12+`
  - summarize the central claim/theme of the source
  - avoid raw filenames, slugs, IDs, URLs, hashes, and boilerplate metadata fragments
  - keep wording readable and specific (not clickbait, not generic placeholders)
  - no trailing punctuation
- `source_dossier` is required and MUST be included:
  - `summary_short`: reader-facing abstract (2-4 sentences)
  - `summary_long`: substantive overview/commentary so readers can understand the source without opening the PDF
    - target depth: `~900..4000` chars (minimum schema requirement is 900)
  - `sections`: 5..8 section objects with `heading`, `body`, and `grounding_claim_ids`
    - each section body should be detailed (`~140..800` chars)
  - section writing should cover: argument, evidence/reasoning path, assumptions/limits, and practical interpretation
  - every section SHOULD cite relevant `claim_id` values in `grounding_claim_ids` when claim evidence exists
  - avoid generic filler; write source-specific commentary grounded in extracted claims
- each claim object SHOULD include `short_title` for UI claim-link labels:
  - MUST be authored by the LLM from claim semantics (not a mechanical truncation of claim text)
  - MUST be `3..7` words
  - SHOULD follow compact truth-apt proposition style (`X is Y`, `X implies Y`, `X constrains Y`)
  - MUST avoid lead-ins like `the paper claims`, `the article argues`, `authors show`
  - MUST be a concise label, not a full sentence/parapraph
- claim `text` MUST be a truth-apt proposition attributed to the source content itself
  - avoid meta narration about the publication process (`the paper presents`, `the article gives`)
  - when the source uses reporting lead-ins, rewrite to the underlying proposition
- claim `evidence_excerpts` (or alias `evidence`) SHOULD include only concrete evidence artifacts:
  - acceptable: measurement values/statistics, theorem/proof steps, equations, formal derivations, table/figure findings
  - avoid repeating the claim text itself or generic narrative summaries (`the paper claims...`)
  - if no concrete evidence artifact is available, prefer an empty list over low-quality filler

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "source_date_inference": null,
  "source": {
    "display_title": ""
  },
  "claims": [
    {
      "text": "",
      "short_title": ""
    }
  ],
  "relations": [],
  "summary": "",
  "warnings": [],
  "source_dossier": {
    "summary_short": "",
    "summary_long": "",
    "sections": [
      {
        "heading": "",
        "body": "",
        "grounding_claim_ids": []
      }
    ]
  }
}
```
