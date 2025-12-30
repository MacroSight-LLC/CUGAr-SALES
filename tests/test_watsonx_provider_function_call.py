import pytest

from cuga.providers.watsonx_provider import WatsonxProvider


@pytest.fixture()
def provider():
    return WatsonxProvider(api_key="x", project_id="y", url="http://example")


def test_function_call_happy_path(provider):
    pydantic = pytest.importorskip("pydantic")

    class EchoModel(pydantic.BaseModel):
        query: str

    result = provider.function_call([EchoModel], "hi")
    assert result["validation"] == []
    assert "response" in result


def test_function_call_fail_fast(provider):
    pydantic = pytest.importorskip("pydantic")

    class EmptyModel(pydantic.BaseModel):
        pass

    with pytest.raises(ValueError):
        provider.function_call([EmptyModel], "prompt", fail_on_validation_error=True)


def test_function_call_graceful(provider):
    pydantic = pytest.importorskip("pydantic")

    class EmptyModel(pydantic.BaseModel):
        pass

    result = provider.function_call([EmptyModel], "prompt", fail_on_validation_error=False)
    assert result["validation"], "Validation errors should be reported"
    assert "response" in result
