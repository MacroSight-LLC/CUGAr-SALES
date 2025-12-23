from dataclasses import dataclass

from pydantic import BaseModel

from cuga.backend.altk_components import ALTKLifecycleManager, normalize_tool_calls
from cuga.backend.cuga_graph.state.agent_state import AgentState


class DummyEnhancer:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, prompt: str) -> str:
        self.calls += 1
        return f"enhanced:{prompt}"


class DummyToolCall(BaseModel):
    id: str
    function: dict
    type: str | None = None


@dataclass
class DataclassToolCall:
    id: str
    function: dict


def test_enhance_state_prompt_runs_once():
    enhancer = DummyEnhancer()
    lifecycle = ALTKLifecycleManager(prompt_enhancer=enhancer, enabled=True)
    state = AgentState(input="hello", url="http://example.com")

    lifecycle.enhance_state_prompt(state)

    assert state.input == "enhanced:hello"
    assert state._enhanced_prompt_applied is True

    lifecycle.enhance_state_prompt(state)

    assert enhancer.calls == 1
    assert state.input == "enhanced:hello"


def test_normalize_tool_calls_handles_models_and_defaults():
    tool_call = DummyToolCall(id="abc", function={"name": "do_work", "arguments": "{}"})
    dataclass_call = DataclassToolCall(id="dc", function={"name": "from_dc"})

    normalized = normalize_tool_calls([tool_call, dataclass_call])

    assert normalized[0]["id"] == "abc"
    assert normalized[0]["type"] == "function"
    assert normalized[0]["function"]["arguments"] == "{}"

    assert normalized[1]["id"] == "dc"
    assert normalized[1]["function"]["arguments"] == {}


def test_normalize_tool_calls_parses_string_and_rejects_invalid():
    from_string = normalize_tool_calls('{"function": {"name": "do_work"}}')
    assert from_string and from_string[0]["id"] == "0"
    assert from_string[0]["function"].get("arguments") == {}

    invalid = normalize_tool_calls("not json")
    assert invalid == []
