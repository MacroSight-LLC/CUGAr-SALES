import json
from pathlib import Path

import pytest

from cuga.providers.watsonx_provider import WatsonxProvider


def test_generate_missing_credentials_raises():
    provider = WatsonxProvider(api_key="", project_id="", url="", model_id="ibm/granite-3-3-8b-instruct")
    with pytest.raises(RuntimeError):
        provider.generate("hello")


def test_audit_includes_ts_actor(tmp_path: Path):
    audit_path = tmp_path / "audit.jsonl"
    provider = WatsonxProvider(
        api_key="k", project_id="p", url="u", model_id="ibm/granite-3-3-8b-instruct", audit_path=audit_path
    )
    provider.actor_id = "tester"
    res = provider._write_audit_and_return({"prompt": "hi", "seed": 1}, {"output_text": "hi", "token_usage": {}})
    record = json.loads(audit_path.read_text().splitlines()[0])
    assert record["actor"] == "tester"
    assert "ts" in res["audit"]


def test_deterministic_seed_reproducible(tmp_path: Path):
    audit = tmp_path / "audit.jsonl"
    provider = WatsonxProvider(api_key="k", project_id="p", url="u", model_id="ibm/granite-3-3-8b-instruct", audit_path=audit)
    out1 = provider.generate("deterministic", seed=42)["output_text"]
    out2 = provider.generate("deterministic", seed=42)["output_text"]
    assert out1 == out2
