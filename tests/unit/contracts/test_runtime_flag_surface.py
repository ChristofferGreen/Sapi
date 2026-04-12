from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import scripts.create_comments as create_comments_entrypoint
import scripts.evaluate_source as evaluate_source_entrypoint
import scripts.generate_profiles as generate_profiles_entrypoint
import scripts.ingest_source as ingest_source_entrypoint
import scripts.query as query_entrypoint


REPO_ROOT = Path(__file__).resolve().parents[3]

_EXPECTED_RUNTIME_FLAGS: set[str] = {
    "--llm-backend",
    "--llm-model",
    "--llm-reasoning-effort",
    "--llm-timeout-secs",
    "--llm-trace",
    "--llm-trace-dir",
    "--trace-llm-io",
    "--mock-llm",
    "--warning-budget",
    "--run-search-visibility",
    "--site-presentation-mode",
    "--enable-source-index",
}


class RuntimeFlagSurfaceContractTests(unittest.TestCase):
    def test_semantic_entrypoints_expose_shared_runtime_flag_surface(self) -> None:
        parser_builders = [
            ingest_source_entrypoint.build_parser,
            query_entrypoint.build_parser,
            create_comments_entrypoint.build_parser,
            generate_profiles_entrypoint.build_parser,
            evaluate_source_entrypoint.build_parser,
        ]
        for builder in parser_builders:
            with self.subTest(parser_builder=builder.__module__):
                parser = builder()
                option_strings = set(parser._option_string_actions.keys())
                self.assertTrue(
                    _EXPECTED_RUNTIME_FLAGS.issubset(option_strings),
                    msg=f"missing runtime flags in {builder.__module__}: "
                    f"{sorted(_EXPECTED_RUNTIME_FLAGS - option_strings)}",
                )

    def test_runtime_flag_defaults_are_consistent_across_semantic_entrypoints(self) -> None:
        parser_cases = [
            (
                ingest_source_entrypoint.build_parser(),
                ["alpha", "source.txt", "--registry-path", "/tmp/registry.toml"],
            ),
            (
                query_entrypoint.build_parser(),
                ["alpha", "what is this", "--registry-path", "/tmp/registry.toml"],
            ),
            (
                create_comments_entrypoint.build_parser(),
                ["alpha", "--registry-path", "/tmp/registry.toml", "--count", "5"],
            ),
            (
                generate_profiles_entrypoint.build_parser(),
                ["alpha", "--registry-path", "/tmp/registry.toml"],
            ),
            (
                evaluate_source_entrypoint.build_parser(),
                ["alpha", "source.txt", "--registry-path", "/tmp/registry.toml"],
            ),
        ]
        for parser, argv in parser_cases:
            with self.subTest(parser=parser.prog):
                args = parser.parse_args(argv)
                self.assertEqual(args.llm_backend, "openai")
                self.assertEqual(args.llm_model, "gpt-5")
                self.assertEqual(args.llm_reasoning_effort, "high")
                self.assertEqual(args.llm_timeout_secs, 120)
                self.assertEqual(args.warning_budget, 200)
                self.assertEqual(args.run_search_visibility, "auto")
                self.assertEqual(args.site_presentation_mode, "public")
                self.assertFalse(args.llm_trace)
                self.assertFalse(args.trace_llm_io)
                self.assertFalse(args.mock_llm)
                self.assertFalse(args.enable_source_index)
                self.assertIsNone(args.llm_trace_dir)

    def test_invalid_trace_dir_combination_fails_fast_with_clear_error(self) -> None:
        commands = [
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "ingest_source.py"),
                "alpha",
                "source.txt",
                "--registry-path",
                "/tmp/registry.toml",
                "--llm-trace-dir",
                "/tmp/trace",
            ],
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "query.py"),
                "alpha",
                "question",
                "--registry-path",
                "/tmp/registry.toml",
                "--llm-trace-dir",
                "/tmp/trace",
            ],
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "create_comments.py"),
                "alpha",
                "--registry-path",
                "/tmp/registry.toml",
                "--count",
                "5",
                "--llm-trace-dir",
                "/tmp/trace",
            ],
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "generate_profiles.py"),
                "alpha",
                "--registry-path",
                "/tmp/registry.toml",
                "--llm-trace-dir",
                "/tmp/trace",
            ],
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "evaluate_source.py"),
                "alpha",
                "source.txt",
                "--registry-path",
                "/tmp/registry.toml",
                "--llm-trace-dir",
                "/tmp/trace",
            ],
        ]
        for command in commands:
            with self.subTest(command=Path(command[1]).name):
                result = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("--llm-trace-dir requires trace emission", result.stderr)


if __name__ == "__main__":
    unittest.main()
