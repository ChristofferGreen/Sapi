from __future__ import annotations

import unittest

from sapi.profiles.history import PersonaHistoryMetrics, apply_persona_history_update


class PersonaHistoryUpdateSemanticsUnitTests(unittest.TestCase):
    def test_first_write_creates_entry(self) -> None:
        update = apply_persona_history_update(
            current_payload=None,
            space_name="alpha",
            persona_id="persona-1",
            metrics=PersonaHistoryMetrics(
                comments_total=3,
                unsupported_claim_rate=0.0,
                retraction_rate=0.0,
                forecast_accuracy=0.59,
            ),
            as_of_date="2026-04-13",
        )
        self.assertEqual(update.status, "generated")
        self.assertEqual(update.payload["schema_version"], "persona_profile_history_v1")
        self.assertEqual(len(update.payload["entries"]), 1)

    def test_same_day_changed_metrics_overwrites_last_entry(self) -> None:
        current_payload = {
            "schema_version": "persona_profile_history_v1",
            "space_name": "alpha",
            "persona_id": "persona-1",
            "entries": [
                {
                    "as_of": "2026-04-13",
                    "comments_total": 1,
                    "unsupported_claim_rate": 0.0,
                    "retraction_rate": 0.0,
                    "forecast_accuracy": 0.53,
                }
            ],
        }
        update = apply_persona_history_update(
            current_payload=current_payload,
            space_name="alpha",
            persona_id="persona-1",
            metrics=PersonaHistoryMetrics(
                comments_total=4,
                unsupported_claim_rate=0.0,
                retraction_rate=0.0,
                forecast_accuracy=0.62,
            ),
            as_of_date="2026-04-13",
        )
        self.assertEqual(update.status, "updated")
        entries = update.payload["entries"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["comments_total"], 4)

    def test_new_day_appends_only_when_non_date_metrics_change(self) -> None:
        baseline_payload = {
            "schema_version": "persona_profile_history_v1",
            "space_name": "alpha",
            "persona_id": "persona-1",
            "entries": [
                {
                    "as_of": "2026-04-13",
                    "comments_total": 2,
                    "unsupported_claim_rate": 0.0,
                    "retraction_rate": 0.0,
                    "forecast_accuracy": 0.56,
                }
            ],
        }
        unchanged = apply_persona_history_update(
            current_payload=baseline_payload,
            space_name="alpha",
            persona_id="persona-1",
            metrics=PersonaHistoryMetrics(
                comments_total=2,
                unsupported_claim_rate=0.0,
                retraction_rate=0.0,
                forecast_accuracy=0.56,
            ),
            as_of_date="2026-04-14",
        )
        self.assertEqual(unchanged.status, "reused")
        self.assertEqual(len(unchanged.payload["entries"]), 1)

        changed = apply_persona_history_update(
            current_payload=baseline_payload,
            space_name="alpha",
            persona_id="persona-1",
            metrics=PersonaHistoryMetrics(
                comments_total=5,
                unsupported_claim_rate=0.2,
                retraction_rate=0.0,
                forecast_accuracy=0.65,
            ),
            as_of_date="2026-04-14",
        )
        self.assertEqual(changed.status, "updated")
        entries = changed.payload["entries"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[-1]["as_of"], "2026-04-14")
        self.assertEqual(entries[-1]["comments_total"], 5)


if __name__ == "__main__":
    unittest.main()
