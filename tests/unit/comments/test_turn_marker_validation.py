from __future__ import annotations

import unittest

from sapi.comments.merge_normalize import apply_merged_comments_to_page, merge_comment_section


_VALID_CLAIM_ID = "claim-evidence-point--abcdefabcdef"
_VALID_SOURCE_ID = "source-primary-study--1234abcd5678"


class TurnMarkerValidationUnitTests(unittest.TestCase):
    def test_canonical_turn_marker_is_supported_for_argumentative_turns(self) -> None:
        result = merge_comment_section(
            page_ref="topic:topic-alpha",
            page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
            semantic_comments=[
                {
                    "persona_id": "commenter-1",
                    "body": (
                        '<<turn:{"position":"support","claim_ids":["'
                        + _VALID_CLAIM_ID
                        + '"],"evidence_refs":["claim:'
                        + _VALID_CLAIM_ID
                        + '"],"confidence":0.81}>>'
                        "Argumentative support text."
                    ),
                }
            ],
        )
        self.assertEqual(result.comments_added, 1)
        row = result.merged_comments[0]
        self.assertEqual(row["body"], "Argumentative support text.")
        self.assertEqual(row["turn"]["position"], "support")
        self.assertEqual(row["turn"]["claim_ids"], [_VALID_CLAIM_ID])
        self.assertEqual(row["turn"]["evidence_refs"], [f"claim:{_VALID_CLAIM_ID}"])
        self.assertEqual(row["turn"]["confidence"], 0.81)

    def test_legacy_turn_marker_is_normalized(self) -> None:
        existing_uid = "comment-existing--abcde12345"
        result = merge_comment_section(
            page_ref="topic:topic-alpha",
            page_payload={
                "topic_id": "topic-alpha",
                "title": "Alpha",
                "comment_section": {
                    "page_ref": "topic:topic-alpha",
                    "comments": [
                        {
                            "comment_uid": existing_uid,
                            "persona_id": "commenter-1",
                            "body": (
                                "<!-- turn:{"
                                '"position":"challenge","claim_ids":["'
                                + _VALID_CLAIM_ID
                                + '"],"evidence_refs":["source:'
                                + _VALID_SOURCE_ID
                                + '"],"confidence":0.22} -->'
                                "Legacy marker challenge text."
                            ),
                            "comment_no": "pc-001",
                        }
                    ],
                },
            },
            semantic_comments=[],
        )
        self.assertEqual(result.comments_added, 0)
        self.assertEqual(len(result.merged_comments), 1)
        row = result.merged_comments[0]
        self.assertEqual(row["comment_uid"], existing_uid)
        self.assertEqual(row["body"], "Legacy marker challenge text.")
        self.assertEqual(row["turn"]["position"], "challenge")
        self.assertEqual(row["turn"]["evidence_refs"], [f"source:{_VALID_SOURCE_ID}"])

    def test_argumentative_turn_requires_claims_evidence_and_confidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "claim_ids"):
            merge_comment_section(
                page_ref="topic:topic-alpha",
                page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
                semantic_comments=[
                    {
                        "persona_id": "commenter-1",
                        "body": (
                            '<<turn:{"position":"support","evidence_refs":["claim:'
                            + _VALID_CLAIM_ID
                            + '"],"confidence":0.5}>>'
                            "Missing claims should fail."
                        ),
                    }
                ],
            )

        with self.assertRaisesRegex(ValueError, "evidence_refs"):
            merge_comment_section(
                page_ref="topic:topic-alpha",
                page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
                semantic_comments=[
                    {
                        "persona_id": "commenter-1",
                        "body": (
                            '<<turn:{"position":"support","claim_ids":["'
                            + _VALID_CLAIM_ID
                            + '"],"confidence":0.5}>>'
                            "Missing evidence should fail."
                        ),
                    }
                ],
            )

        with self.assertRaisesRegex(ValueError, "confidence"):
            merge_comment_section(
                page_ref="topic:topic-alpha",
                page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
                semantic_comments=[
                    {
                        "persona_id": "commenter-1",
                        "body": (
                            '<<turn:{"position":"support","claim_ids":["'
                            + _VALID_CLAIM_ID
                            + '"],"evidence_refs":["claim:'
                            + _VALID_CLAIM_ID
                            + '"],"confidence":1.2}>>'
                            "Out of range confidence should fail."
                        ),
                    }
                ],
            )

    def test_social_turns_reject_unclassified_factual_claims(self) -> None:
        with self.assertRaisesRegex(ValueError, "factual claim references"):
            merge_comment_section(
                page_ref="topic:topic-alpha",
                page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
                semantic_comments=[
                    {
                        "persona_id": "commenter-1",
                        "body": (
                            '<<turn:{"position":"social"}>>'
                            f"This casual line references {_VALID_CLAIM_ID}."
                        ),
                    }
                ],
            )

        with self.assertRaisesRegex(ValueError, "factual claim references"):
            merge_comment_section(
                page_ref="topic:topic-alpha",
                page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
                semantic_comments=[
                    {
                        "persona_id": "commenter-1",
                        "body": f"No marker but factual reference to {_VALID_SOURCE_ID}.",
                    }
                ],
            )

    def test_lightweight_social_turn_allows_empty_claim_fields(self) -> None:
        result = merge_comment_section(
            page_ref="topic:topic-alpha",
            page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
            semantic_comments=[
                {
                    "persona_id": "commenter-1",
                    "body": '<<turn:{"position":"social","confidence":0.33}>>Friendly chat reply.',
                }
            ],
        )
        self.assertEqual(result.comments_added, 1)
        row = result.merged_comments[0]
        self.assertEqual(row["body"], "Friendly chat reply.")
        self.assertEqual(row["turn"], {"position": "social", "confidence": 0.33})

    def test_rebuttal_turn_requires_steelman_ack_and_prefix_ordering(self) -> None:
        with self.assertRaisesRegex(ValueError, "strongest_opposing_point_ack"):
            merge_comment_section(
                page_ref="topic:topic-alpha",
                page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
                semantic_comments=[
                    {
                        "persona_id": "commenter-1",
                        "body": (
                            '<<turn:{"position":"rebuttal","claim_ids":["'
                            + _VALID_CLAIM_ID
                            + '"],"evidence_refs":["claim:'
                            + _VALID_CLAIM_ID
                            + '"],"confidence":0.71}>>'
                            "I disagree because the evidence does not support that point."
                        ),
                    }
                ],
            )

        with self.assertRaisesRegex(ValueError, "start of rebuttal body"):
            merge_comment_section(
                page_ref="topic:topic-alpha",
                page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
                semantic_comments=[
                    {
                        "persona_id": "commenter-1",
                        "body": (
                            "I disagree because the evidence does not support that point. "
                            "You correctly note that publication lag can distort counts."
                        ),
                        "turn": {
                            "position": "rebuttal",
                            "claim_ids": [_VALID_CLAIM_ID],
                            "evidence_refs": [f"claim:{_VALID_CLAIM_ID}"],
                            "confidence": 0.71,
                            "strongest_opposing_point_ack": (
                                "You correctly note that publication lag can distort counts."
                            ),
                        },
                    }
                ],
            )

        result = merge_comment_section(
            page_ref="topic:topic-alpha",
            page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
            semantic_comments=[
                {
                    "persona_id": "commenter-1",
                    "body": (
                        "You correctly note that publication lag can distort counts. "
                        "I still disagree because the source shows the trend persisted after normalization."
                    ),
                    "turn": {
                        "position": "rebuttal",
                        "claim_ids": [_VALID_CLAIM_ID],
                        "evidence_refs": [f"claim:{_VALID_CLAIM_ID}"],
                        "confidence": 0.71,
                        "strongest_opposing_point_ack": (
                            "You correctly note that publication lag can distort counts."
                        ),
                    },
                }
            ],
        )
        self.assertEqual(result.comments_added, 1)
        turn = result.merged_comments[0]["turn"]
        self.assertEqual(turn["position"], "rebuttal")
        self.assertEqual(
            turn["strongest_opposing_point_ack"],
            "You correctly note that publication lag can distort counts.",
        )

    def test_claim_badges_normalize_status_vocabulary_with_deterministic_fallback(self) -> None:
        result = merge_comment_section(
            page_ref="topic:topic-alpha",
            page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
            semantic_comments=[
                {
                    "persona_id": "commenter-1",
                    "body": "Claim badge normalization check.",
                    "turn": {
                        "position": "support",
                        "claim_ids": [_VALID_CLAIM_ID],
                        "evidence_refs": [f"claim:{_VALID_CLAIM_ID}"],
                        "confidence": 0.66,
                    },
                    "claim_badges": [
                        {"claim_id": _VALID_CLAIM_ID, "status": "verified", "confidence": 0.92},
                        {"claim_id": _VALID_CLAIM_ID, "status": "needs-review"},
                        {"claim_id": _VALID_CLAIM_ID},
                    ],
                }
            ],
        )
        badges = result.merged_comments[0]["claim_badges"]
        self.assertEqual(
            badges,
            [
                {"claim_id": _VALID_CLAIM_ID, "status": "verified", "confidence": 0.92},
                {"claim_id": _VALID_CLAIM_ID, "status": "unverified"},
                {"claim_id": _VALID_CLAIM_ID, "status": "unverified"},
            ],
        )

    def test_render_fields_and_moderator_outcomes_follow_comment_uid_contract(self) -> None:
        first = merge_comment_section(
            page_ref="topic:topic-alpha",
            page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
            semantic_comments=[
                {
                    "persona_id": "commenter-1",
                    "body": (
                        '<<turn:{"position":"support","claim_ids":["'
                        + _VALID_CLAIM_ID
                        + '"],"evidence_refs":["claim:'
                        + _VALID_CLAIM_ID
                        + '"],"confidence":0.81}>>'
                        "Supportive row."
                    ),
                },
                {
                    "persona_id": "commenter-2",
                    "body": (
                        '<<turn:{"position":"challenge","claim_ids":["'
                        + _VALID_CLAIM_ID
                        + '"],"evidence_refs":["source:'
                        + _VALID_SOURCE_ID
                        + '"],"confidence":0.42}>>'
                        "Challenge row."
                    ),
                    "parent_ref": "draft-1",
                },
            ],
        )
        second = merge_comment_section(
            page_ref="topic:topic-alpha",
            page_payload={
                "topic_id": "topic-alpha",
                "title": "Alpha",
                "comment_section": {
                    "page_ref": "topic:topic-alpha",
                    "comments": first.merged_comments,
                },
            },
            semantic_comments=[
                {
                    "persona_id": "commenter-1",
                    "body": (
                        '<<turn:{"position":"support","claim_ids":["'
                        + _VALID_CLAIM_ID
                        + '"],"evidence_refs":["claim:'
                        + _VALID_CLAIM_ID
                        + '"],"confidence":0.81}>>'
                        "Supportive row."
                    ),
                },
                {
                    "persona_id": "commenter-2",
                    "body": (
                        '<<turn:{"position":"challenge","claim_ids":["'
                        + _VALID_CLAIM_ID
                        + '"],"evidence_refs":["source:'
                        + _VALID_SOURCE_ID
                        + '"],"confidence":0.42}>>'
                        "Challenge row."
                    ),
                    "parent_ref": "draft-1",
                },
            ],
        )
        self.assertEqual(first.comments_added, 2)
        first_by_uid = {row["comment_uid"]: row for row in first.merged_comments}
        second_by_uid = {row["comment_uid"]: row for row in second.merged_comments}
        self.assertEqual(set(first_by_uid.keys()), set(second_by_uid.keys()))
        for comment_uid, row in first_by_uid.items():
            self.assertEqual(row["permalink"], f"#{comment_uid}")
            self.assertEqual(row["thread_state_key"], comment_uid)
            self.assertEqual(row["thread_expansion_key"], comment_uid)
            self.assertEqual(row["score_assessment"]["score"], row["social_vote"]["score"])
            self.assertTrue(row["score_assessment"]["rationale"])
            self.assertEqual(row["social_vote"], second_by_uid[comment_uid]["social_vote"])

        updated_page = apply_merged_comments_to_page(
            page_payload={"topic_id": "topic-alpha", "title": "Alpha"},
            page_ref="topic:topic-alpha",
            merged_comments=first.merged_comments,
        )
        moderator_outcomes = updated_page["comment_section"]["moderator_outcomes"]
        self.assertTrue(moderator_outcomes["moderator_check"].startswith("- Moderator Check:"))
        self.assertEqual(
            set(moderator_outcomes["guardrail_checks"].keys()),
            {"claim_citation", "anti_repetition", "strongest_opposing_point_ack"},
        )
        self.assertIn("Consensus", moderator_outcomes["outcome_sections"])
        self.assertIn("Open Disagreements", moderator_outcomes["outcome_sections"])
        self.assertIn("Missing Evidence Priorities", moderator_outcomes["outcome_sections"])


if __name__ == "__main__":
    unittest.main()
