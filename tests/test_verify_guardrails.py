from pathlib import Path

import pytest

import scripts.verify_guardrails as vg


MINIMAL_ROOT_AGENTS = """# Root
## 1. Scope & Precedence
allowlist denylist escalation budget redaction
## 2. Profile Isolation
## 3. Registry Hygiene
## 4. Sandbox Expectations
## 5. Audit / Trace Semantics
## 6. Documentation Update Rules
planner worker coordinator
## 7. Verification & No Conflicting Guardrails
"""

MINIMAL_CHANGELOG = """# Log
## vNext
- guardrail automation
## v1.0.0
- baseline
"""


def configure_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vg, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(vg, "ROOT_AGENTS", tmp_path / "AGENTS.md")
    monkeypatch.setattr(vg, "CHANGELOG", tmp_path / "CHANGELOG.md")
    monkeypatch.setattr(vg, "CONFIG", vg.GuardrailConfig.from_env())


def write_allowlisted_dirs(tmp_path: Path) -> None:
    for dirname in vg.CONFIG.allowlisted_dirs:
        target = tmp_path / dirname
        target.mkdir(parents=True, exist_ok=True)
        marker = target / vg.CONFIG.inherit_filename
        marker.write_text(vg.INHERIT_MARKER, encoding="utf-8")


def write_required_docs(tmp_path: Path) -> None:
    for doc in vg.CONFIG.required_docs:
        if doc == "CHANGELOG.md":
            continue
        (tmp_path / doc).write_text(f"{doc} placeholder", encoding="utf-8")


def write_root_agents(tmp_path: Path, content: str = MINIMAL_ROOT_AGENTS) -> None:
    (tmp_path / "AGENTS.md").write_text(content, encoding="utf-8")


def write_changelog(tmp_path: Path, content: str = MINIMAL_CHANGELOG) -> None:
    (tmp_path / "CHANGELOG.md").write_text(content, encoding="utf-8")


def test_missing_root_agents_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_repo(tmp_path, monkeypatch)
    write_allowlisted_dirs(tmp_path)
    write_changelog(tmp_path)
    write_required_docs(tmp_path)

    errors = vg.run_checks(changed_files=[])

    assert any("Root AGENTS.md is missing" in err for err in errors)


def test_missing_inherit_marker_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_repo(tmp_path, monkeypatch)
    write_root_agents(tmp_path)
    write_changelog(tmp_path)
    write_required_docs(tmp_path)

    for dirname in vg.CONFIG.allowlisted_dirs:
        (tmp_path / dirname).mkdir(parents=True, exist_ok=True)

    errors = vg.run_checks(changed_files=[])

    assert any("inheritance marker" in err for err in errors)


def test_guardrail_change_requires_doc_updates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_repo(tmp_path, monkeypatch)
    write_root_agents(tmp_path)
    write_allowlisted_dirs(tmp_path)
    write_changelog(tmp_path, content="""## vNext\n- guardrail change\n## v1.0.0\n- baseline\n""")
    write_required_docs(tmp_path)

    changed_files = ["registry.yaml"]

    errors = vg.run_checks(changed_files=changed_files)

    assert any("documentation" in err.lower() for err in errors)


def test_guardrail_change_requires_vnext_guardrail_note(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_repo(tmp_path, monkeypatch)
    write_root_agents(tmp_path)
    write_allowlisted_dirs(tmp_path)
    write_changelog(tmp_path, content="""## vNext\n- misc update\n## v1.0.0\n- baseline\n""")
    write_required_docs(tmp_path)

    changed_files = ["AGENTS.md", "README.md", "PRODUCTION_READINESS.md", "CHANGELOG.md", "todo1.md"]

    errors = vg.run_checks(changed_files=changed_files)

    assert any("guardrail or registry changes" in err.lower() for err in errors)


def test_happy_path_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_repo(tmp_path, monkeypatch)
    write_root_agents(tmp_path)
    write_allowlisted_dirs(tmp_path)
    write_changelog(tmp_path)
    write_required_docs(tmp_path)

    changed_files = [
        "registry.yaml",
        "AGENTS.md",
        "README.md",
        "PRODUCTION_READINESS.md",
        "CHANGELOG.md",
        "todo1.md",
    ]

    errors = vg.run_checks(changed_files=changed_files)

    assert errors == []


def test_main_reports_failures(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(vg, "run_checks", lambda changed_files=None, base=None: ["FAIL: missing"])

    exit_code = vg.main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Guardrail verification failed" in captured.out
    assert "FAIL" in captured.out


def test_main_reports_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(vg, "run_checks", lambda changed_files=None, base=None: [])

    exit_code = vg.main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Guardrail verification passed" in captured.out
