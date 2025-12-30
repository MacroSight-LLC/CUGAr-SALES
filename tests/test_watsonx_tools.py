import pytest

from cuga.providers.watsonx_provider import WatsonxProvider


def test_watsonx_defaults_are_deterministic(tmp_path):
    audit = tmp_path / "audit.jsonl"
    provider = WatsonxProvider(audit_path=audit)
    result_one = provider.generate("ping", seed=0)
    result_two = provider.generate("ping", seed=0)
    assert result_one["output_text"] == result_two["output_text"]
    assert audit.exists()
