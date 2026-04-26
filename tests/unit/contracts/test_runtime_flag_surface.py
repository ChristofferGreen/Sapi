from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path

import scripts.create_comments as create_comments_entrypoint
import scripts.evaluate_source as evaluate_source_entrypoint
import scripts.generate_profiles as generate_profiles_entrypoint
import scripts.ingest_source as ingest_source_entrypoint
import scripts.query as query_entrypoint
from sapi.core.runtime_config import DEFAULT_LIVE_LLM_MODEL


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
    def test_ingest_entrypoint_does_not_expose_removed_mode_flags(self) -> None:
        parser = ingest_source_entrypoint.build_parser()
        option_strings = set(parser._option_string_actions.keys())
        self.assertNotIn("--source-only", option_strings)
        self.assertNotIn("--query-only", option_strings)

    def test_comments_entrypoint_does_not_expose_removed_alias_flags(self) -> None:
        parser = create_comments_entrypoint.build_parser()
        option_strings = set(parser._option_string_actions.keys())
        self.assertNotIn("--user", option_strings)
        self.assertNotIn("--page", option_strings)
        self.assertNotIn("--comment-web-evidence", option_strings)

    def test_comments_entrypoint_rejects_removed_alias_flags_as_unknown_arguments(self) -> None:
        parser = create_comments_entrypoint.build_parser()
        removed_alias_cases = [
            (["--user", "persona-maya-santoro"], "--user persona-maya-santoro"),
            (["--page", "topic:topic-a"], "--page topic:topic-a"),
            (["--comment-web-evidence"], "--comment-web-evidence"),
        ]
        base_argv = ["alpha", "--registry-path", "/tmp/registry.toml", "--count", "5"]
        for removed_alias_argv, expected_fragment in removed_alias_cases:
            stderr = io.StringIO()
            with self.subTest(flag=removed_alias_argv[0]), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc:
                    parser.parse_args([*base_argv, *removed_alias_argv])
            self.assertEqual(exc.exception.code, 2)
            self.assertIn("unrecognized arguments:", stderr.getvalue())
            self.assertIn(expected_fragment, stderr.getvalue())

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
                self.assertEqual(args.llm_backend, "codex")
                self.assertEqual(args.llm_model, DEFAULT_LIVE_LLM_MODEL)
                self.assertEqual(args.llm_reasoning_effort, "high")
                self.assertIsNone(args.llm_timeout_secs)
                self.assertEqual(args.warning_budget, 200)
                self.assertEqual(args.run_search_visibility, "auto")
                self.assertEqual(args.site_presentation_mode, "public")
                self.assertFalse(args.llm_trace)
                self.assertFalse(args.trace_llm_io)
                self.assertFalse(args.mock_llm)
                self.assertFalse(args.enable_source_index)
                self.assertIsNone(args.llm_trace_dir)

    def test_runtime_flags_accept_no_timeout_sentinel(self) -> None:
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
                args = parser.parse_args([*argv, "--llm-timeout-secs", "none"])
                self.assertIsNone(args.llm_timeout_secs)

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
