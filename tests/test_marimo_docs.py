"""Behavioral coverage for source-backed Marimo Markdown auditing."""

import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from style_audit.cli import CLIOptions, build_cli, run
from style_audit.deterministic import analyze_deterministic
from style_audit.docstrings import extract_docstrings
from style_audit.marimo_docs import extract_markdown_cells
from style_audit.rules import RULES_BY_CODE


def _parse_options(arguments: list[str]) -> CLIOptions:
    command = build_cli()
    with command.make_context("style-audit", list(arguments)) as context:
        return CLIOptions(**context.params)


class MarimoMarkdownTests(unittest.TestCase):
    def setUp(self) -> None:
        for provider in (
            "style_audit.llm.litellm.completion",
        ):
            guard = patch(
                provider,
                side_effect=AssertionError("Marimo extraction tests must not call live providers"),
            )
            self.addCleanup(guard.stop)
            guard.start()

    def test_literal_markdown_cells_are_audited_without_executing_app_code(self) -> None:
        source = (
            "import marimo\n"
            "__generated_with = '0.25.2'\n"
            "app = marimo.App()\n"
            "@app.cell\n"
            "def _():\n"
            "    import marimo as mo\n"
            "    mo.md(\"\"\"\n"
            "        # Report\n"
            "        The service uses a robust parser.\n"
            "        ```python\n"
            "        robust executable example\n"
            "        ```\n"
            '        """)\n'
            "    return\n"
            "raise RuntimeError('The audited module must never execute')\n"
        )
        documents = extract_markdown_cells("report.py", source)
        self.assertIsNotNone(documents)
        self.assertEqual(len(documents), 1)
        document, = documents
        self.assertEqual(
            document.text,
            "# Report\nThe service uses a robust parser.\n```python\n"
            "robust executable example\n```",
        )
        findings = analyze_deterministic(document, (RULES_BY_CODE["NAS001"],))
        finding, = findings
        prose_match = source.index("robust", source.index("mo.md"))
        self.assertEqual((finding.code, finding.evidence), ("NAS001", "robust"))
        self.assertEqual(
            (finding.line, finding.column),
            (source.count("\n", 0, prose_match) + 1,
             prose_match - source.rfind("\n", 0, prose_match)),
        )

    def test_fstring_fragments_and_escaped_literals_map_to_original_source(self) -> None:
        source = (
            "import marimo as mo\n"
            "app = mo.App()\n"
            "@app.cell\n"
            "def _():\n"
            "    private_value = 'PRIVATE_CODE_VALUE'\n"
            '    mo.md("Café 🌿 wrote a \\u0072obust parser.")\n'
            '    mo.md(f"""The report uses a robust {private_value} and {{literal}} token.""")\n'
            "    return\n"
        )
        documents = extract_markdown_cells("unicode_report.py", source)
        self.assertIsNotNone(documents)
        self.assertEqual(len(documents), 2)
        literal, formatted = documents
        self.assertEqual(literal.text, "Café 🌿 wrote a robust parser.")
        self.assertNotIn("PRIVATE_CODE_VALUE", formatted.text)
        self.assertIn("{literal}", formatted.text)

        finding, = analyze_deterministic(literal, (RULES_BY_CODE["NAS001"],))
        spelling = r"\u0072obust"
        self.assertEqual(finding.evidence, spelling)
        offset = source.index(spelling)
        self.assertEqual(
            (finding.line, finding.column, finding.end_line, finding.end_column),
            (source.count("\n", 0, offset) + 1,
             offset - source.rfind("\n", 0, offset),
             source.count("\n", 0, offset + len(spelling)) + 1,
             offset + len(spelling) - source.rfind("\n", 0, offset + len(spelling))),
        )

    def test_non_app_python_keeps_docstring_extraction(self) -> None:
        source = '"""A robust module."""\nimport marimo\n'
        self.assertIsNone(extract_markdown_cells("ordinary.py", source))
        self.assertEqual(
            [document.text for document in extract_docstrings("ordinary.py", source)],
            ["A robust module."],
        )

    def test_cli_sends_only_literal_cell_prose_to_the_selected_chat_rules(self) -> None:
        source = (
            "import marimo as mo\n"
            "app = mo.App()\n"
            "# COMMENT_SECRET_4821\n"
            "assigned = 'ASSIGNED_SECRET_9137'\n"
            "@app.cell\n"
            "def _():\n"
            '    mo.md("The service starts before it receives traffic.")\n'
            "    return\n"
        )
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"findings":[]}'))]
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pyproject.toml").write_text("[tool.style-audit]\n", encoding="utf-8")
            path = root / "report.py"
            path.write_text(source, encoding="utf-8")
            args = _parse_options([
                str(path), "--select", "NAS106", "--model", "openai/test-model", "--format", "json",
            ])
            with patch("style_audit.llm.litellm.completion", return_value=response) as completion:
                code, output = run(args, cwd=root)

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["findings"], [])
        request = json.dumps(completion.call_args.kwargs["messages"], ensure_ascii=False)
        self.assertIn("The service starts before it receives traffic.", request)
        self.assertNotIn("COMMENT_SECRET_4821", request)
        self.assertNotIn("ASSIGNED_SECRET_9137", request)
        self.assertNotIn("app = mo.App()", request)
