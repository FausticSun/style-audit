"""Integration-level tests for project configuration and command behavior."""

import json
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from style_audit.cli import build_parser, main, run
from style_audit.config import load_config
from style_audit.models import AuditError


class ConfigTests(unittest.TestCase):
    def test_defaults_and_nested_pyproject_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            nested = project / "docs" / "nested"
            nested.mkdir(parents=True)
            (project / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["NAS001"]\noutput = "json"\n', encoding="utf-8"
            )
            self.assertEqual(load_config(root).include, ("*.md", "*.markdown", "*.rst", "*.txt"))
            config = load_config(nested)
            self.assertEqual(config.root, project)
            self.assertEqual(config.select, ("NAS001",))
            self.assertEqual(config.output, "json")

    def test_invalid_toml_or_llm_configuration_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            config = project / "pyproject.toml"
            config.write_text("[tool.style-audit\n", encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "cannot load configuration"):
                load_config(project)
            config.write_text("[tool.style-audit.llm]\nenabled = true\n", encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "model is required"):
                load_config(project)
            config.write_text('[tool.style-audit]\ninclude = "*.md"\n', encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "include must be an array"):
                load_config(project)

    def test_threshold_defaults_and_numeric_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(load_config(root).llm_threshold, 0.8)
            config_path = root / "pyproject.toml"
            for literal, expected in (("0", 0.0), ("1", 1.0), ("0.65", 0.65)):
                with self.subTest(literal=literal):
                    config_path.write_text(
                        f"[tool.style-audit.llm]\nthreshold = {literal}\n", encoding="utf-8"
                    )
                    config = load_config(root)
                    self.assertEqual(config.llm_threshold, expected)
                    self.assertIsInstance(config.llm_threshold, float)

    def test_threshold_configuration_rejects_non_numeric_nonfinite_and_out_of_range(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "pyproject.toml"
            for literal in (
                "true", "false", '"0.8"', "[]", "{}",
                "nan", "inf", "-inf", "-0.01", "1.01",
            ):
                with self.subTest(literal=literal):
                    config_path.write_text(
                        f"[tool.style-audit.llm]\nthreshold = {literal}\n", encoding="utf-8"
                    )
                    with self.assertRaisesRegex(AuditError, "threshold"):
                        load_config(root)


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        completion = patch(
            "style_audit.llm.litellm.completion",
            side_effect=AssertionError("CLI tests must not make live chat provider calls"),
        )
        self.addCleanup(completion.stop)
        completion.start()

    def test_directory_config_selection_exclusions_and_json_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["NAS001"]\noutput = "json"\n', encoding="utf-8"
            )
            docs = root / "docs"
            docs.mkdir()
            (docs / "draft.md").write_text("The robust integration shipped.\n", encoding="utf-8")
            (docs / "ignored.txt").write_text("The delve into detail was long.\n", encoding="utf-8")
            excluded = root / ".venv"
            excluded.mkdir()
            (excluded / "example.md").write_text("A robust example.\n", encoding="utf-8")

            args = build_parser().parse_args([str(root)])
            code, stdout = run(args, cwd=root)
            self.assertEqual(code, 1)
            report = json.loads(stdout)
            self.assertEqual(len(report["findings"]), 2)
            self.assertEqual([item["path"] for item in report["findings"]], ["docs/draft.md", "docs/ignored.txt"])
            self.assertEqual({item["code"] for item in report["findings"]}, {"NAS001"})

    def test_clean_stdin_and_explicit_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = build_parser().parse_args(["-", "--stdin-filename", "draft.txt"])
            code, stdout = run(args, "Ordinary clear prose.", root)
            self.assertEqual((code, stdout), (0, ""))

            args = build_parser().parse_args(["-", "--select", "NAS002"])
            code, stdout = run(args, "# 🌿 Heading", root)
            self.assertEqual(code, 1)
            self.assertIn("NAS002", stdout)

    def test_input_errors_and_llm_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = build_parser().parse_args(["missing.md"])
            with self.assertRaisesRegex(AuditError, "does not exist"):
                run(args, cwd=root)

            args = build_parser().parse_args(["-", "--select", "NAS101"])
            with self.assertRaisesRegex(AuditError, "requires an explicit model"):
                run(args, "Some prose.", root)

            args = build_parser().parse_args(["-", "--select", "NAS001"])
            code, _ = run(args, "The robust parser.", root)
            self.assertEqual(code, 1)

            args = build_parser().parse_args(["-", "--ignore", "NAS999"])
            with self.assertRaisesRegex(AuditError, "unknown rule selector"):
                run(args, "Text", root)


    def test_readability_config_selection_ignore_and_cli_override(self) -> None:
        source = (
            "Memory freshness allocation envelope changed.\n"
            "The proposal expects the reader to calendar the premise.\n"
            "A robust parser shipped.\n"
        )

        def provider(*, state, questions, **kwargs):
            probabilities = {
                "RDL104": 0.95 if "Memory freshness allocation envelope" in state["text"] else 0.05,
                "RDL106": 0.95 if "proposal expects" in state["text"] else 0.05,
            }
            return SimpleNamespace(answers={
                code: SimpleNamespace(type="noul", noul=probabilities.get(code, 0.05))
                for code in questions
            })

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["RDL"]\nignore = ["RDL104"]\noutput = "json"\n'
                '[tool.style-audit.llm]\nmodel = "microsoft/microsoft-decision-1"\n',
                encoding="utf-8",
            )
            with patch("style_audit.llm.litellm.systemone", side_effect=provider):
                code, output = run(build_parser().parse_args(["-"]), source, root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["code"], item["line"], item["column"], item["evidence"])
                 for item in json.loads(output)["findings"]],
                [("RDL106", 2, 1, "The proposal expects the reader to calendar the premise.")],
            )

            with patch("style_audit.llm.litellm.systemone") as provider_call:
                code, output = run(build_parser().parse_args(["-", "--select", "NAS001"]), source, root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["code"], item["line"], item["column"]) for item in json.loads(output)["findings"]],
                [("NAS001", 3, 3)],
            )
            provider_call.assert_not_called()

            with patch("style_audit.llm.litellm.systemone") as provider_call:
                code, output = run(build_parser().parse_args(["-", "--ignore", "RDL"]), source, root)
            self.assertEqual((code, json.loads(output)["findings"]), (0, []))
            provider_call.assert_not_called()


    @staticmethod
    def _decision_response(probability):
        return SimpleNamespace(answers={
            "NAS106": SimpleNamespace(type="noul", noul=probability),
        })

    def test_cli_threshold_overrides_config_in_observable_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for configured, override, expected_code in (
                (0.7, None, 0),
                (0.7, 0.6, 1),
                (0.6, 0.9, 0),
            ):
                with self.subTest(configured=configured, override=override):
                    (root / "pyproject.toml").write_text(
                        '[tool.style-audit]\nselect = ["NAS106"]\n'
                        '[tool.style-audit.llm]\nenabled = true\n'
                        'model = "microsoft/microsoft-decision-1"\n'
                        f'threshold = {configured}\n',
                        encoding="utf-8",
                    )
                    options = ["-", "--format", "json"]
                    if override is not None:
                        options.extend(["--threshold", str(override)])
                    args = build_parser().parse_args(options)
                    with patch("style_audit.llm.litellm.systemone", return_value=self._decision_response(0.65)):
                        code, stdout = run(args, "Visible paragraph.", root)
                    self.assertEqual(code, expected_code)
                    report = json.loads(stdout)
                    self.assertEqual(len(report["findings"]), expected_code)
                    if expected_code:
                        self.assertEqual(report["findings"][0]["code"], "NAS106")
                        self.assertEqual(report["findings"][0]["evidence"], "Visible paragraph.")

    def test_cli_threshold_endpoints_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for threshold, probability, expected_code in ((0, 0, 1), (1, 0, 0), (1, 1, 1)):
                with self.subTest(threshold=threshold, probability=probability):
                    args = build_parser().parse_args([
                        "-", "--select", "NAS106", "--model", "microsoft/microsoft-decision-1",
                        "--threshold", str(threshold), "--format", "json",
                    ])
                    with patch("style_audit.llm.litellm.systemone", return_value=self._decision_response(probability)):
                        code, stdout = run(args, "Visible paragraph.", root)
                    self.assertEqual(code, expected_code)
                    self.assertEqual(len(json.loads(stdout)["findings"]), expected_code)

    def test_cli_threshold_rejects_non_numeric_input(self) -> None:
        for value in ("true", "false", "not-a-number"):
            with self.subTest(value=value):
                with patch("sys.stderr", new_callable=StringIO) as stderr:
                    with self.assertRaises(SystemExit) as raised:
                        build_parser().parse_args(["-", f"--threshold={value}"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("--threshold", stderr.getvalue())

    def test_invalid_cli_thresholds_fail_before_any_provider_call(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for value in ("nan", "inf", "-inf", "-0.01", "1.01"):
                with self.subTest(value=value):
                    args = build_parser().parse_args([
                        "-", "--select", "NAS106", "--model", "microsoft/microsoft-decision-1",
                        f"--threshold={value}",
                    ])
                    with patch("style_audit.llm.litellm.systemone") as decision_provider:
                        with patch("style_audit.llm.litellm.completion") as chat_provider:
                            with self.assertRaisesRegex(AuditError, "threshold"):
                                run(args, "Visible paragraph.", root)
                    decision_provider.assert_not_called()
                    chat_provider.assert_not_called()

    def test_invalid_threshold_configuration_is_not_hidden_by_cli_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                "[tool.style-audit.llm]\nthreshold = true\n", encoding="utf-8"
            )
            args = build_parser().parse_args(["-", "--select", "NAS001", "--threshold", "0.5"])
            with self.assertRaisesRegex(AuditError, "threshold"):
                run(args, "Ordinary prose.", root)

    def test_deterministic_only_selection_never_calls_a_provider_even_with_llm_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "pyproject.toml"
            for configured in (False, True):
                config_path.write_text(
                    '[tool.style-audit]\nselect = ["NAS106"]\n'
                    '[tool.style-audit.llm]\nenabled = true\n'
                    'model = "microsoft/microsoft-decision-1"\n'
                    if configured else "[tool.style-audit]\n",
                    encoding="utf-8",
                )
                for flags in (
                    ["--llm"],
                    ["--model", "microsoft/microsoft-decision-1"],
                    ["--llm", "--model", "microsoft/microsoft-decision-1", "--threshold", "0"],
                ):
                    with self.subTest(configured=configured, flags=flags):
                        args = build_parser().parse_args([
                            "-", "--select", "NAS001", "--format", "json", *flags,
                        ])
                        with patch("style_audit.llm.litellm.systemone") as decision_provider:
                            with patch("style_audit.llm.litellm.completion") as chat_provider:
                                code, stdout = run(args, "The robust parser.", root)
                        self.assertEqual(code, 1)
                        self.assertEqual(
                            {finding["code"] for finding in json.loads(stdout)["findings"]}, {"NAS001"}
                        )
                        decision_provider.assert_not_called()
                        chat_provider.assert_not_called()

    def test_provider_or_answer_failure_emits_error_without_a_partial_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "pyproject.toml"
            config_path.write_text("[tool.style-audit]\n", encoding="utf-8")
            first = root / "first.md"
            second = root / "second.md"
            first.write_text("A robust first paragraph.", encoding="utf-8")
            second.write_text("Second visible paragraph.", encoding="utf-8")
            for failure in (
                RuntimeError("decision provider offline"),
                SimpleNamespace(answers={}),
            ):
                with self.subTest(failure=failure):
                    with patch("style_audit.llm.litellm.systemone", side_effect=[
                        self._decision_response(0.9), failure,
                    ]):
                        with patch("sys.stdout", new_callable=StringIO) as stdout:
                            with patch("sys.stderr", new_callable=StringIO) as stderr:
                                code = main([
                                    str(first), str(second), "--config", str(config_path),
                                    "--select", "NAS001,NAS106", "--model", "microsoft/microsoft-decision-1",
                                    "--format", "json",
                                ])
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn("style-audit: error:", stderr.getvalue())
                    if isinstance(failure, RuntimeError):
                        self.assertIn("decision provider offline", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
