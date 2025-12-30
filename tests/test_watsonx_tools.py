import pytest

pytest.importorskip("pydantic")

from pydantic import BaseModel, Field

from cuga.providers.watsonx_provider import WatsonxProvider


class Args(BaseModel):
    a: int = Field(...)
    b: int = Field(...)


def test_function_call_schema_validation(monkeypatch):
    provider = WatsonxProvider(api_key="k", project_id="p", url="u", model_id="ibm/granite-3-3-8b-instruct")
    monkeypatch.setattr(provider, "generate", lambda prompt, seed=None: {"text": "ok", "token_usage": {}})
    result = provider.function_call([Args], "sum please")
    assert result["validation"] == []
