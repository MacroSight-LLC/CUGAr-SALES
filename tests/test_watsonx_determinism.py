import pytest

from cuga.providers.watsonx_provider import WatsonxProvider


def test_deterministic_seed_reproducible(tmp_path):
    audit = tmp_path / "audit.jsonl"
    provider = WatsonxProvider(audit_path=audit)
    out1 = provider.generate("deterministic", seed=42)["output_text"]
    out2 = provider.generate("deterministic", seed=42)["output_text"]
    assert out1 == out2
