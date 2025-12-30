import logging
from pathlib import Path

import pytest

from cuga.tools.registry import RegistryLoader


def test_audit_logging_includes_context_and_outcome(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        '{"servers": [{"id": "valid", "url": "http://ok"}, {"id": "missing-url"}]}',
        encoding="utf-8",
    )

    audit_context = {
        "actor": "tester",
        "correlation_id": "corr-1",
        "principal": "service-account",
    }

    logger = logging.getLogger("registry_audit")
    with caplog.at_level(logging.INFO, logger=logger.name):
        servers = RegistryLoader(
            registry_path,
            logger=logger,
            audit_context=audit_context,
        )._load()

    assert len(servers) == 1

    violations = [record for record in caplog.records if getattr(record, "event", "") == "registry_schema_violation"]
    assert violations
    for record in violations:
        assert record.outcome == "failure"
        assert record.actor == audit_context["actor"]
        assert record.operation == "registry_schema_validation"
        assert record.correlation_id == audit_context["correlation_id"]
        assert isinstance(record.path, list)
        assert isinstance(record.schema_path, list)
        assert hasattr(record, "index")
        if hasattr(record, "missing"):
            assert record.missing == ["id", "url"]
        if hasattr(record, "expected_type"):
            assert record.expected_type == "object"

    summary = next(record for record in caplog.records if getattr(record, "event", "") == "registry_schema_validation")
    assert summary.outcome == "partial"
    assert summary.accepted == 1
    assert summary.rejected == 1
    assert summary.total == 2
    assert summary.actor == audit_context["actor"]
    assert summary.correlation_id == audit_context["correlation_id"]
    assert summary.operation == "registry_schema_validation"


def test_fail_on_validation_error_raises_sanitized(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text('{"servers": {"id": "not-a-list", "url": "http://secret"}}', encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        with pytest.raises(ValueError) as excinfo:
            RegistryLoader(registry_path, fail_on_validation_error=True)._load()

    assert str(excinfo.value) == "Invalid registry schema"
    assert all("http://secret" not in record.getMessage() for record in caplog.records)
    assert all("http://secret" not in str(getattr(record, "constraint", "")) for record in caplog.records)


def test_custom_logger_injection(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text('{"servers": [{"id": "a", "url": "https://example"}]}', encoding="utf-8")

    custom_logger = logging.getLogger("custom.registry")
    with caplog.at_level(logging.INFO, logger=custom_logger.name):
        RegistryLoader(registry_path, logger=custom_logger)._load()

    assert any(record.name == custom_logger.name for record in caplog.records)

    audit_records = [
        record
        for record in caplog.records
        if record.name == custom_logger.name and getattr(record, "event", None) == "registry_schema_validation"
    ]
    assert audit_records, "Expected registry_schema_validation events from custom logger"

    for record in audit_records:
        assert getattr(record, "operation", None) == "registry_schema_validation"
        assert getattr(record, "outcome", None) is not None
        assert hasattr(record, "accepted") or hasattr(record, "rejected")


def test_entries_without_required_fields_are_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        '{"servers": [{"id": "ok", "url": "http://ok"}, {}]}',
        encoding="utf-8",
    )

    with caplog.at_level(logging.INFO):
        servers = RegistryLoader(registry_path)._load()

    assert len(servers) == 1
    summary = next(record for record in caplog.records if getattr(record, "event", "") == "registry_schema_validation")
    assert summary.outcome == "partial"
    assert summary.accepted == 1
    assert summary.rejected == 1
