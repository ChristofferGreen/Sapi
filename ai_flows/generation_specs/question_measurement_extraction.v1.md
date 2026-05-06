flow_key: question_measurement_extraction
version: v1
schema_path: schemas/question_measurement_extraction.v1.schema.json
output_json_path: <space_root>/runs/<run_id>/semantic/question_measurement_extraction/<question_id>.json
context_paths:
  - <space_root>/questions/<question_id>.json
  - <space_root>/sources/records
  - <space_root>/claims
  - <space_root>/evidence
---
## Task
Generate one strict JSON object containing a small set of structured measurement rows that materially help
answer one prepared question.

## Context Interpretation Rules
- Extract only key measurements that are interesting for the prepared question, not every numeric value in
  the linked sources.
- Keep a measurement only when it changes, constrains, compares, or usefully calibrates the answer to the
  question. Omit incidental dataset sizes, timestamps, hardware facts, table dimensions, or source-level
  statistics unless they directly matter to the question.
- Prefer `0..5` measurement rows. Return at most `6` rows; if more explicit numbers are available, select
  the most decision-relevant, comparative, surprising, or answer-shaping rows and add a warning that lower
  priority measurements were omitted.
- Extract measurements only from linked, context-grounded source, claim, and evidence material.
- Preserve units, population/context, outcome, comparator, and uncertainty exactly enough for audit.
- Do not coerce incompatible units or missing values into numeric rows.
- Return `chart_groups` only when rows share compatible measure, unit, outcome, and population semantics.

## Strict Output Rules
- Return JSON object only.
- Do not return markdown fences.
- Do not include prose outside JSON.
- Do not invent numeric values.
- Every measurement row must include a canonical source ID and either a claim ID or evidence ID.
- Every measurement row must include `question_relevance`, a concise explanation of why this measurement
  is worth showing for the prepared question.

## Schema-Repair Instructions
- If given prior invalid JSON and validation errors, return one complete corrected JSON replacement.

## Non-Normative Shape Sketch
```json
{
  "schema_version": "question_measurement_extraction_v1",
  "question_id": "question-protein-intake",
  "measurements": [
    {
      "measurement_id": "measurement-protein-grams-per-day--123456789abc",
      "source_id": "source-protein-intake--123456789abc",
      "claim_id": "claim-protein-dose--123456789abc",
      "evidence_id": "evidence-protein-dose-response--123456789abc",
      "measure_name": "protein intake",
      "value": 1.6,
      "value_max": 2.2,
      "unit": "g/kg/day",
      "population": "resistance-trained adults",
      "outcome": "muscle hypertrophy",
      "comparator": "lower intake",
      "uncertainty": "range depends on training status and energy balance",
      "question_relevance": "This range directly calibrates the answer by giving a dose window for the target outcome."
    }
  ],
  "chart_groups": [
    {
      "chart_group_id": "chart-protein-intake-hypertrophy",
      "measure_name": "protein intake",
      "unit": "g/kg/day",
      "outcome": "muscle hypertrophy",
      "population": "resistance-trained adults",
      "measurement_ids": ["measurement-protein-grams-per-day--123456789abc"]
    }
  ],
  "warnings": []
}
```
