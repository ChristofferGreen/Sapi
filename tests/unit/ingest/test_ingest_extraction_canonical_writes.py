from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.ingest.records_writer import (
    ingest_source_artifacts_and_record,
    run_ingest_extraction_and_persist_canonical,
)
from sapi.ingest.relation_store import relation_file_id_from_relation_id
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.semantic_executor import SemanticFlowError


class _StaticSemanticClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        payload = dict(self._payload)
        if "evidence_items" not in payload:
            payload["evidence_items"] = []
        return json.dumps(payload)


class IngestExtractionCanonicalWriteTests(unittest.TestCase):
    def test_ingest_extraction_output_must_validate_against_schema_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            run_id = "run-schema-invalid"

            invalid_semantic_output = {
                "source_date_inference": None,
                "source": {},
                "claims": [],
                "relations": [],
            }
            with self.assertRaises(SemanticFlowError):
                run_ingest_extraction_and_persist_canonical(
                    space_root=space_root,
                    source_id=source_id,
                    run_id=run_id,
                    llm_client=_StaticSemanticClient(invalid_semantic_output),
                    max_repair_loops=0,
                )

            semantic_path = space_root / "runs" / run_id / "semantic" / "ingest_extraction.json"
            self.assertFalse(semantic_path.exists())
            self.assertFalse((space_root / "claims").exists())
            self.assertFalse((space_root / "relations").exists())

    def test_canonical_claim_and_relation_writes_follow_id_and_path_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            run_id = "run-claim-relation-contract"

            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Contract Source",
                    "display_title": "Contract Source Core Findings",
                },
                "claims": [
                    {"text": "Cats purr when content."},
                    {"text": "Purring can indicate comfort in domestic cats."},
                ],
                "relations": [
                    {
                        "relation_type": "supports",
                        "src_claim_ref": "0",
                        "dst_claim_ref": "1",
                    }
                ],
                "summary": "Two claims extracted.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id=run_id,
                llm_client=_StaticSemanticClient(semantic_output),
            )

            self.assertTrue(result.semantic_output_path.is_file())
            self.assertEqual(len(result.claim_paths), 2)
            claim_ids: list[str] = []
            for claim_path in result.claim_paths:
                self.assertEqual(claim_path.parent, space_root / "claims")
                self.assertRegex(claim_path.name, r"^claim-[a-z0-9-]+--[0-9a-f]{12,}\.json$")
                claim_payload = json.loads(claim_path.read_text())
                claim_id = claim_payload["claim_id"]
                claim_ids.append(claim_id)
                self.assertEqual(claim_path.name, f"{claim_id}.json")
                self.assertEqual(claim_payload["source_id"], source_id)

            self.assertEqual(len(result.relation_paths), 1)
            relation_path = result.relation_paths[0]
            self.assertEqual(relation_path.parent, space_root / "relations")
            self.assertRegex(relation_path.name, r"^rel-[0-9a-f]{64}\.json$")
            relation_payload = json.loads(relation_path.read_text())
            self.assertEqual(
                relation_payload["relation_id"],
                f"supports:{claim_ids[0]}->{claim_ids[1]}",
            )
            self.assertEqual(
                relation_payload["relation_file_id"],
                relation_file_id_from_relation_id(relation_payload["relation_id"]),
            )
            self.assertEqual(relation_path.name, f"{relation_payload['relation_file_id']}.json")

    def test_relation_writes_reject_removed_closed_status_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))

            claim_alpha = "claim-alpha--111111111111"
            claim_beta = "claim-beta--222222222222"
            semantic_output = {
                "source_date_inference": {
                    "date": "2026-04-12",
                    "origin": "explicit",
                    "confidence": "high",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Normalization Source",
                    "display_title": "Normalization Source and Contradictory Claims",
                    "article_title": "Normalization Source and Contradictory Claims",
                },
                "claims": [
                    {"claim_id": claim_alpha, "text": "Alpha statement."},
                    {"claim_id": claim_beta, "text": "Beta statement."},
                ],
                "relations": [
                    {
                        "relation_type": "contradictory",
                        "src_claim_id": claim_beta,
                        "dst_claim_id": claim_alpha,
                        "status": "closed",
                    }
                ],
                "summary": "Contradictory relation extracted.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            with self.assertRaisesRegex(ValueError, "Unsupported relation status: closed"):
                run_ingest_extraction_and_persist_canonical(
                    space_root=space_root,
                    source_id=source_id,
                    run_id="run-relation-normalization",
                    llm_client=_StaticSemanticClient(semantic_output),
                )

            relations_dir = space_root / "relations"
            self.assertFalse(relations_dir.exists())

    def test_ingest_extraction_persists_summary_warnings_and_source_date_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": "no publication date found",
                },
                "source": {
                    "source_id": source_id,
                    "title": "Summary Source",
                    "display_title": "Summary Source Main Arguments",
                },
                "claims": [{"text": "One claim extracted."}],
                "relations": [],
                "summary": "Extraction summary text.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [
                    {
                        "code": "missing_publication_date",
                        "message": "Publication date could not be resolved; continuing with date=null.",
                    }
                ],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-source-summary",
                llm_client=_StaticSemanticClient(semantic_output),
            )

            source_record = json.loads(result.source_record_path.read_text())
            self.assertEqual(source_record["source_date_inference"], semantic_output["source_date_inference"])
            self.assertEqual(source_record["summary"], semantic_output["summary"])
            self.assertEqual(source_record["warnings"], semantic_output["warnings"])
            self.assertEqual(source_record["display_title"], "Summary Source Main Arguments")

    def test_ingest_extraction_persists_source_dossier_for_source_page_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": "2026-04-14",
                    "origin": "inferred",
                    "confidence": "medium",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Dossier Source",
                    "display_title": "Dossier Source Overview",
                },
                "claims": [{"text": "One claim extracted."}],
                "relations": [],
                "summary": "Short summary text for feeds.",
                "source_dossier": {
                    "summary_short": "A short abstract that gives readers immediate context without opening the PDF.",
                    "summary_long": (
                        "This source dossier provides a longer interpretive walkthrough of the argument, "
                        "its evidence strategy, and its implications for topic synthesis. The narrative "
                        "explains the internal logic of the paper, tracks how premises move into conclusions, "
                        "and calls out the assumptions that make the core claim persuasive or vulnerable.\n\n"
                        "It is intended for readers who want substance before diving into the full paper. "
                        "The commentary also describes how the source should be interpreted in relation to "
                        "neighboring topics, what skeptical checks should be performed before reusing the "
                        "conclusions, and where boundary conditions are most likely to limit generalization.\n\n"
                        "In addition, this long-form layer explains how a reviewer should distinguish direct "
                        "textual support from interpretive interpolation, why certain inferential bridges need "
                        "extra caution, and how to evaluate whether cross-source synthesis remains faithful to "
                        "the original argumentative scope rather than drifting into unsupported generalization."
                    ),
                    "sections": [
                        {
                            "heading": "What the Source Argues",
                            "body": (
                                "The paper advances a specific position and clarifies where that position "
                                "is stronger than common alternatives in the same debate. It also explains "
                                "how that position avoids both overconfident realism and empty instrumentalism "
                                "by explicitly constraining the scope of its claims."
                            ),
                            "grounding_claim_ids": [],
                        },
                        {
                            "heading": "How the Argument Is Built",
                            "body": (
                                "The reasoning is staged through explicit premises and evidence-linked "
                                "inferences that can be checked against extracted claim artifacts. The section "
                                "walks through how intermediate steps support the final conclusion and where "
                                "counter-interpretations would need additional evidence."
                            ),
                            "grounding_claim_ids": [],
                        },
                        {
                            "heading": "Evidence and Interpretive Weight",
                            "body": (
                                "Evidence is separated into descriptive claims, inferential claims, and "
                                "cross-source contextual claims. This separation makes it easier to detect "
                                "when later discourse overstates what the source itself directly establishes."
                            ),
                            "grounding_claim_ids": [],
                        },
                        {
                            "heading": "Assumptions and Limits",
                            "body": (
                                "The key scrutiny point is whether scope constraints and assumptions remain "
                                "valid when moving from local claims to broader metaphysical conclusions. "
                                "Boundary conditions are identified so downstream synthesis does not treat "
                                "contingent premises as universal commitments."
                            ),
                            "grounding_claim_ids": [],
                        },
                        {
                            "heading": "How to Use This Source in the Space",
                            "body": (
                                "Readers should treat this dossier as an orientation layer: first absorb the "
                                "argument map, then inspect claim links for exact wording, and finally compare "
                                "topic-level reuse patterns to decide whether extrapolations remain justified."
                            ),
                            "grounding_claim_ids": [],
                        },
                    ],
                },
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-source-dossier",
                llm_client=_StaticSemanticClient(semantic_output),
            )

            source_record = json.loads(result.source_record_path.read_text())
            self.assertIn("source_dossier", source_record)
            self.assertEqual(
                source_record["source_dossier"]["summary_short"],
                semantic_output["source_dossier"]["summary_short"],
            )
            self.assertEqual(len(source_record["source_dossier"]["sections"]), 5)

    def test_ingest_extraction_persists_llm_authored_source_authors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": "2026-04-14",
                    "origin": "inferred",
                    "confidence": "medium",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Author Source",
                    "display_title": "Author Source Overview",
                    "authors": ["Ada Lovelace", "Alan Turing", "Ada Lovelace"],
                },
                "claims": [{"text": "One claim extracted."}],
                "relations": [],
                "summary": "Short summary text for feeds.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-source-authors",
                llm_client=_StaticSemanticClient(semantic_output),
            )

            source_record = json.loads(result.source_record_path.read_text())
            self.assertEqual(source_record["authors"], ["Ada Lovelace", "Alan Turing"])
            self.assertEqual(
                source_record["source_semantic"]["authors"],
                ["Ada Lovelace", "Alan Turing"],
            )

    def test_ingest_extraction_accepts_evidence_object_alias_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Evidence Alias Source",
                    "display_title": "Evidence Alias Source Findings",
                },
                "claims": [
                    {
                        "text": "Alias evidence extraction claim.",
                        "evidence": [
                            {"quote": "Theorem 1 proves psi-epistemic overlap <= 0.10 under preparation independence."},
                            {"text": "Measured overlap was 0.07 +/- 0.01 with n=64 prepared systems."},
                            {"content": "Table 2 reports p-value = 0.004 for the null overlap hypothesis."},
                            {"excerpt": "Formal derivation shows contradiction when overlap > 0 in Eq. (5)."},
                        ],
                    }
                ],
                "evidence_items": [
                    {
                        "evidence_id": "evidence-psi-overlap-measurement--1a2b3c4d5e6f",
                        "title": "Psi overlap measurement",
                        "excerpt": "Measured overlap was 0.07 +/- 0.01 with n=64 prepared systems.",
                        "overview": (
                            "This measurement constrains overlap assumptions in psi-epistemic models "
                            "and is linked to the extracted claim as canonical evidence."
                        ),
                        "evidence_type": "measurement",
                        "claim_refs": ["0"],
                        "source_id": source_id,
                        "page_refs": ["p.4"],
                    }
                ],
                "relations": [],
                "summary": "Evidence aliases normalized.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-evidence-aliases",
                llm_client=_StaticSemanticClient(semantic_output),
            )
            claim_payload = json.loads(result.claim_paths[0].read_text())
            self.assertEqual(
                claim_payload["evidence_excerpts"],
                [
                    "Theorem 1 proves psi-epistemic overlap <= 0.10 under preparation independence.",
                    "Measured overlap was 0.07 +/- 0.01 with n=64 prepared systems.",
                    "Table 2 reports p-value = 0.004 for the null overlap hypothesis.",
                    "Formal derivation shows contradiction when overlap > 0 in Eq. (5).",
                ],
            )
            self.assertEqual(len(result.evidence_paths), 1)
            evidence_payload = json.loads(result.evidence_paths[0].read_text())
            self.assertEqual(evidence_payload["evidence_id"], "evidence-psi-overlap-measurement--1a2b3c4d5e6f")
            self.assertEqual(evidence_payload["claim_ids"], [claim_payload["claim_id"]])
            self.assertEqual(evidence_payload["source_id"], source_id)

    def test_ingest_extraction_preserves_claim_level_evidence_excerpts_without_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Evidence Filter Source",
                    "display_title": "Evidence Filter Source Findings",
                },
                "claims": [
                    {
                        "text": "The paper claims the ontology is local-realistic.",
                        "evidence_excerpts": [
                            "The paper claims the ontology is local-realistic.",
                            "This article argues that realism is preferable.",
                            "Measured Bell parameter was 2.71 with n=120 trials.",
                            "Lemma 3 proves incompatibility under Eq. (9).",
                        ],
                    }
                ],
                "relations": [],
                "summary": "Evidence filtering keeps only formal/measurement excerpts.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-evidence-filter",
                llm_client=_StaticSemanticClient(semantic_output),
            )
            claim_payload = json.loads(result.claim_paths[0].read_text())
            self.assertEqual(
                claim_payload["evidence_excerpts"],
                [
                    "The paper claims the ontology is local-realistic.",
                    "This article argues that realism is preferable.",
                    "Measured Bell parameter was 2.71 with n=120 trials.",
                    "Lemma 3 proves incompatibility under Eq. (9).",
                ],
            )

    def test_ingest_extraction_rejects_evidence_items_with_unknown_claim_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Evidence Ref Validation Source",
                    "display_title": "Evidence Ref Validation Source Findings",
                },
                "claims": [{"text": "One claim extracted."}],
                "evidence_items": [
                    {
                        "evidence_id": "evidence-bad-claim-ref--1234567890ab",
                        "title": "Bad claim ref",
                        "excerpt": "Equation (7) shows contradiction under overlap assumptions in the setup.",
                        "overview": (
                            "This should fail because claim_refs does not map to an extracted claim ID "
                            "after canonical claim resolution during ingest record persistence."
                        ),
                        "evidence_type": "equation",
                        "claim_refs": ["missing-claim-ref"],
                        "source_id": source_id,
                    }
                ],
                "relations": [],
                "summary": "Evidence ref validation.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            with self.assertRaisesRegex(ValueError, "unknown claim"):
                run_ingest_extraction_and_persist_canonical(
                    space_root=space_root,
                    source_id=source_id,
                    run_id="run-evidence-bad-ref",
                    llm_client=_StaticSemanticClient(semantic_output),
                )

    def test_ingest_extraction_preserves_ai_authored_short_claim_titles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Short Title Source",
                    "display_title": "Short Title Source Findings",
                },
                "claims": [
                    {
                        "text": (
                            "The paper claims that preparation independence constrains epistemic overlaps "
                            "between distinct quantum states in multi-system settings."
                        ),
                        "short_title": "Preparation overlap is constrained",
                    }
                ],
                "relations": [],
                "summary": "Short title normalization.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-short-title",
                llm_client=_StaticSemanticClient(semantic_output),
            )
            claim_payload = json.loads(result.claim_paths[0].read_text())
            self.assertIn("short_title", claim_payload)
            self.assertEqual(claim_payload["short_title"], "Preparation overlap is constrained")
            self.assertIn("added_at", claim_payload)
            self.assertTrue(claim_payload["added_at"].endswith("Z"))
            self.assertIn("T", claim_payload["added_at"])

    def test_ingest_extraction_persists_explicit_claim_added_at_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Claim Timestamp Source",
                    "display_title": "Claim Timestamp Source Findings",
                },
                "claims": [
                    {
                        "text": "Preparation independence constrains epistemic overlaps.",
                        "added_at": "2026-04-01T09:30:00Z",
                    }
                ],
                "relations": [],
                "summary": "Claim timestamp persistence.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-claim-added-at",
                llm_client=_StaticSemanticClient(semantic_output),
            )
            claim_payload = json.loads(result.claim_paths[0].read_text())
            self.assertEqual(claim_payload["added_at"], "2026-04-01T09:30:00Z")

    def test_ingest_extraction_preserves_ai_authored_claim_text_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Claim Normalization Source",
                    "display_title": "Claim Normalization Source Findings",
                },
                "claims": [
                    {
                        "text": "A second core assumption is preparation independence.",
                    },
                    {
                        "text": (
                            "The paper also gives a noise-tolerant formal version of the theorem, "
                            "deriving a lower bound on the total variation distance between "
                            "underlying-state distributions."
                        ),
                    },
                ],
                "relations": [],
                "summary": "Claim preservation behavior.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-claim-normalization",
                llm_client=_StaticSemanticClient(semantic_output),
            )
            first_claim = json.loads(result.claim_paths[0].read_text())
            second_claim = json.loads(result.claim_paths[1].read_text())

            self.assertEqual(first_claim["text"], "A second core assumption is preparation independence.")
            self.assertEqual(first_claim["short_title"], "A second core assumption is preparation independence")
            self.assertIn("paper", second_claim["text"].casefold())
            self.assertIn("deriving", second_claim["text"].casefold())
            self.assertEqual(second_claim["short_title"], second_claim["text"].rstrip("."))

    def test_ingest_extraction_normalizes_display_title_with_article_title_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {
                    "source_id": source_id,
                    "title": "Fallback Source",
                    "display_title": "https://example.com/source.pdf",
                    "article_title": "Quantum Ontology Without Speculation",
                },
                "claims": [{"text": "One claim extracted."}],
                "relations": [],
                "summary": "Fallback display title normalized.",
                "source_dossier": self._default_source_dossier(),
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-display-title-fallback",
                llm_client=_StaticSemanticClient(semantic_output),
            )

            source_record = json.loads(result.source_record_path.read_text())
            self.assertEqual(source_record["display_title"], "Quantum Ontology Without Speculation")
            self.assertEqual(
                source_record["source_semantic"]["display_title"],
                "Quantum Ontology Without Speculation",
            )

    def _bootstrap_source(self, tmp_root: Path) -> tuple[Path, str]:
        space_root = tmp_root / "spaces" / "alpha"
        source_path = tmp_root / "source.txt"
        source_path.write_text("ingest extraction contract fixture\n")
        result = ingest_source_artifacts_and_record(
            space_root=space_root,
            source_path_or_url=str(source_path),
            source_title_override="Fixture Source",
        )
        return space_root, result.source_id

    def _default_source_dossier(self) -> dict[str, object]:
        return {
            "summary_short": (
                "This dossier provides a concise reader-facing abstract so users can understand the source "
                "without immediately opening the full document."
            ),
            "summary_long": (
                "This fallback dossier text is intentionally long-form and structured for deterministic test "
                "coverage. It explains argument intent, evidence framing, and transfer limits so source pages "
                "can render substantial narrative content rather than minimal stubs.\n\n"
                "The prose is scoped to contract validation rather than domain novelty: it demonstrates that "
                "readers can absorb a useful synopsis, see clearly separated sections, and inspect grounded "
                "claim-link placeholders while maintaining strict schema conformance.\n\n"
                "In production flows, this field is expected to be source-specific analysis. In test fixtures, "
                "the objective is to keep output shape stable while still exercising large-body rendering paths, "
                "section hierarchy styling, and evidence-link placement behavior in the generated source page.\n\n"
                "This extra paragraph intentionally extends the body so tests enforce the full long-form dossier "
                "contract rather than a near-threshold approximation. It also simulates realistic reader support "
                "copy where synthesis context, confidence boundaries, and practical interpretation guidance are "
                "spelled out before users inspect underlying claim files."
            ),
            "sections": [
                {
                    "heading": "What the Source Argues",
                    "body": (
                        "This section states the source thesis in plain language and explains the intended "
                        "scope of that thesis so readers do not confuse local claims with universal commitments."
                    ),
                    "grounding_claim_ids": [],
                },
                {
                    "heading": "How the Argument Is Built",
                    "body": (
                        "This section describes the inferential path from premises to conclusion and clarifies "
                        "how evidence-bearing statements differ from interpretive bridge statements."
                    ),
                    "grounding_claim_ids": [],
                },
                {
                    "heading": "Evidence and Interpretive Weight",
                    "body": (
                        "This section explains how much argumentative weight each evidence cluster is expected "
                        "to carry and where caution is needed before drawing stronger downstream conclusions."
                    ),
                    "grounding_claim_ids": [],
                },
                {
                    "heading": "Assumptions and Limits",
                    "body": (
                        "This section lists assumptions that must hold for the argument to remain valid and "
                        "highlights context shifts that could weaken or invalidate the proposed inference."
                    ),
                    "grounding_claim_ids": [],
                },
                {
                    "heading": "How to Use This Source in the Space",
                    "body": (
                        "This section gives practical guidance for navigating from source narrative to linked "
                        "claims and related topics so synthesis stays auditable and faithful to canonical evidence."
                    ),
                    "grounding_claim_ids": [],
                },
            ],
        }


if __name__ == "__main__":
    unittest.main()
