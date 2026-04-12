from __future__ import annotations

from dataclasses import is_dataclass
import unittest

from sapi.contracts.domain_models import (
    Claim,
    Comment,
    Persona,
    Relation,
    Site,
    Space,
    Source,
    SubSpace,
    TopicPage,
    validate_boundary_invariants,
)


class DomainModelContractTests(unittest.TestCase):
    def test_core_entities_are_represented_as_typed_models(self) -> None:
        site = Site(site_name="My Site")
        space = Space(space_name="alpha", site_name=site.site_name)
        subspace = SubSpace(space_name="alpha-policy", parent_space_name=space.space_name)
        source = Source(source_id="source-paper--aaaaaaaaaaaa", space_name=space.space_name)
        claim_a = Claim(
            claim_id="claim-main-a--bbbbbbbbbbbb",
            source_id=source.source_id,
            space_name=space.space_name,
        )
        claim_b = Claim(
            claim_id="claim-main-b--cccccccccccc",
            source_id=source.source_id,
            space_name=space.space_name,
        )
        relation = Relation(
            relation_type="supports",
            src_claim_id=claim_a.claim_id,
            dst_claim_id=claim_b.claim_id,
            relation_id=f"supports:{claim_a.claim_id}->{claim_b.claim_id}",
            space_name=space.space_name,
        )
        topic = TopicPage(
            topic_id="topic-main--dddddddddddd",
            space_name=space.space_name,
            claim_ids=(claim_a.claim_id, claim_b.claim_id),
            source_ids=(source.source_id,),
            narrative_id="topic-main--dddddddddddd",
        )
        persona = Persona(
            persona_id="persona_1",
            display_name="Persona One",
            full_name="Persona One",
            id="persona_1",
        )
        comment = Comment(
            comment_uid="comment-root--abcde12345",
            persona_id=persona.persona_id,
            space_name=space.space_name,
            page_type="topic",
            page_id=topic.topic_id,
        )

        for model in (site, space, subspace, source, claim_a, relation, topic, persona, comment):
            self.assertTrue(is_dataclass(model))

        validate_boundary_invariants(
            space=space,
            subspaces=[subspace],
            sources=[source],
            claims=[claim_a, claim_b],
            relations=[relation],
            topics=[topic],
            personas=[persona],
            comments=[comment],
        )

    def test_identity_alias_constraints_fail_fast(self) -> None:
        with self.assertRaises(ValueError):
            Persona(
                persona_id="persona_1",
                display_name="Persona One",
                id="persona_mismatch",
            )

        with self.assertRaises(ValueError):
            TopicPage(
                topic_id="topic-main--dddddddddddd",
                narrative_id="topic-other--eeeeeeeeeeee",
                space_name="alpha",
                claim_ids=(),
                source_ids=(),
            )

    def test_boundary_invariants_fail_fast_on_invalid_relationships(self) -> None:
        space = Space(space_name="alpha", site_name="My Site")
        source = Source(source_id="source-paper--aaaaaaaaaaaa", space_name="alpha")
        claim = Claim(
            claim_id="claim-main-a--bbbbbbbbbbbb",
            source_id=source.source_id,
            space_name="alpha",
        )
        persona = Persona(persona_id="persona_1", display_name="Persona One")
        topic = TopicPage(
            topic_id="topic-main--dddddddddddd",
            space_name="alpha",
            claim_ids=(claim.claim_id,),
            source_ids=(source.source_id,),
        )
        comment = Comment(
            comment_uid="comment-root--abcde12345",
            persona_id=persona.persona_id,
            space_name="alpha",
            page_type="topic",
            page_id=topic.topic_id,
        )

        with self.assertRaises(ValueError):
            cross_space_source = Source(source_id=source.source_id, space_name="beta")
            validate_boundary_invariants(space=space, sources=[cross_space_source])

        with self.assertRaises(ValueError):
            bad_claim = Claim(
                claim_id="claim-main-b--cccccccccccc",
                source_id="source-missing--ffffffffffff",
                space_name="alpha",
            )
            validate_boundary_invariants(space=space, sources=[source], claims=[bad_claim])

        with self.assertRaises(ValueError):
            bad_relation = Relation(
                relation_type="supports",
                src_claim_id=claim.claim_id,
                dst_claim_id="claim-missing--eeeeeeeeeeee",
                relation_id=f"supports:{claim.claim_id}->claim-missing--eeeeeeeeeeee",
                space_name="alpha",
            )
            validate_boundary_invariants(
                space=space,
                sources=[source],
                claims=[claim],
                relations=[bad_relation],
            )

        with self.assertRaises(ValueError):
            bad_comment = Comment(
                comment_uid="comment-root--abcde12345",
                persona_id=persona.persona_id,
                space_name="alpha",
                page_type="topic",
                page_id="topic-missing--ffffffffffff",
            )
            validate_boundary_invariants(
                space=space,
                sources=[source],
                claims=[claim],
                topics=[topic],
                personas=[persona],
                comments=[bad_comment],
            )


if __name__ == "__main__":
    unittest.main()
