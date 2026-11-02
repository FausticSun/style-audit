"""Configuration and local-HTTP smoke tests for LiteLLM Decisions judging."""

import json
import os
from pathlib import Path
import tempfile
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch

from style_audit.config import LiteLLMConfig, load_config
from style_audit.decision_api import load_decision_api
from style_audit.llm import judge_document
from style_audit.models import AuditError
from style_audit.rules import RULES_BY_CODE
from style_audit.text import TextDocument


class DecisionAPIConfigurationTests(unittest.TestCase):
    def test_resolves_registry_base_model_and_hides_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "models.yml"
            registry.write_text(
                "providers:\n"
                "  azure-maas-judge:\n"
                "    api: openrouter-decisions\n"
                "    baseUrl: https://judge.example/openai/v1/\n"
                "    apiKey: fixture-secret\n"
                "    models:\n"
                "      - id: Decision-1\n",
                encoding="utf-8",
            )
            settings = load_decision_api(registry_path=registry)

        self.assertEqual(settings.api_base, "https://judge.example/openai/v1")
        self.assertEqual(settings.model, "Decision-1")
        self.assertEqual(settings.custom_llm_provider, "openai")
        self.assertNotIn("fixture-secret", repr(settings))

    def test_environment_key_overrides_the_registry_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "models.yml"
            registry.write_text(
                "providers:\n"
                "  azure-maas-judge:\n"
                "    api: openrouter-decisions\n"
                "    baseUrl: https://judge.example/openai/v1\n"
                "    apiKey: registry-secret\n"
                "    models: [{id: Decision-1}]\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"AZURE_MAAS_JUDGE_API_KEY": "environment-secret"}):
                settings = load_decision_api(registry_path=registry)

        self.assertEqual(settings.api_key, "environment-secret")

    def test_complete_project_settings_bypass_the_registry(self) -> None:
        config = LiteLLMConfig(
            api_base="https://override.example/openai/v1",
            api_key_env="STYLE_AUDIT_TEST_API_KEY",
            custom_llm_provider="openai",
            decision_model="Decision-1",
            timeout=25,
        )
        with patch.dict(os.environ, {"STYLE_AUDIT_TEST_API_KEY": "environment-secret"}):
            settings = load_decision_api(config)

        self.assertEqual(settings.api_base, "https://override.example/openai/v1")
        self.assertEqual(settings.model, "Decision-1")
        self.assertEqual(settings.custom_llm_provider, "openai")
        self.assertEqual(settings.timeout, 25)
        self.assertEqual(settings.api_key, "environment-secret")
        self.assertNotIn("environment-secret", repr(settings))

    def test_invalid_registry_configuration_fails(self) -> None:

        invalid_registries = (
            "providers: {}\n",
            "providers:\n  azure-maas-judge:\n    api: openai\n",
            "providers:\n  azure-maas-judge:\n    api: openrouter-decisions\n"
            "    baseUrl: http://judge.example/v1\n    apiKey: secret\n"
            "    models: [{id: Decision-1}]\n",
        )
        for contents in invalid_registries:
            with self.subTest(contents=contents), tempfile.TemporaryDirectory() as temporary:
                registry = Path(temporary) / "models.yml"
                registry.write_text(contents, encoding="utf-8")
                with self.assertRaises(AuditError):
                    load_decision_api(registry_path=registry)

    def test_missing_registry_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing.yml"
            with self.assertRaisesRegex(AuditError, "cannot read"):
                load_decision_api(registry_path=missing)

    def test_pyproject_foundry_settings_use_registry_key_and_route(self) -> None:
        requests: list[tuple[str, dict[str, str]]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers["Content-Length"])
                self.rfile.read(length)
                requests.append((self.path, dict(self.headers)))
                response = json.dumps(
                    {
                        "model": "Decision-1",
                        "answers": {"NAS101": {"type": "noul", "noul": 0.93}},
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}/api/projects/proj-default"
            with tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                (project / "pyproject.toml").write_text(
                    "[tool.style-audit.llm.litellm]\n"
                    f'api_base = "{base}"\n'
                    'custom_llm_provider = "azure_ai"\n'
                    'decision_model = "Decision-1"\n'
                    "timeout = 5.0\n"
                    "temperature = 0.0\n",
                    encoding="utf-8",
                )
                registry = project / "models.yml"
                registry.write_text(
                    "providers:\n"
                    "  azure-maas-judge:\n"
                    "    api: openrouter-decisions\n"
                    "    baseUrl: https://registry.example/openai/v1\n"
                    "    apiKey: fixture-secret\n"
                    "    models:\n"
                    "      - id: Decision-1\n",
                    encoding="utf-8",
                )
                config = load_config(project).llm_litellm
                self.assertEqual(config.api_base, base)
                self.assertEqual(config.custom_llm_provider, "azure_ai")
                self.assertEqual(config.decision_model, "Decision-1")
                self.assertEqual(config.timeout, 5.0)
                self.assertEqual(config.temperature, 0.0)
                document = TextDocument("draft.md", "The future isn't coming. It's already here.")

                def load_registry_config(project_config, model_id):
                    return load_decision_api(project_config, model_id, registry_path=registry)

                with patch("style_audit.llm.load_decision_api", side_effect=load_registry_config):
                    with patch.dict(os.environ, {"AZURE_MAAS_JUDGE_API_KEY": ""}):
                        findings = judge_document(
                            document,
                            (RULES_BY_CODE["NAS101"],),
                            "azure-maas-judge/Decision-1",
                            threshold=0.8,
                            litellm_config=config,
                        )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(len(requests), 1)
        path, headers = requests[0]
        self.assertEqual(path, "/providers/microsoft/v1/systemone")
        self.assertEqual(headers["Authorization"], "Bearer fixture-secret")
        self.assertEqual(
            [(finding.code, finding.line, finding.column, finding.evidence) for finding in findings],
            [("NAS101", 1, 1, document.text)],
        )


    def test_openrouter_decision_model_uses_alpha_decisions_endpoint(self) -> None:
        requests: list[tuple[str, dict[str, str], dict[str, object]]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers["Content-Length"])
                body = json.loads(self.rfile.read(length))
                requests.append((self.path, dict(self.headers), body))
                response = json.dumps(
                    {
                        "id": "gen-dec-fixture",
                        "model": "microsoft/microsoft-decision-1",
                        "answers": {"NAS101": {"type": "noul", "noul": 0.93}},
                        "usage": {"input_tokens": 4, "output_tokens": 0, "total_tokens": 4},
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}/api"
            with tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                (project / "pyproject.toml").write_text(
                    "[tool.style-audit.llm.litellm]\n"
                    f'api_base = "{base}"\n'
                    "timeout = 5.0\n",
                    encoding="utf-8",
                )
                config = load_config(project).llm_litellm
                document = TextDocument("draft.md", "The future isn't coming. It's already here.")
                with patch("style_audit.llm.load_decision_api", side_effect=load_decision_api):
                    with patch.dict(
                        os.environ,
                        {"HOME": temporary, "OPENROUTER_API_KEY": "fixture-secret"},
                    ):
                        findings = judge_document(
                            document,
                            (RULES_BY_CODE["NAS101"],),
                            "openrouter/microsoft/microsoft-decision-1",
                            threshold=0.8,
                            litellm_config=config,
                        )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(len(requests), 1)
        path, headers, body = requests[0]
        self.assertEqual(path, "/api/alpha/decisions")
        self.assertEqual(headers["Authorization"], "Bearer fixture-secret")
        self.assertEqual(body["model"], "microsoft/microsoft-decision-1")
        self.assertEqual(len(findings), 1)
        self.assertEqual(
            (findings[0].code, findings[0].line, findings[0].column, findings[0].evidence),
            ("NAS101", 1, 1, document.text),
        )

if __name__ == "__main__":
    unittest.main()
