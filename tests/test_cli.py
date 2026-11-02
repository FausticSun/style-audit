"""Integration-level tests for project configuration and command behavior."""

import json
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from click.testing import CliRunner
from style_audit.cli import CLIOptions, build_cli, main, run
from style_audit.config import load_config
from style_audit.models import AuditError


def _parse_options(arguments: list[str]) -> CLIOptions:
    command = build_cli()
    with command.make_context("style-audit", list(arguments)) as context:
        return CLIOptions(**context.params)


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

    def test_rule_word_lists_parse_and_reject_non_arrays(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "pyproject.toml"
            config_path.write_text(
                '[tool.style-audit.no-ai-slop]\nallowed-words = ["robust"]\n'
                'disallowed-words = ["excellent"]\n'
                '[tool.style-audit.ste]\nallowed-words = ["actuator"]\n'
                'disallowed-words = ["snapshot"]\n',
                encoding="utf-8",
            )
            config = load_config(root)
            self.assertEqual(config.nas_allowed_words, ("robust",))
            self.assertEqual(config.nas_disallowed_words, ("excellent",))
            self.assertEqual(config.ste_allowed_words, ("actuator",))
            self.assertEqual(config.ste_disallowed_words, ("snapshot",))

            config_path.write_text(
                '[tool.style-audit.ste]\ndisallowed-words = "snapshot"\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AuditError, "disallowed-words must be an array"):
                load_config(root)

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
            generated_site = root / "site"
            generated_site.mkdir()
            (generated_site / "draft.feature").write_text(
                "Feature: robust generated page.\n", encoding="utf-8"
            )

            args = _parse_options([str(root)])
            code, stdout = run(args, cwd=root)
            self.assertEqual(code, 1)
            report = json.loads(stdout)
            self.assertEqual(len(report["findings"]), 2)
            self.assertEqual([item["path"] for item in report["findings"]], ["docs/draft.md", "docs/ignored.txt"])
            self.assertEqual({item["code"] for item in report["findings"]}, {"NAS001"})

    def test_clean_stdin_and_explicit_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = _parse_options(["-", "--stdin-filename", "draft.txt"])
            code, stdout = run(args, "Ordinary clear prose.", root)
            self.assertEqual((code, stdout), (0, ""))

            args = _parse_options(["-", "--select", "NAS002"])
            code, stdout = run(args, "# 🌿 Heading", root)
            self.assertEqual(code, 1)
            self.assertIn("NAS002", stdout)

    def test_input_errors_and_llm_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = _parse_options(["missing.md"])
            with self.assertRaisesRegex(AuditError, "does not exist"):
                run(args, cwd=root)

            args = _parse_options(["-", "--select", "NAS101"])
            with self.assertRaisesRegex(AuditError, "requires an explicit model"):
                run(args, "Some prose.", root)

            args = _parse_options(["-", "--select", "NAS001"])
            code, _ = run(args, "The robust parser.", root)
            self.assertEqual(code, 1)

            args = _parse_options(["-", "--ignore", "NAS999"])
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
                '[tool.style-audit.llm]\nmodel = "azure-maas-judge/Decision-1"\n',
                encoding="utf-8",
            )
            with patch("style_audit.llm.litellm.systemone", side_effect=provider):
                code, output = run(_parse_options(["-"]), source, root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["code"], item["line"], item["column"], item["evidence"])
                 for item in json.loads(output)["findings"]],
                [("RDL106", 2, 1, "The proposal expects the reader to calendar the premise.")],
            )

            with patch("style_audit.llm.litellm.systemone") as provider_call:
                code, output = run(_parse_options(["-", "--select", "NAS001"]), source, root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["code"], item["line"], item["column"]) for item in json.loads(output)["findings"]],
                [("NAS001", 3, 3)],
            )
            provider_call.assert_not_called()

            with patch("style_audit.llm.litellm.systemone") as provider_call:
                code, output = run(_parse_options(["-", "--ignore", "RDL"]), source, root)
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
                        'model = "azure-maas-judge/Decision-1"\n'
                        f'threshold = {configured}\n',
                        encoding="utf-8",
                    )
                    options = ["-", "--format", "json"]
                    if override is not None:
                        options.extend(["--threshold", str(override)])
                    args = _parse_options(options)
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
                    args = _parse_options([
                        "-", "--select", "NAS106", "--model", "azure-maas-judge/Decision-1",
                        "--threshold", str(threshold), "--format", "json",
                    ])
                    with patch("style_audit.llm.litellm.systemone", return_value=self._decision_response(probability)):
                        code, stdout = run(args, "Visible paragraph.", root)
                    self.assertEqual(code, expected_code)
                    self.assertEqual(len(json.loads(stdout)["findings"]), expected_code)

    def test_cli_threshold_rejects_non_numeric_input(self) -> None:
        runner = CliRunner()
        for value in ("true", "false", "not-a-number"):
            with self.subTest(value=value):
                result = runner.invoke(build_cli(), ["-", f"--threshold={value}"])
                self.assertEqual(result.exit_code, 2)
                self.assertIn("--threshold", result.output)

    def test_invalid_cli_thresholds_fail_before_any_provider_call(self) -> None:
        for value in ("nan", "inf", "-inf", "-0.01", "1.01"):
            with self.subTest(value=value):
                with patch("sys.stdin", StringIO("Visible paragraph.\n")):
                    with patch("sys.stdout", new_callable=StringIO):
                        with patch("sys.stderr", new_callable=StringIO) as stderr:
                            with patch("style_audit.llm.litellm.systemone") as decision_provider:
                                with patch("style_audit.llm.litellm.completion") as chat_provider:
                                    code = main([
                                        "-", "--select", "NAS106", "--model", "azure-maas-judge/Decision-1",
                                        f"--threshold={value}",
                                    ])
                self.assertEqual(code, 2)
                self.assertIn("--threshold", stderr.getvalue())
                decision_provider.assert_not_called()
                chat_provider.assert_not_called()

    def test_invalid_threshold_configuration_is_not_hidden_by_cli_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                "[tool.style-audit.llm]\nthreshold = true\n", encoding="utf-8"
            )
            args = _parse_options(["-", "--select", "NAS001", "--threshold", "0.5"])
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
                    'model = "azure-maas-judge/Decision-1"\n'
                    if configured else "[tool.style-audit]\n",
                    encoding="utf-8",
                )
                for flags in (
                    ["--llm"],
                    ["--model", "azure-maas-judge/Decision-1"],
                    ["--llm", "--model", "azure-maas-judge/Decision-1", "--threshold", "0"],
                ):
                    with self.subTest(configured=configured, flags=flags):
                        args = _parse_options([
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
                                    "--select", "NAS001,NAS106", "--model", "azure-maas-judge/Decision-1",
                                    "--format", "json",
                                ])
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn("style-audit: error:", stderr.getvalue())
                    if isinstance(failure, RuntimeError):
                        self.assertIn("LiteLLM Decisions call failed (RuntimeError)", stderr.getvalue())

    def test_directory_defaults_audit_python_docstrings_not_comments_or_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["NAS001"]\noutput = "json"\n', encoding="utf-8"
            )
            (root / "package.py").write_text(
                '# A robust comment.\n'
                'VALUE = "robust executable text"\n'
                'def scan():\n'
                '    """A robust parser."""\n'
                '    return "robust executable text"\n', encoding="utf-8"
            )
            (root / "types.pyi").write_text(
                '"""A robust interface."""\ndef scan() -> None: ...\n', encoding="utf-8"
            )
            (root / "README.md").write_text("A robust explanation.\n", encoding="utf-8")
            (root / "ignored.js").write_text("A robust unsupported file.\n", encoding="utf-8")
            excluded = root / ".venv"
            excluded.mkdir()
            (excluded / "invalid.py").write_text("def broken(:\n", encoding="utf-8")
            with patch("style_audit.llm.litellm.systemone") as decision_provider:
                with patch("style_audit.llm.litellm.completion") as chat_provider:
                    code, output = run(_parse_options([str(root)]), cwd=root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(finding["path"], finding["code"], finding["evidence"], finding["line"], finding["column"])
                 for finding in json.loads(output)["findings"]],
                [("README.md", "NAS001", "robust", 1, 3),
                 ("package.py", "NAS001", "robust", 4, 10),
                 ("types.pyi", "NAS001", "robust", 1, 6)],
            )
            decision_provider.assert_not_called()
            chat_provider.assert_not_called()

    def test_gherkin_double_quote_docstrings_hide_fixture_values(self) -> None:
        source = (
            "Feature: robust title\n"
            "  Scenario: fixture data stays hidden\n"
            "    Given the parser reads input\n"
            '      """\n'
            "      robust fixture value\n"
            '      """\n'
            "    Then the robust output appears\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            feature = root / "draft.feature"
            feature.write_text(source, encoding="utf-8")
            with patch("style_audit.llm.litellm.systemone") as decision_provider:
                code, output = run(
                    _parse_options([
                        str(feature), "--select", "NAS001", "--format", "json",
                    ]),
                    cwd=root,
                )
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["path"], item["code"], item["evidence"], item["line"], item["column"])
                 for item in json.loads(output)["findings"]],
                [("draft.feature", "NAS001", "robust", 1, 10),
                 ("draft.feature", "NAS001", "robust", 7, 14)],
            )
            decision_provider.assert_not_called()

    def test_python_include_exclude_and_rule_selection_keep_existing_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "src"
            source_dir.mkdir()
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\ninclude = ["src/*.pyi"]\nexclude = ["src/skip.pyi"]\n'
                'select = ["NAS001"]\noutput = "json"\n', encoding="utf-8"
            )
            (source_dir / "included.pyi").write_text(
                '"""A robust interface serves as a tracker."""\n', encoding="utf-8"
            )
            (source_dir / "skip.pyi").write_text("def excluded(:\n", encoding="utf-8")
            (source_dir / "not_included.py").write_text("def not_included(:\n", encoding="utf-8")
            for options, expected in (
                ([], ("NAS001", "robust", 1, 6)),
                (["--select", "NAS001,NAS003", "--ignore", "NAS001"],
                 ("NAS003", "serves as", 1, 23)),
            ):
                with self.subTest(options=options):
                    code, output = run(_parse_options([str(root), *options]), cwd=root)
                    self.assertEqual(code, 1)
                    findings = json.loads(output)["findings"]
                    self.assertEqual(
                        [(finding["path"], finding["code"], finding["evidence"],
                          finding["line"], finding["column"]) for finding in findings],
                        [("src/included.pyi", *expected)],
                    )

    def test_explicit_python_files_and_stdin_suffix_select_docstrings_only(self) -> None:
        source = (
            '# A robust comment.\n'
            'VALUE = "robust executable text"\n'
            'def documented():\n'
            '    """A robust parser."""\n'
            '    return "robust executable text"\n'
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("[tool.style-audit]\n", encoding="utf-8")
            for suffix in (".py", ".pyi"):
                for mode in ("file", "stdin"):
                    with self.subTest(suffix=suffix, mode=mode):
                        path = root / f"input{suffix}"
                        path.write_text(source, encoding="utf-8")
                        options = [str(path)] if mode == "file" else ["-", "--stdin-filename", path.name]
                        code, output = run(_parse_options([
                            *options, "--select", "NAS001", "--format", "json",
                        ]), source if mode == "stdin" else None, root)
                        self.assertEqual(code, 1)
                        self.assertEqual(
                            [(finding["path"], finding["evidence"], finding["line"], finding["column"])
                             for finding in json.loads(output)["findings"]],
                            [(path.name, "robust", 4, 10)],
                        )

    def test_python_comment_only_stdin_is_clean_but_other_suffixes_retain_prose(self) -> None:
        source = '# A robust comment.\nVALUE = "robust executable text"\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for filename, expected_code in (("input.py", 0), ("input.pyi", 0),
                                             ("input.txt", 1), ("<stdin>", 1)):
                with self.subTest(filename=filename):
                    with patch("style_audit.llm.litellm.systemone") as decision_provider:
                        with patch("style_audit.llm.litellm.completion") as chat_provider:
                            code, output = run(_parse_options([
                                "-", "--stdin-filename", filename, "--select", "NAS001,NAS106",
                                "--model", "azure-maas-judge/Decision-1", "--format", "json",
                            ] if expected_code == 0 else [
                                "-", "--stdin-filename", filename, "--select", "NAS001", "--format", "json",
                            ]), source, root)
                    self.assertEqual(code, expected_code)
                    findings = json.loads(output)["findings"]
                    self.assertEqual(
                        [(finding["evidence"], finding["line"], finding["column"]) for finding in findings],
                        [] if expected_code == 0 else [("robust", 1, 5)],
                    )
                    decision_provider.assert_not_called()
                    chat_provider.assert_not_called()

    def test_invalid_python_is_an_operational_error_before_any_provider_or_json(self) -> None:
        invalid = '"""A robust preamble."""\ndef broken(:\n    pass\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "pyproject.toml"
            config_path.write_text("[tool.style-audit]\n", encoding="utf-8")
            first = root / "a_valid.py"
            first.write_text('"""A robust earlier document."""\n', encoding="utf-8")
            for suffix in (".py", ".pyi"):
                invalid_path = root / f"z_invalid{suffix}"
                invalid_path.write_text(invalid, encoding="utf-8")
                for mode in ("file", "stdin"):
                    for model in ("openai/test-model", "azure-maas-judge/Decision-1"):
                        with self.subTest(suffix=suffix, mode=mode, model=model):
                            inputs = ([str(first), str(invalid_path)] if mode == "file" else
                                      ["-", "--stdin-filename", invalid_path.name, str(first)])
                            with patch("style_audit.llm.litellm.completion") as chat_provider:
                                with patch("style_audit.llm.litellm.systemone") as decision_provider:
                                    with patch("sys.stdin", StringIO(invalid)):
                                        with patch("sys.stdout", new_callable=StringIO) as stdout:
                                            with patch("sys.stderr", new_callable=StringIO) as stderr:
                                                code = main([
                                                    *inputs, "--config", str(config_path),
                                                    "--select", "NAS001,NAS106", "--model", model,
                                                    "--format", "json",
                                                ])
                            self.assertEqual(code, 2)
                            self.assertEqual(stdout.getvalue(), "")
                            self.assertIn("style-audit: error:", stderr.getvalue())
                            self.assertIn(invalid_path.name, stderr.getvalue())
                            self.assertRegex(stderr.getvalue(), r"(?:line |:)2(?:[:, ]|$)")
                            chat_provider.assert_not_called()
                            decision_provider.assert_not_called()

    def test_python_file_accepts_utf8_bom_and_reports_original_unicode_columns(self) -> None:
        source = (
            '\ufeff"""Élodie 🌿 wrote a robust parser."""\n'
            '# A robust comment is excluded.\n'
            'VALUE = "robust executable text"\n'
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "bom.py"
            path.write_bytes(source.encode("utf-8"))
            with patch("style_audit.llm.litellm.systemone") as decision_provider:
                with patch("style_audit.llm.litellm.completion") as chat_provider:
                    code, output = run(_parse_options([
                        str(path), "--select", "NAS001", "--format", "json",
                    ]), cwd=root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(finding["path"], finding["code"], finding["evidence"], finding["line"],
                  finding["column"], finding["end_line"], finding["end_column"])
                 for finding in json.loads(output)["findings"]],
                [("bom.py", "NAS001", "robust", 1, source.index("robust") + 1, 1, 28)],
            )
            decision_provider.assert_not_called()
            chat_provider.assert_not_called()

    def test_python_file_and_stdin_preserve_unicode_crlf_and_decision_evidence(self) -> None:
        source = (
            '# Café 🌿\r\n'
            'def café():\r\n'
            '    """🌿 Café marks a pivotal moment.\r\n'
            '    Details follow.\r\n'
            '    """\r\n'
        )
        expected_text = "🌿 Café marks a pivotal moment.\nDetails follow."
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "unicode.py"
            path.write_bytes(source.encode("utf-8"))
            for mode in ("file", "stdin"):
                with self.subTest(mode=mode):
                    contexts = []

                    def provider(*, state, questions, **kwargs):
                        contexts.append(state)
                        return SimpleNamespace(answers={
                            "NAS101": SimpleNamespace(type="noul", noul=0.9),
                        })

                    inputs = [str(path)] if mode == "file" else ["-", "--stdin-filename", path.name]
                    with patch("style_audit.llm.litellm.systemone", side_effect=provider):
                        code, output = run(_parse_options([
                            *inputs, "--select", "NAS101", "--model", "azure-maas-judge/Decision-1",
                            "--format", "json",
                        ]), source if mode == "stdin" else None, root)
                    self.assertEqual(code, 1)
                    self.assertEqual(contexts, [{"scope": "paragraph", "text": expected_text}])
                    self.assertEqual(
                        [(finding["path"], finding["code"], finding["line"], finding["column"],
                          finding["end_line"], finding["end_column"], finding["evidence"])
                         for finding in json.loads(output)["findings"]],
                        [("unicode.py", "NAS101", 3, 8, 4, 20,
                          "🌿 Café marks a pivotal moment.\r\n    Details follow.")],
                    )

    def test_python_chat_context_is_private_and_findings_use_original_locations(self) -> None:
        source = (
            '# SECRET_COMMENT should not be sent.\n'
            'def first():\n'
            '    """The first report marks a pivotal moment."""\n'
            '    return "SECRET_FIRST_CODE"\n'
            'def second():\n'
            '    """The second report stays concrete."""\n'
            '    return "SECRET_SECOND_CODE"\n'
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contexts = []

            def provider(*, messages, **kwargs):
                context = json.loads(messages[-1]["content"])
                contexts.append(context)
                self.assertNotIn("SECRET_", json.dumps(messages))
                findings = []
                if context["text"] == "The first report marks a pivotal moment.":
                    findings = [{
                        "code": "NAS106", "evidence": "marks a pivotal moment",
                        "reason": "This inflates importance without a concrete fact.",
                    }]
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                    content=json.dumps({"findings": findings})
                ))])

            with patch("style_audit.llm.litellm.completion", side_effect=provider):
                code, output = run(_parse_options([
                    "-", "--stdin-filename", "private.py", "--select", "NAS106",
                    "--model", "openai/test-model", "--format", "json",
                ]), source, root)
            self.assertEqual(code, 1)
            self.assertEqual(contexts, [
                {"scope": "sentence", "text": "The first report marks a pivotal moment."},
                {"scope": "sentence", "text": "The second report stays concrete."},
            ])
            self.assertEqual(
                [(finding["path"], finding["code"], finding["evidence"], finding["line"], finding["column"])
                 for finding in json.loads(output)["findings"]],
                [("private.py", "NAS106", "marks a pivotal moment", 3, 25)],
            )

    def test_chat_quote_from_python_code_fails_without_partial_json(self) -> None:
        source = (
            '"""A robust report."""\n'
            'SECRET = "marks a pivotal moment"\n'
            '# marks a pivotal moment\n'
        )
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
            content=json.dumps({"findings": [{
                "code": "NAS106", "evidence": "marks a pivotal moment", "reason": "Unsupported code quote.",
            }]})
        ))])
        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "pyproject.toml"
            config_path.write_text("[tool.style-audit]\n", encoding="utf-8")
            with patch("style_audit.llm.litellm.completion", return_value=response):
                with patch("sys.stdin", StringIO(source)):
                    with patch("sys.stdout", new_callable=StringIO) as stdout:
                        with patch("sys.stderr", new_callable=StringIO) as stderr:
                            code = main([
                                "-", "--stdin-filename", "private.py", "--config", str(config_path),
                                "--select", "NAS001,NAS106", "--model", "openai/test-model", "--format", "json",
                            ])
            self.assertEqual(code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("not present in visible prose", stderr.getvalue())

    def test_per_file_globs_union_replace_defaults_and_respect_ignores_from_nested_cwd(self) -> None:
        text = "# 🌿 Header\nA robust parser has the ability to read counts.\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nested = root / "docs" / "nested"
            nested.mkdir(parents=True)
            (root / "src").mkdir()
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["NAS002"]\nignore = ["NAS003"]\noutput = "json"\n'
                '[tool.style-audit.per-file-select]\n"docs/**" = ["NAS00[13]"]\n'
                '"docs/*/draft[12].md" = ["NAS002"]\n"src/*.py" = []\n', encoding="utf-8",
            )
            for relative in ("docs/draft.md", "docs/nested/draft1.md", "docs/nested/draft3.md", "fallback.txt"):
                (root / relative).write_text(text, encoding="utf-8")
            (root / "src" / "api.py").write_text('"""' + text + '"""\n', encoding="utf-8")
            for cwd in (root, nested):
                with self.subTest(cwd=cwd):
                    code, output = run(_parse_options([str(root)]), cwd=cwd)
                    self.assertEqual(code, 1)
                    self.assertEqual(sorted(
                        ((cwd / item["path"]).relative_to(root).as_posix(), item["code"])
                        for item in json.loads(output)["findings"]
                    ), [
                        ("docs/draft.md", "NAS001"),
                        ("docs/nested/draft1.md", "NAS001"),
                        ("docs/nested/draft1.md", "NAS002"),
                        ("docs/nested/draft3.md", "NAS001"),
                        ("fallback.txt", "NAS002"),
                    ])

    def test_per_file_named_stdin_and_cli_glob_overrides_use_config_root(self) -> None:
        text = "# 🌿 Header\nA robust parser has the ability to read counts.\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "pyproject.toml"
            config.write_text(
                '[tool.style-audit]\nselect = ["NAS001"]\nignore = ["NAS003"]\noutput = "json"\n'
                '[tool.style-audit.per-file-select]\n"docs/*.md" = ["NAS002"]\n"*.py" = ["NAS003"]\n',
                encoding="utf-8",
            )
            for filename, source, expected in (
                ("docs/draft.md", text, ["NAS002"]),
                ("api.py", '"""' + text + '"""\n', []),
                ("<stdin>", text, ["NAS001"]),
            ):
                for override in (False, True):
                    with self.subTest(filename=filename, override=override):
                        options = ["-", "--stdin-filename", filename]
                        if override:
                            options.extend(["--select", "NAS00?", "--ignore", "NAS00[23]"])
                        code, output = run(_parse_options(options), source, root)
                        expected_codes = ["NAS001"] if override else expected
                        self.assertEqual(code, 1 if expected_codes else 0)
                        self.assertEqual([item["code"] for item in json.loads(output)["findings"]], expected_codes)
            other_cwd = root / "other"
            other_cwd.mkdir()
            code, output = run(_parse_options([
                "-", "--stdin-filename", str(root / "docs" / "virtual.md"), "--config", str(config),
            ]), text, other_cwd)
            self.assertEqual(code, 1)
            self.assertEqual([item["code"] for item in json.loads(output)["findings"]], ["NAS002"])

    def test_per_file_llm_selection_only_sends_matching_files_and_needs_no_unused_model(self) -> None:
        def provider(*, state, questions, **kwargs):
            self.assertNotIn("PRIVATE", state["text"])
            return SimpleNamespace(answers={
                code: SimpleNamespace(type="noul", noul=0.95 if code == "RDL104" and "Memory freshness" in state["text"] else 0.05)
                for code in questions
            })

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "review").mkdir()
            (root / "src").mkdir()
            config = root / "pyproject.toml"
            settings = (
                '[tool.style-audit]\noutput = "json"\n'
                '[tool.style-audit.per-file-select]\n"review/*.md" = ["RDL10[46]"]\n'
            )
            config.write_text(settings + '[tool.style-audit.llm]\nmodel = "azure-maas-judge/Decision-1"\n', encoding="utf-8")
            (root / "review" / "draft.md").write_text("Memory freshness allocation envelope changed.\n", encoding="utf-8")
            local = root / "local.md"
            local.write_text("A robust PRIVATE local report.\n", encoding="utf-8")
            python = root / "src" / "api.py"
            python.write_text('"""A robust PRIVATE parser."""\n', encoding="utf-8")
            with patch("style_audit.llm.litellm.systemone", side_effect=provider):
                code, output = run(_parse_options([str(root)]), cwd=root)
            self.assertEqual(code, 1)
            self.assertEqual(sorted((item["path"], item["code"]) for item in json.loads(output)["findings"]), [
                ("local.md", "NAS001"), ("review/draft.md", "RDL104"), ("src/api.py", "NAS001"),
            ])
            config.write_text(settings, encoding="utf-8")
            with patch("style_audit.llm.litellm.systemone", side_effect=AssertionError("Private files reached a provider")):
                code, output = run(_parse_options([str(local), str(python)]), cwd=root)
                self.assertEqual(code, 1)
                self.assertEqual([(item["path"], item["code"]) for item in json.loads(output)["findings"]], [
                    ("local.md", "NAS001"), ("src/api.py", "NAS001"),
                ])
                code, output = run(_parse_options([str(root), "--select", "NAS001"]), cwd=root)
                self.assertEqual(code, 1)
                self.assertEqual([(item["path"], item["code"]) for item in json.loads(output)["findings"]], [
                    ("local.md", "NAS001"), ("src/api.py", "NAS001"),
                ])

    def test_invalid_per_file_settings_and_unmatched_rule_patterns_are_errors_even_with_cli_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "pyproject.toml"
            for settings in (
                '[tool.style-audit]\nper-file-select = []\n',
                '[tool.style-audit.per-file-select]\n"*.md" = "NAS00"\n',
                '[tool.style-audit.per-file-select]\n"*.md" = [true]\n',
                '[tool.style-audit.per-file-select]\n"*.md" = [""]\n',
                '[tool.style-audit.per-file-select]\n" " = ["NAS00"]\n',
                '[tool.style-audit.per-file-select]\n"unmatched/*.md" = ["NAS999"]\n',
                '[tool.style-audit.per-file-select]\n"unmatched/*.md" = ["nas*"]\n',
                '[tool.style-audit.per-file-select]\n"unmatched/*.md" = ["NAS00[9]"]\n',
            ):
                with self.subTest(settings=settings):
                    config.write_text(settings, encoding="utf-8")
                    with patch("sys.stdout", new_callable=StringIO) as stdout, patch("sys.stderr", new_callable=StringIO) as stderr:
                        code = main(["-", "--config", str(config), "--select", "NAS001", "--format", "json"])
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertRegex(stderr.getvalue(), "per-file-select|unknown rule selector")

    def test_matching_per_file_llm_rules_fail_before_partial_json_without_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["NAS001"]\noutput = "json"\n'
                '[tool.style-audit.per-file-select]\n"z-review.md" = ["NAS106"]\n', encoding="utf-8",
            )
            (root / "a-local.md").write_text("A robust local report.\n", encoding="utf-8")
            (root / "z-review.md").write_text("The release marks a pivotal moment.\n", encoding="utf-8")
            with patch("style_audit.llm.litellm.systemone", side_effect=AssertionError("Missing model started a provider")):
                with patch("sys.stdout", new_callable=StringIO) as stdout, patch("sys.stderr", new_callable=StringIO) as stderr:
                    code = main([str(root), "--config", str(root / "pyproject.toml")])
            self.assertEqual(code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("requires an explicit model", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
