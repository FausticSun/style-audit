"""Integration-level tests for project configuration and command behavior."""

import json
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError
from style_audit.cli import CLIOptions, build_cli, main, run
from style_audit.config import AuditConfig, LiteLLMConfig, load_config
from style_audit.models import AuditError


def _parse_options(arguments: list[str]) -> CLIOptions:
    command = build_cli()
    with command.make_context("style-audit", list(arguments)) as context:
        return CLIOptions(**context.params)


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()

_PROJECT_RULESET = """schema_version: 1
rules:
  - code: TEAM001
    name: Weak intensifier
    engine: deterministic
    scope: sentence
    source: https://example.invalid/team-style#intensifiers
    description: Flag the weak intensifier very.
    detector:
      kind: regex
      pattern: '(?<!\\w)very(?!\\w)'
      target: unit
      message: Replace {evidence!r} with a specific description.
      fix: State the measurable property directly.
    examples:
      - before: The service is very fast.
        after: The service is fast.
        explanation: Replace the vague intensifier with a direct claim.
  - code: TEAM002
    name: Unsupported success claim
    engine: llm
    scope: sentence
    source: https://example.invalid/team-style#claims
    prompt: >-
      Flag unsupported claims of success without an observable result. Preserve supported outcomes.
    examples:
      - before: The launch was a complete success.
        after: The launch shipped on 12 May.
        explanation: Replace the unsupported evaluation with an observable outcome.
"""


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

    def test_project_rule_catalogs_load_relative_paths_and_reject_unsafe_or_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "rules" / "team.yaml"
            catalog.parent.mkdir()
            catalog.write_text(_PROJECT_RULESET, encoding="utf-8")
            config_path = root / "pyproject.toml"
            config_path.write_text(
                '[tool.style-audit]\nrule-catalogs = ["rules/team.yaml"]\n',
                encoding="utf-8",
            )

            config = load_config(root)
            self.assertEqual([rule.code for rule in config.project_rules], ["TEAM001", "TEAM002"])

            for filename in ("../outside.yaml", str(catalog.resolve())):
                with self.subTest(filename=filename):
                    config_path.write_text(
                        f'[tool.style-audit]\nrule-catalogs = ["{filename}"]\n',
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(AuditError, "project-relative"):
                        load_config(root)

            config_path.write_text(
                '[tool.style-audit]\nrule-catalogs = ["rules/team.yaml"]\n',
                encoding="utf-8",
            )
            catalog.write_text(_PROJECT_RULESET.replace("TEAM001", "NAS001"), encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "defined more than once"):
                load_config(root)

            catalog.write_text(_PROJECT_RULESET, encoding="utf-8")
            second_catalog = root / "rules" / "another.yaml"
            second_catalog.write_text(_PROJECT_RULESET, encoding="utf-8")
            config_path.write_text(
                '[tool.style-audit]\nrule-catalogs = ["rules/team.yaml", "rules/another.yaml"]\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AuditError, "defined more than once"):
                load_config(root)

            config_path.write_text(
                '[tool.style-audit]\nrule-catalogs = ["rules/missing.yaml"]\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AuditError, "cannot read project YAML rule catalog"):
                load_config(root)

    def test_project_rule_catalogs_reject_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "project"
            (root / "rules").mkdir(parents=True)
            outside = base / "outside.yaml"
            outside.write_text(_PROJECT_RULESET, encoding="utf-8")
            link = root / "rules" / "outside.yaml"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nrule-catalogs = ["rules/outside.yaml"]\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(AuditError, "must resolve inside"):
                load_config(root)

    def test_invalid_toml_or_llm_configuration_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            config = project / "pyproject.toml"
            config.write_text("[tool.style-audit\n", encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "cannot load configuration"):
                load_config(project)
            config.write_text(
                '[tool.style-audit.llm]\nenabled = true\nmodel = ""\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AuditError, "model must be a non-empty string"):
                load_config(project)
            config.write_text('[tool.style-audit]\ninclude = "*.md"\n', encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "include must be an array"):
                load_config(project)

    def test_default_model_is_present_and_llm_default_is_unspecified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            config = load_config(project)
            self.assertEqual(config.llm_model, "openrouter/openrouter/free")
            self.assertIsNone(config.llm_enabled)
            self.assertEqual(config.llm_api, "completion")

            (project / "pyproject.toml").write_text(
                "[tool.style-audit.llm]\nenabled = true\n",
                encoding="utf-8",
            )
            configured = load_config(project)
            self.assertEqual(configured.llm_model, "openrouter/openrouter/free")
            self.assertTrue(configured.llm_enabled)

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


    def test_pydantic_configuration_models_are_strict_and_immutable(self) -> None:
        with self.assertRaises(ValidationError):
            LiteLLMConfig(timeout=True)
        config = AuditConfig(root=Path.cwd())
        with self.assertRaises(ValidationError):
            config.output = "json"
        self.assertEqual(config.output, "text")

    def test_unknown_litellm_transport_setting_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                "[tool.style-audit.llm.litellm]\nunknown_transport_setting = true\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AuditError, "unsupported setting"):
                load_config(root)

    def test_generic_litellm_provider_settings_are_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit.llm]\nmodel = "openai/test-model"\n'
                '[tool.style-audit.llm.litellm]\n'
                'api_base = "https://provider.example/v1"\n'
                'api_key_env = "STYLE_AUDIT_TEST_API_KEY"\n'
                'custom_llm_provider = "openai"\n'
                'timeout = 12.0\n'
                'temperature = 0.0\n',
                encoding="utf-8",
            )
            config = load_config(root).llm_litellm

        self.assertEqual(config.api_base, "https://provider.example/v1")
        self.assertEqual(config.api_key_env, "STYLE_AUDIT_TEST_API_KEY")
        self.assertEqual(config.custom_llm_provider, "openai")
        self.assertEqual(config.timeout, 12.0)
        self.assertEqual(config.temperature, 0.0)


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
            for directory in (root, docs):
                for filename in ("AGENTS.md", "SKILL.md"):
                    (directory / filename).write_text("A robust instruction example.\n", encoding="utf-8")
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

    def test_project_rulesets_run_custom_deterministic_and_llm_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rules = root / "rules"
            rules.mkdir()
            (rules / "team.yaml").write_text(_PROJECT_RULESET, encoding="utf-8")
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\n'
                'rule-catalogs = ["rules/team.yaml"]\n'
                'select = ["TEAM"]\n'
                'output = "json"\n'
                '[tool.style-audit.llm]\n'
                'model = "openai/test-model"\n',
                encoding="utf-8",
            )
            nested = root / "docs"
            nested.mkdir()
            (nested / "draft.md").write_text("The launch was very successful.\n", encoding="utf-8")
            response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content=json.dumps({
                    "findings": [{
                        "code": "TEAM002",
                        "evidence": "The launch was very successful.",
                        "reason": "The sentence makes an unsupported success claim without an observed result.",
                    }],
                }),
            ))])

            with patch("style_audit.llm.litellm.completion", return_value=response) as provider:
                code, output = run(_parse_options([str(nested / "draft.md")]), cwd=nested)

        findings = {finding["code"]: finding for finding in json.loads(output)["findings"]}
        self.assertEqual(code, 1)
        self.assertEqual(set(findings), {"TEAM001", "TEAM002"})
        self.assertEqual(
            (findings["TEAM001"]["evidence"], findings["TEAM001"]["line"], findings["TEAM001"]["column"]),
            ("very", 1, 16),
        )
        self.assertEqual(
            (findings["TEAM002"]["evidence"], findings["TEAM002"]["line"], findings["TEAM002"]["column"]),
            ("The launch was very successful.", 1, 1),
        )
        provider.assert_called_once()
        prompt = "\n".join(message["content"] for message in provider.call_args.kwargs["messages"])
        self.assertIn("Flag unsupported claims of success", prompt)
        self.assertNotIn("NAS001", prompt)


    def test_project_rule_overrides_merge_regex_terms_and_llm_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rules = root / "rules"
            rules.mkdir()
            (rules / "team.yaml").write_text(_PROJECT_RULESET, encoding="utf-8")
            (rules / "overrides.yaml").write_text(
                "schema_version: 1\n"
                "overrides:\n"
                "  - code: TEAM001\n"
                "    name: Project speed wording\n"
                "    description: Review direct speed terms.\n"
                "    detector:\n"
                "      pattern: '(?<!\\w)fast(?!\\w)'\n"
                "      flags: [ignorecase]\n"
                "      message: Review {evidence!r}.\n"
                "      fix: State the measured performance.\n"
                "    additional-terms: [rapid]\n"
                "    examples:\n"
                "      - before: The service is fast.\n"
                "        after: The service transfers 4 MB/s.\n"
                "        explanation: Replace evaluation with a measured result.\n"
                "  - code: TEAM002\n"
                "    name: Evidence-based launch claims\n"
                "    prompt: Flag unsupported launch claims; preserve observable outcomes.\n"
                "    examples:\n"
                "      - before: The launch was a complete success.\n"
                "        after: The launch shipped on 12 May.\n"
                "        explanation: Replace the unsupported evaluation with an outcome.\n",
                encoding="utf-8",
            )
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\n'
                'rule-catalogs = ["rules/team.yaml"]\n'
                'rule-overrides = ["rules/overrides.yaml"]\n'
                'select = ["TEAM"]\n'
                'output = "json"\n'
                '[tool.style-audit.llm]\n'
                'model = "openai/test-model"\n',
                encoding="utf-8",
            )
            document = root / "draft.md"
            document.write_text(
                "The service is FAST and rapid; the launch was a complete success.\n",
                encoding="utf-8",
            )

            config = load_config(root)
            overridden = {rule.code: rule for rule in config.overridden_rules}
            self.assertEqual(overridden["TEAM001"].name, "Project speed wording")
            self.assertEqual(overridden["TEAM001"].detector.pattern, r"(?<!\w)fast(?!\w)")
            self.assertEqual(overridden["TEAM001"].additional_terms, ("rapid",))
            self.assertEqual(
                overridden["TEAM002"].description,
                "Flag unsupported launch claims; preserve observable outcomes.",
            )
            self.assertEqual(
                overridden["TEAM002"].examples[0].after,
                "The launch shipped on 12 May.",
            )

            response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content=json.dumps({
                    "findings": [{
                        "code": "TEAM002",
                        "evidence": "the launch was a complete success",
                        "reason": "The launch claim gives no observable result.",
                    }],
                }),
            ))])
            with patch("style_audit.llm.litellm.completion", return_value=response) as provider:
                code, output = run(_parse_options([str(document)]), cwd=root)

        findings = json.loads(output)["findings"]
        self.assertEqual(code, 1)
        self.assertEqual(
            [(item["code"], item["evidence"]) for item in findings],
            [
                ("TEAM001", "FAST"),
                ("TEAM001", "rapid"),
                ("TEAM002", "the launch was a complete success"),
            ],
        )
        self.assertEqual(findings[0]["fix"], "State the measured performance.")
        provider.assert_called_once()
        prompt = "\n".join(message["content"] for message in provider.call_args.kwargs["messages"])
        self.assertIn("Evidence-based launch claims", prompt)
        self.assertIn("Flag unsupported launch claims", prompt)
        self.assertIn("The launch shipped on 12 May.", prompt)

    def test_invalid_project_rule_overrides_fail_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            overrides = root / "overrides.yaml"
            config_path = root / "pyproject.toml"
            config_path.write_text(
                '[tool.style-audit]\nrule-overrides = ["overrides.yaml"]\n',
                encoding="utf-8",
            )
            invalid_catalogs = (
                ("schema_version: 1\noverrides: [{code: UNKNOWN001, name: Unknown}]\n", "unknown rule"),
                ("schema_version: 1\noverrides: [{code: NAS001, unsupported: true}]\n", "invalid rule overrides"),
                (
                    "schema_version: 1\noverrides: [{code: NAS001, detector: {pattern: '['}}]\n",
                    "invalid detector override",
                ),
                ("schema_version: 1\noverrides: [{code: NAS001, prompt: Not deterministic}]\n", "prompt can only"),
                (
                    "schema_version: 1\noverrides: [{code: NAS101, additional-terms: [word]}]\n",
                    "additional-terms can only",
                ),
                (
                    "schema_version: 1\noverrides: [{code: NAS001, name: Duplicate}, {code: NAS001, source: https://example.invalid}]\n",
                    "only once per file",
                ),
            )
            for content, expected_error in invalid_catalogs:
                with self.subTest(expected_error=expected_error):
                    overrides.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(AuditError, expected_error):
                        load_config(root)

            overrides.write_text(
                "schema_version: 1\noverrides: [{code: NAS001, name: First}]\n",
                encoding="utf-8",
            )
            (root / "second.yaml").write_text(
                "schema_version: 1\noverrides: [{code: NAS001, name: Second}]\n",
                encoding="utf-8",
            )
            config_path.write_text(
                '[tool.style-audit]\nrule-overrides = ["overrides.yaml", "second.yaml"]\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AuditError, "more than one project file"):
                load_config(root)


    def test_default_markdown_selects_nas_and_readability_with_explicit_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("[tool.style-audit]\n", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (root / "README.md").write_text("A robust parser works.", encoding="utf-8")
            (docs / "guide.md").write_text("A resilient parser works.", encoding="utf-8")
            for directory in (root, docs):
                (directory / "AGENTS.md").write_text("AGENTS_PRIVATE_481.", encoding="utf-8")
                (directory / "SKILL.md").write_text("SKILL_PRIVATE_592.", encoding="utf-8")

            requested_text: list[str] = []
            requested_prompts: list[str] = []
            requested_models: set[str] = set()

            def judge(*, messages, model, **kwargs):
                user_message = next(message for message in messages if message["role"] == "user")
                requested_text.append(json.loads(user_message["content"])["text"])
                requested_prompts.extend(
                    message["content"] for message in messages if message["role"] == "system"
                )
                requested_models.add(model)
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                    content='{"findings":[]}'
                ))])

            with patch("style_audit.llm.litellm.completion", side_effect=judge) as provider:
                code, output = run(_parse_options([
                    str(root), "--format", "json", "--model", "openai/test-model",
                ]), cwd=root)

        findings = json.loads(output)["findings"]
        self.assertEqual(code, 1)
        self.assertEqual(
            [(item["path"], item["code"]) for item in findings],
            [("README.md", "NAS001")],
        )
        self.assertEqual(requested_models, {"openai/test-model"})
        self.assertTrue(any("A robust parser works." in text for text in requested_text))
        self.assertTrue(any("A resilient parser works." in text for text in requested_text))
        self.assertFalse(any(
            "PRIVATE_481" in text or "PRIVATE_592" in text
            for text in requested_text + requested_prompts
        ))
        self.assertTrue(any("NAS" in text for text in requested_prompts))
        self.assertTrue(any("RDL" in text for text in requested_prompts))
        self.assertFalse(any("STE" in text for text in requested_prompts))

    def test_default_rulesets_run_nas_and_readability_judgments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("[tool.style-audit]\n", encoding="utf-8")
            (root / "README.md").write_text("A robust parser works.", encoding="utf-8")
            (root / "draft.txt").write_text("A short sentence uses clear words.", encoding="utf-8")
            response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content='{"findings":[]}',
            ))])
            with patch("style_audit.llm.litellm.completion", return_value=response) as chat_provider:
                code, output = run(_parse_options([str(root), "--format", "json"]), cwd=root)

        self.assertEqual(code, 1)
        self.assertEqual(
            [(item["path"], item["code"]) for item in json.loads(output)["findings"]],
            [("README.md", "NAS001")],
        )
        self.assertGreater(chat_provider.call_count, 0)
        prompts = json.dumps([call.kwargs["messages"] for call in chat_provider.call_args_list])
        self.assertIn("NAS", prompts)
        self.assertIn("RDL", prompts)
        self.assertNotIn("STE", prompts)
        self.assertNotIn("MWG", prompts)
        self.assertIn("A short sentence uses clear words.", prompts)

    def test_llm_enabled_false_keeps_default_rules_local(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                "[tool.style-audit.llm]\nenabled = false\n", encoding="utf-8",
            )
            (root / "README.md").write_text("A robust parser works.", encoding="utf-8")
            with patch("style_audit.llm.litellm.completion") as chat_provider:
                code, output = run(_parse_options([str(root), "--format", "json"]), cwd=root)

        self.assertEqual(code, 1)
        self.assertEqual(
            [(item["path"], item["code"]) for item in json.loads(output)["findings"]],
            [("README.md", "NAS001")],
        )
        chat_provider.assert_not_called()

    def test_chat_model_runs_through_cli(self) -> None:
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
            content=json.dumps({
                "findings": [{
                    "code": "NAS106",
                    "evidence": "marks a pivotal moment",
                    "reason": "This announces importance without a concrete fact.",
                }],
            }),
        ))])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = _parse_options([
                "-", "--stdin-filename", "draft.md", "--select", "NAS106",
                "--model", "openai/test-model", "--format", "json",
            ])
            with patch("style_audit.llm.litellm.completion", return_value=response) as chat:
                code, output = run(
                    args, "The launch marks a pivotal moment for the team.", root,
                )

        self.assertEqual(code, 1)
        findings = json.loads(output)["findings"]
        self.assertEqual([(item["code"], item["evidence"]) for item in findings], [
            ("NAS106", "marks a pivotal moment"),
        ])
        chat.assert_called_once()
        self.assertEqual(chat.call_args.kwargs["model"], "openai/test-model")

    def test_mwg_catalog_selection_runs_and_reports_llm_finding(self) -> None:
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
            content=json.dumps({
                "findings": [{
                    "code": "MWG001",
                    "evidence": "The team recommends the hosted option.",
                    "reason": "The paragraph states its recommendation directly.",
                }],
            }),
        ))])
        text = "We compared operating costs and migration work. The team recommends the hosted option."
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = _parse_options([
                "-", "--stdin-filename", "draft.md", "--select", "MWG001",
                "--model", "openai/test-model", "--format", "json",
            ])
            with patch("style_audit.llm.litellm.completion", return_value=response) as chat:
                code, output = run(args, text, root)

        self.assertEqual(code, 1)
        findings = json.loads(output)["findings"]
        self.assertEqual(
            [(item["code"], item["evidence"]) for item in findings],
            [("MWG001", "The team recommends the hosted option.")],
        )
        chat.assert_called_once()

    def test_decisions_threshold_override_reports_all_confidences(self) -> None:
        text = "First sentence. Second sentence."
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["NAS106"]\n'
                '[tool.style-audit.llm]\nmodel = "openai/test-model"\n'
                'api = "decisions"\nthreshold = 0.9\n',
                encoding="utf-8",
            )

            for output_format in ("json", "text"):
                probabilities = iter((0.7, 0.4))
                calls = []

                def decide(**kwargs):
                    calls.append(kwargs)
                    return SimpleNamespace(answers=[SimpleNamespace(
                        type="predicate",
                        name="NAS106",
                        probability=next(probabilities),
                    )])

                args = _parse_options([
                    "-", "--stdin-filename", "draft.md", "--threshold", "0.5",
                    "--show-confidences", "--format", output_format,
                ])
                with patch("style_audit.llm.litellm.decisions", side_effect=decide):
                    with patch("style_audit.llm.litellm.completion") as completion:
                        code, output = run(args, text, root)

                self.assertEqual(code, 1)
                self.assertEqual(len(calls), 2)
                completion.assert_not_called()
                if output_format == "json":
                    report = json.loads(output)
                    self.assertEqual(len(report["findings"]), 1)
                    self.assertIn("decision probability 0.70 meets threshold 0.50", report["findings"][0]["message"])
                    self.assertEqual(report["confidence_threshold"], 0.5)
                    self.assertEqual(
                        [(item["evidence"], item["probability"], item["meets_threshold"])
                         for item in report["confidences"]],
                        [("First sentence.", 0.7, True), ("Second sentence.", 0.4, False)],
                    )
                else:
                    self.assertIn("Model confidence scores (threshold 0.50):", output)
                    self.assertIn("NAS106: 0.70 (meets threshold)", output)
                    self.assertIn("NAS106: 0.40 (below threshold)", output)

            low_probabilities = iter((0.4, 0.3))

            def low_confidence(**kwargs):
                return SimpleNamespace(answers=[SimpleNamespace(
                    type="predicate",
                    name="NAS106",
                    probability=next(low_probabilities),
                )])

            args = _parse_options([
                "-", "--stdin-filename", "draft.md", "--threshold", "0.5",
                "--show-confidences", "--format", "json",
            ])
            with patch("style_audit.llm.litellm.decisions", side_effect=low_confidence):
                code, output = run(args, text, root)
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])
            self.assertEqual(
                [(item["probability"], item["meets_threshold"]) for item in report["confidences"]],
                [(0.4, False), (0.3, False)],
            )

    def test_confidence_options_require_decisions_and_reject_invalid_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for option in ("--show-confidences", "--threshold"):
                arguments = [
                    "-", "--select", "NAS106", "--model", "openai/test-model", option,
                ]
                if option == "--threshold":
                    arguments.append("0.5")
                args = _parse_options(arguments)
                with self.subTest(option=option):
                    expected_error = "requires" if option == "--show-confidences" else "Decisions API"
                    with self.assertRaisesRegex(AuditError, expected_error):
                        run(args, "First sentence.", root)

        with patch("sys.stderr", new_callable=StringIO) as stderr:
            code = main(["--threshold", "nan"])
        self.assertEqual(code, 2)
        self.assertIn("finite number from 0 to 1", stderr.getvalue())

    def test_confidence_reporting_does_not_override_disabled_llm(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit.llm]\nenabled = false\nmodel = "openai/test-model"\napi = "decisions"\n',
                encoding="utf-8",
            )
            args = _parse_options([
                "-", "--stdin-filename", "draft.md", "--show-confidences",
            ])
            with patch("style_audit.llm.litellm.decisions") as provider:
                with self.assertRaisesRegex(
                    AuditError, "require selected LLM rules with judging enabled",
                ):
                    run(args, "First sentence.", root)
            provider.assert_not_called()

    def test_commit_messages_audit_reachable_history_and_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _git(root, "init", "--quiet")
            _git(root, "config", "user.name", "Style audit tests")
            _git(root, "config", "user.email", "style-audit@example.invalid")
            _git(root, "config", "commit.gpgsign", "false")
            _git(root, "commit", "--quiet", "--allow-empty", "-m", "# 🌿 Past heading")
            first_commit = _git(root, "rev-parse", "HEAD")
            _git(root, "commit", "--quiet", "--allow-empty", "-m", "Clear follow-up")

            args = _parse_options(["--commit-messages", "HEAD", "--format", "json"])
            response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content='{"findings":[]}',
            ))])
            with patch("style_audit.llm.litellm.decisions") as decisions:
                with patch("style_audit.llm.litellm.completion", return_value=response) as completion:
                    code, output = run(args, cwd=root)

            self.assertEqual(code, 1)
            findings = json.loads(output)["findings"]
            self.assertIn(
                (f"commit/{first_commit}.txt", "NAS002", 1),
                [(item["path"], item["code"], item["line"]) for item in findings],
            )
            decisions.assert_not_called()
            requests = json.dumps([call.kwargs["messages"] for call in completion.call_args_list])
            self.assertGreater(completion.call_count, 0)
            self.assertIn("NAS", requests)
            self.assertIn("RDL", requests)
            self.assertNotIn("STE", requests)
            self.assertNotIn("MWG", requests)

            args = _parse_options([
                "--commit-messages", "HEAD~1..HEAD", "--select", "NAS002", "--format", "json",
            ])
            code, output = run(args, cwd=root)
            self.assertEqual((code, json.loads(output)["findings"]), (0, []))

            args = _parse_options(["--commit-messages", "not-a-revision"])
            with self.assertRaisesRegex(AuditError, "cannot read Git commit messages"):
                run(args, cwd=root)

    def test_commit_message_mode_rejects_paths_and_requires_a_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = _parse_options(["--commit-messages", "HEAD", "draft.md"])
            with self.assertRaisesRegex(AuditError, "cannot be combined with input paths"):
                run(args, cwd=root)

            args = _parse_options(["--commit-messages", "HEAD"])
            with self.assertRaisesRegex(AuditError, "cannot read Git commit messages"):
                run(args, cwd=root)

    def test_clean_stdin_and_explicit_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = _parse_options(["-", "--stdin-filename", "draft.txt", "--select", "NAS00"])
            code, stdout = run(args, "Ordinary clear prose.", root)
            self.assertEqual((code, stdout), (0, ""))

            args = _parse_options(["-", "--select", "NAS002"])
            code, stdout = run(args, "# 🌿 Heading", root)
            self.assertEqual(code, 1)
            self.assertIn("NAS002", stdout)

    def test_input_errors_and_selected_llm_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = _parse_options(["missing.md"])
            with self.assertRaisesRegex(AuditError, "does not exist"):
                run(args, cwd=root)

            args = _parse_options(["-", "--select", "NAS101"])
            response = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"findings":[]}'))],
            )
            with patch("style_audit.llm.litellm.completion", return_value=response) as provider:
                code, output = run(args, "Some prose.", root)
            self.assertEqual((code, output), (0, ""))
            provider.assert_called_once()
            self.assertEqual(provider.call_args.kwargs["model"], "openrouter/openrouter/free")

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

        def provider(*, messages, **kwargs):
            user_message = next(message for message in messages if message["role"] == "user")
            text = json.loads(user_message["content"])["text"]
            findings = []
            if "proposal expects" in text:
                findings.append({
                    "code": "RDL106",
                    "evidence": "The proposal expects the reader to calendar the premise.",
                    "reason": "The premise is difficult to follow.",
                })
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content=json.dumps({"findings": findings})
            ))])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["RDL"]\nignore = ["RDL104"]\noutput = "json"\n'
                '[tool.style-audit.llm]\nmodel = "openai/test-model"\n',
                encoding="utf-8",
            )
            with patch("style_audit.llm.litellm.completion", side_effect=provider):
                code, output = run(_parse_options(["-"]), source, root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["code"], item["line"], item["column"], item["evidence"])
                 for item in json.loads(output)["findings"]],
                [("RDL106", 2, 1, "The proposal expects the reader to calendar the premise.")],
            )

            with patch("style_audit.llm.litellm.completion") as provider_call:
                code, output = run(_parse_options(["-", "--select", "NAS001"]), source, root)
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["code"], item["line"], item["column"]) for item in json.loads(output)["findings"]],
                [("NAS001", 3, 3)],
            )
            provider_call.assert_not_called()

            with patch("style_audit.llm.litellm.completion") as provider_call:
                code, output = run(_parse_options(["-", "--ignore", "RDL"]), source, root)
            self.assertEqual((code, json.loads(output)["findings"]), (0, []))
            provider_call.assert_not_called()


    def test_deterministic_only_selection_never_calls_a_provider_even_with_llm_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "pyproject.toml"
            for configured in (False, True):
                config_path.write_text(
                    '[tool.style-audit]\nselect = ["NAS106"]\n'
                    '[tool.style-audit.llm]\nenabled = true\n'
                    'model = "openai/test-model"\n'
                    if configured else "[tool.style-audit]\n",
                    encoding="utf-8",
                )
                for flags in (
                    ["--llm"],
                    ["--model", "openai/test-model"],
                    ["--llm", "--model", "openai/test-model"],
                ):
                    with self.subTest(configured=configured, flags=flags):
                        args = _parse_options([
                            "-", "--select", "NAS001", "--format", "json", *flags,
                        ])
                        with patch("style_audit.llm.litellm.completion") as chat_provider:
                            code, stdout = run(args, "The robust parser.", root)
                        self.assertEqual(code, 1)
                        self.assertEqual(
                            {finding["code"] for finding in json.loads(stdout)["findings"]}, {"NAS001"}
                        )
                        chat_provider.assert_not_called()

    def test_provider_or_response_failure_emits_error_without_partial_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "pyproject.toml"
            config_path.write_text("[tool.style-audit]\n", encoding="utf-8")
            first = root / "first.md"
            second = root / "second.md"
            first.write_text("A robust first paragraph.", encoding="utf-8")
            second.write_text("Second visible paragraph.", encoding="utf-8")
            empty_response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content='{"findings":[]}'
            ))])
            malformed_response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content="not json"
            ))])
            for failure in (RuntimeError("chat provider offline"), malformed_response):
                with self.subTest(failure=failure):
                    with patch("style_audit.llm.litellm.completion", side_effect=[
                        empty_response, failure,
                    ]):
                        with patch("sys.stdout", new_callable=StringIO) as stdout:
                            with patch("sys.stderr", new_callable=StringIO) as stderr:
                                code = main([
                                    str(first), str(second), "--config", str(config_path),
                                    "--select", "NAS001,NAS106", "--model", "openai/test-model",
                                    "--format", "json",
                                ])
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn("style-audit: error:", stderr.getvalue())
                    if isinstance(failure, RuntimeError):
                        self.assertIn("LiteLLM provider call failed", stderr.getvalue())

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
            with patch("style_audit.llm.litellm.completion") as provider:
                code, output = run(
                    _parse_options([str(feature), "--select", "NAS001", "--format", "json"]),
                    cwd=root,
                )
            self.assertEqual(code, 1)
            self.assertEqual(
                [(item["path"], item["code"], item["evidence"], item["line"], item["column"])
                 for item in json.loads(output)["findings"]],
                [("draft.feature", "NAS001", "robust", 1, 10),
                 ("draft.feature", "NAS001", "robust", 7, 14)],
            )
            provider.assert_not_called()

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
                    with patch("style_audit.llm.litellm.completion") as chat_provider:
                        code, output = run(_parse_options([
                            "-", "--stdin-filename", filename, "--select", "NAS001,NAS106",
                            "--model", "openai/test-model", "--format", "json",
                        ] if expected_code == 0 else [
                            "-", "--stdin-filename", filename, "--select", "NAS001", "--format", "json",
                        ]), source, root)
                    self.assertEqual(code, expected_code)
                    findings = json.loads(output)["findings"]
                    self.assertEqual(
                        [(finding["evidence"], finding["line"], finding["column"]) for finding in findings],
                        [] if expected_code == 0 else [("robust", 1, 5)],
                    )
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
                    inputs = ([str(first), str(invalid_path)] if mode == "file" else
                              ["-", "--stdin-filename", invalid_path.name, str(first)])
                    with self.subTest(suffix=suffix, mode=mode):
                        with patch("style_audit.llm.litellm.completion") as chat_provider:
                            with patch("sys.stdin", StringIO(invalid)):
                                with patch("sys.stdout", new_callable=StringIO) as stdout:
                                    with patch("sys.stderr", new_callable=StringIO) as stderr:
                                        code = main([
                                            *inputs, "--config", str(config_path),
                                            "--select", "NAS001,NAS106", "--model", "openai/test-model",
                                            "--format", "json",
                                        ])
                        self.assertEqual(code, 2)
                        self.assertEqual(stdout.getvalue(), "")
                        self.assertIn("style-audit: error:", stderr.getvalue())
                        self.assertIn(invalid_path.name, stderr.getvalue())
                        self.assertRegex(stderr.getvalue(), r"(?:line |:)2(?:[:, ]|$)")
                        chat_provider.assert_not_called()

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
            chat_provider.assert_not_called()

    def test_python_file_and_stdin_preserve_unicode_crlf_and_chat_evidence(self) -> None:
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

                    def provider(*, messages, **kwargs):
                        user_message = next(message for message in messages if message["role"] == "user")
                        context = json.loads(user_message["content"])
                        contexts.append(context)
                        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                            content=json.dumps({"findings": [{
                                "code": "NAS101", "evidence": expected_text,
                                "reason": "The statement needs support.",
                            }]})
                        ))])

                    inputs = [str(path)] if mode == "file" else ["-", "--stdin-filename", path.name]
                    with patch("style_audit.llm.litellm.completion", side_effect=provider):
                        code, output = run(_parse_options([
                            *inputs, "--select", "NAS101", "--model", "openai/test-model",
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
        def provider(*, messages, **kwargs):
            self.assertNotIn("PRIVATE", json.dumps(messages))
            user_message = next(message for message in messages if message["role"] == "user")
            text = json.loads(user_message["content"])["text"]
            findings = []
            if "Memory freshness" in text:
                findings.append({
                    "code": "RDL104",
                    "evidence": "Memory freshness allocation envelope changed.",
                    "reason": "The phrase is difficult to interpret.",
                })
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content=json.dumps({"findings": findings})
            ))])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "review").mkdir()
            (root / "src").mkdir()
            config = root / "pyproject.toml"
            settings = (
                '[tool.style-audit]\nselect = ["NAS001"]\noutput = "json"\n'
                '[tool.style-audit.per-file-select]\n"review/*.md" = ["RDL10[46]"]\n'
            )
            config.write_text(settings + '[tool.style-audit.llm]\nmodel = "openai/test-model"\n', encoding="utf-8")
            (root / "review" / "draft.md").write_text("Memory freshness allocation envelope changed.\n", encoding="utf-8")
            local = root / "local.md"
            local.write_text("A robust PRIVATE local report.\n", encoding="utf-8")
            python = root / "src" / "api.py"
            python.write_text('"""A robust PRIVATE parser."""\n', encoding="utf-8")
            with patch("style_audit.llm.litellm.completion", side_effect=provider):
                code, output = run(_parse_options([str(root)]), cwd=root)
            self.assertEqual(code, 1)
            self.assertEqual(sorted((item["path"], item["code"]) for item in json.loads(output)["findings"]), [
                ("local.md", "NAS001"), ("review/draft.md", "RDL104"), ("src/api.py", "NAS001"),
            ])
            config.write_text(settings, encoding="utf-8")
            with patch("style_audit.llm.litellm.completion", side_effect=AssertionError("Private files reached a provider")) as chat:
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
            chat.assert_not_called()

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

    def test_matching_per_file_llm_rules_use_default_model_and_keep_other_files_local(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text(
                '[tool.style-audit]\nselect = ["NAS001"]\noutput = "json"\n'
                '[tool.style-audit.per-file-select]\n"z-review.md" = ["NAS106"]\n', encoding="utf-8",
            )
            (root / "a-local.md").write_text("A robust local report.\n", encoding="utf-8")
            (root / "z-review.md").write_text("The release marks a pivotal moment.\n", encoding="utf-8")
            response = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"findings":[]}'))],
            )
            with patch("style_audit.llm.litellm.completion", return_value=response) as chat:
                with patch("sys.stdout", new_callable=StringIO) as stdout, patch("sys.stderr", new_callable=StringIO) as stderr:
                    code = main([str(root), "--config", str(root / "pyproject.toml")])
            self.assertEqual(code, 1)
            report = json.loads(stdout.getvalue())
            self.assertEqual([(item["path"], item["code"]) for item in report["findings"]], [(str(root / "a-local.md"), "NAS001")])
            self.assertEqual(stderr.getvalue(), "")
            chat.assert_called_once()
            self.assertEqual(chat.call_args.kwargs["model"], "openrouter/openrouter/free")
            request = json.dumps(chat.call_args.kwargs["messages"])
            self.assertIn("The release marks a pivotal moment.", request)
            self.assertNotIn("A robust local report.", request)


if __name__ == "__main__":
    unittest.main()
