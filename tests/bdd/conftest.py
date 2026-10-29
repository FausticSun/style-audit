"""Isolated projects and controlled providers for CLI acceptance scenarios."""

from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from style_audit.cli import main
from style_audit import llm


@pytest.fixture
def project(tmp_path):
    return tmp_path


@pytest.fixture
def audit_directory(project):
    return project


@pytest.fixture
def stdin_text():
    return ""


@pytest.fixture(autouse=True)
def providers(monkeypatch):
    calls = {
        "chat": Mock(side_effect=AssertionError("Unexpected chat provider call")),
        "decision": Mock(side_effect=AssertionError("Unexpected decision provider call")),
    }
    monkeypatch.setattr(llm.litellm, "completion", calls["chat"])
    monkeypatch.setattr(llm.litellm, "systemone", calls["decision"])
    return calls


@pytest.fixture
def invoke_audit(monkeypatch, capsys, audit_directory, stdin_text):
    def invoke(arguments):
        monkeypatch.chdir(audit_directory)
        monkeypatch.setattr("sys.stdin", StringIO(stdin_text))
        capsys.readouterr()
        try:
            code = main(arguments)
        except SystemExit as exc:
            code = exc.code
        captured = capsys.readouterr()
        return SimpleNamespace(
            code=code, stdout=captured.out, stderr=captured.err, cwd=audit_directory,
        )

    return invoke
